import telebot
import time
import urllib.request
from ml_backend.controller import Controller, Artifact
from forest_bot_front.utils import get_radius_from_msg, get_cords_from_msg, is_float
from satelline.satellite_data import download_rect
from threading import Thread
from pathlib import Path


class ForestBot:
    """
    Entity for interaction with Telegram users and their messages.
    """
    max_attempts = 10  # Max number of attempts to send the result
    model_input_size = 224
    use_crop = True
    crop_size = 224
    default_radius = 0.02
    max_radius = 0.05
    min_radius = 0.01
    default_threshold = 0.2

    def __init__(self):
        # TODO: hide token to env
        with open(Path("forest_bot_front/token.txt"), 'r') as token_file:
            token = token_file.readline()

        # TODO: save + load from save. make static?
        self.user_radiuses = dict()
        self.user_thresholds = dict()
        self.bot = telebot.TeleBot(token)
        self.__init_messages()
        self.__add_handlers()
        self.controller = Controller(
            callback=self.__send_prediction_callback,
            model_input_size=ForestBot.model_input_size,
            use_crop=ForestBot.use_crop,
            crop_size=ForestBot.crop_size if ForestBot.use_crop else None
        )

        Thread(target=self.controller.observe_updates).start()

    def start(self) -> None:
        """Start the bot. Thread will be captured"""
        self.bot.polling(none_stop=True)

    def __add_handlers(self) -> None:
        """Method for initialize message handlers from Telegram bot"""

        @self.bot.message_handler(commands=['set_threshold'])
        @self.bot.message_handler(commands=['set_sensitivity'])
        def handle_threshold(message) -> None:
            msg_wrong = "Для установки чувствительности введите число" \
                        " в диапазоне от 0 до 1. Чем больше чувствительность, тем больше потенциальных дорог будет" \
                        "обнаружено \n\nПример:\n/set_sensitivity 0.2"
            words = message.text.split(' ')
            if len(words) != 2 or not is_float(words[1]) or not 0 < float(words[1]) < 1:
                self.bot.send_message(message.chat.id, msg_wrong)
            else:
                # higher sensitivity => lower trashhold
                new_threshold = 1 - float(words[1])
                self.user_thresholds[message.chat.id] = new_threshold
                self.bot.send_message(message.chat.id, f"Установлена новая чувствительность: {new_threshold}")

        @self.bot.message_handler(commands=['start'])
        def handle_start_message(message) -> None:
            self.bot.send_message(message.chat.id, self.start_message)

        @self.bot.message_handler(commands=['help'])
        def handle_start_message(message) -> None:
            # TODO: Написать /help
            self.bot.send_message(message.chat.id, "Нормально делай - нормально будет")

        @self.bot.message_handler(commands=['set_radius'])
        def handle_change_radius_message(message) -> None:
            # TODO: degree -> km. Text?
            wrong_command_message = "Для изменения радиуса снимка используйте команду таким образом:\n/set_radius " \
                                    f"{{число в пределах [{ForestBot.min_radius}, {ForestBot.max_radius}]}}\n\n" \
                                    "Пример:\n/set_radius 0.5"
            success, custom_radius = get_radius_from_msg(
                message=message, min_value=ForestBot.min_radius, max_value=ForestBot.max_radius)

            if not success:
                self.bot.send_message(message.chat.id, wrong_command_message)
            else:
                self.user_radiuses[message.chat.id] = custom_radius
                self.bot.send_message(message.chat.id,
                                      f"Радиус снимка успешно установлен: {round(custom_radius, 5)}°")

        @self.bot.message_handler(func=ForestBot.__test_document_message_is_image, content_types=['document'])
        @self.bot.message_handler(content_types=['photo'])
        def handle_photo_message(message) -> None:
            self.bot.send_message(message.chat.id, self.accept_photo_message)

            # Here we take only last image from the assumption that the user has sent only one picture
            # TODO: add processing of several photos in one message
            if message.content_type == 'photo':
                file_id = message.photo[-1].file_id
                file_format = "jpg"
            else:  # document
                file_id = message.document.file_id
                file_format = message.document.mime_type.split('/')[1]

            # Generate unique name for image
            image_name = f"input_image&id={message.chat.id}&time={round(time.time() * 1000)}.{file_format}"

            file_info = self.bot.get_file(file_id)
            file_url = f'https://api.telegram.org/file/bot{self.bot.token}/{file_info.file_path}'
            urllib.request.urlretrieve(file_url, f"input_photos/{image_name}")
            chat_id = message.chat.id
            # A pair of image and id is added to the processing queue
            self.controller.request_queue.put(Artifact(chat_id, image_name, self.__get_threshold(chat_id)))

        @self.bot.message_handler(content_types=['text'])
        def handle_text_cords_message(message) -> None:
            # TODO: make queue for anti-DDOS
            success, cords = get_cords_from_msg(message.text)
            if not success:
                self.bot.send_message(message.chat.id, self.wrong_cords_message)
            else:
                self.__handle_cords_input(chat_id=message.chat.id, cords=cords)

        @self.bot.message_handler(content_types=['location'])
        def handle_location_message(message) -> None:
            self.__handle_cords_input(chat_id=message.chat.id,
                                      cords=(message.location.latitude, message.location.longitude))

    def __handle_cords_input(self, chat_id, cords):
        self.bot.send_message(chat_id, "Ваши координаты приняты. Начинаем обработку...")
        image_name = f"input_image&id={chat_id}&time={round(time.time() * 1000)}.png"
        radius = ForestBot.default_radius if chat_id not in self.user_radiuses else \
            self.user_radiuses[chat_id]

        Thread(
            target=self.__parallel_load_satellite_image,
            kwargs={
                'image_name': image_name,
                'cords': cords,
                'radius': radius,
                'download_dir': Path("../input_photos"),
                'chat_id': chat_id
            }
        ).start()

    @staticmethod
    def __test_document_message_is_image(message) -> bool:
        return message.document.mime_type.split('/')[0] == 'image'

    def __parallel_load_satellite_image(self, image_name, cords, radius, download_dir, chat_id):
        try:
            transform_func = download_rect(image_name=image_name, center=cords, radius=radius,
                                           download_dir=download_dir)
            self.controller.request_queue.put(Artifact(chat_id, image_name, self.__get_threshold(chat_id)))
        except Exception as ex:
            print(f"Failed to load satellite images:\n{ex}")
            self.bot.send_message(chat_id, "Не удалось обнаружить спутниковые снимки в данном районе. Похоже, "
                                           "Вы - отважный путешественник, раз решили отправиться туда!")

    def __init_messages(self) -> None:
        """Loads basic messages from files."""
        # TODO: do DRY. JSON?
        with open("forest_bot_front/messages/start_message.txt", encoding="UTF-8") as f:
            self.start_message = f.read()

        with open("forest_bot_front/messages/accept_photo_message.txt", encoding="UTF-8") as f:
            self.accept_photo_message = f.read()

        with open("forest_bot_front/messages/accept_cords_message.txt", encoding="UTF-8") as f:
            self.accept_cords_message = f.read()

        with open("forest_bot_front/messages/ready_img_message.txt", encoding="UTF-8") as f:
            self.ready_img_message = f.read()

        with open("forest_bot_front/messages/failed_to_send_img_message.txt", encoding="UTF-8") as f:
            self.failed_to_send_message = f.read()

        with open("forest_bot_front/messages/wrong_cords_message.txt", encoding="UTF-8") as f:
            self.wrong_cords_message = f.read()

    def __get_threshold(self, chat_id: int) -> float:
        if chat_id in self.user_thresholds:
            return self.user_thresholds[chat_id]
        else:
            return self.default_threshold

    def __send_prediction_callback(self, result_path: Path, chat_id: int) -> None:
        """
        Callback for completed prediction.
        :param Path result_path: path to the result image
        :param int chat_id: chat id
        """
        Thread(target=self.__send_result_with_retry, args=[result_path, chat_id]).start()

    def __send_result_with_retry(self, result_path: Path, chat_id: int, attempt: int = 0) -> None:
        """
        Method for sending the processed image. Applies multiple retries on failed submission.
        :param Path result_path: path to the result image
        :param int chat_id: chat id
        :param int attempt: attempt number (starts from 0)
        """
        try:
            # Try to read and send result
            result = open(result_path, 'rb')
            self.bot.send_photo(chat_id=chat_id, photo=result)
        except Exception as exception:
            print(
                f"Attempt {attempt}/{ForestBot.max_attempts} failed. Trying again...\n"
                f"Chat id = {chat_id},\npath={result_path}\n{exception}\n\n"
            )

            if attempt < ForestBot.max_attempts:
                # Do another attempt with delay
                time.sleep(1)
                self.__send_result_with_retry(result_path, chat_id, attempt + 1)
            else:
                # Maximum number of attempts made. Ask user to retry
                print('=' * 10, f"\nFailed to send\nchat_id = {chat_id}\nimg = {result_path}\n", '=' * 10, sep='')

                try:
                    # Try to ask user for retry if it is possible
                    self.bot.send_message(chat_id, self.failed_to_send_message)
                except Exception as exception:
                    print('=' * 10, f"\nLost connection with chat id = {chat_id}\n{exception}\n", '=' * 10, sep='')
        else:
            if attempt:
                print(
                    f"!!!\nSuccessfully send by {attempt}th attempt.\nChat id = {chat_id}, img = {result_path}\n!!!\n")
