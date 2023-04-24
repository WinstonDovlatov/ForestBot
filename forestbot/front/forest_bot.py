import urllib.request
from forestbot.ml_backend.controller import Controller, Artifact
from forestbot.front.image_analyzer.size_analyzer import is_correct_size
from forestbot.satellite.satellite_data import download_rect
from forestbot.satellite.osm_convert import generate_osm
from forestbot.front.utils import *
from threading import Thread, Lock
from pathlib import Path
import telebot
import numpy as np
import configparser
import xml.etree.ElementTree as ET
import os


class ForestBot:
    """
    Entity for interaction with Telegram users and their messages.
    """
    max_attempts = 10  # Max number of attempts to send the result
    model_input_size = 224
    use_crop = True
    crop_size = 224
    default_radius_deg = convert_km_to_deg(2.0)
    max_radius_km = 7.0
    min_radius_km = 1.0
    default_threshold = 0.2
    out_date_time = 60 * 10  # in seconds
    min_photo_size = 200
    max_photo_size = 2000
    valid_formats = ['png', 'jpeg', 'jpg', 'bmp']
    min_download_size_to_notify = 5

    def __init__(self):
        config = configparser.ConfigParser()
        config.read(Path("credentials.ini"))

        token = config['BOT']['bot_token']

        # TODO: save + load from save. make static?
        self.user_radiuses_deg = dict()
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
        self.download_satellite_lock = Lock()
        self.download_satellite_queue_size = 0

        self.img_to_mask = dict()
        self.img_to_func = dict()

        Thread(target=self.controller.observe_updates).start()
        print("Bot is running")

    def start(self) -> None:
        """Start the bot. Thread will be captured"""
        self.bot.polling(none_stop=True)

    def __add_handlers(self) -> None:
        """Method for initialize message handlers from Telegram bot"""

        @self.bot.message_handler(commands=['set_sensitivity'])
        def handle_threshold(message) -> None:
            words = message.text.split(' ')
            if len(words) != 2 or not is_float(words[1]) or not 0 < float(words[1]) < 1:
                self.send_text_message(chat_id=message.chat.id, text=self.wrong_threshold)
            else:
                # higher sensitivity => lower threshold
                new_threshold = 1 - float(words[1])
                self.user_thresholds[message.chat.id] = new_threshold
                self.send_text_message(message.chat.id, f"Установлена новая чувствительность: {1 - new_threshold:.2f}")

        @self.bot.message_handler(commands=['start'])
        def handle_start_message(message) -> None:
            self.send_text_message(message.chat.id, self.start_message)

        @self.bot.message_handler(commands=['help'])
        def handle_help_message(message) -> None:
            self.send_text_message(message.chat.id, self.help_message)

        @self.bot.message_handler(commands=['set_radius'])
        def handle_change_radius_message(message) -> None:

            success, custom_radius = get_radius_from_msg(
                message=message.text, min_value=ForestBot.min_radius_km, max_value=ForestBot.max_radius_km)

            if not success:
                self.send_text_message(message.chat.id, self.wrong_change_radius_message)
            else:
                self.user_radiuses_deg[message.chat.id] = convert_km_to_deg(custom_radius)
                self.send_text_message(message.chat.id,
                                       f"Радиус снимка успешно установлен: {round(custom_radius, 2)} км")

        @self.bot.message_handler(
            content_types=['audio', 'sticker', 'video', 'video_note', 'voice', 'contact', 'web_app_data'])
        def handle_other_types(message) -> None:
            self.send_text_message(message.chat.id, self.wrong_file_format_message)

        @self.bot.message_handler(content_types=['document'])
        @self.bot.message_handler(content_types=['photo'])
        def handle_photo_message(message) -> None:
            # Here we take only last image from the assumption that the user has sent only one picture
            # TODO: add processing of several photos in one message
            # TODO: move validation to another method
            if message.content_type == 'photo':
                file_id = message.photo[-1].file_id
                file_format = "png"

            else:  # document
                file_id = message.document.file_id
                file_format = message.document.mime_type.split('/')[1]
                if not ForestBot.__is_correct_format(file_format):
                    self.send_text_message(message.chat.id, self.wrong_file_format_message)
                    return

            file_info = self.bot.get_file(file_id)
            file_url = f'https://api.telegram.org/file/bot{self.bot.token}/{file_info.file_path}'

            if not is_correct_size(url=file_url, max_size=ForestBot.max_photo_size, min_size=ForestBot.min_photo_size):
                self.send_text_message(message.chat.id, self.wrong_size_message)
                return

            self.send_text_message(message.chat.id, self.accept_photo_message)
            image_name = generate_image_name(chat_id=message.chat.id, file_format=file_format)
            urllib.request.urlretrieve(file_url, f"input_photos/{image_name}")
            chat_id = message.chat.id

            # A pair of image and id is added to the processing queue
            self.controller.request_queue.put(
                Artifact(chat_id, image_name, self.user_thresholds.get(chat_id, self.default_threshold)))

        @self.bot.message_handler(content_types=['text'])
        def handle_text_cords_message(message) -> None:
            success, cords = get_cords_from_msg(message.text)
            if not success:
                self.send_text_message(message.chat.id, self.wrong_cords_message)
            else:
                self.__handle_cords_input(chat_id=message.chat.id, cords=cords)

        @self.bot.message_handler(content_types=['location'])
        def handle_location_message(message) -> None:
            self.__handle_cords_input(chat_id=message.chat.id,
                                      cords=(message.location.latitude, message.location.longitude))

        @self.bot.callback_query_handler(func=is_osm_call)
        def callback_for_osm(call):
            chat_id = call.from_user.id
            msg_id = call.message.message_id
            date = call.message.date

            if time.time() - date > ForestBot.out_date_time:
                self.bot.answer_callback_query(call.id, 'Сообщение устарело ⌛')
                self.send_text_message(chat_id, 'Похоже, прошло слишком много времени 😱\n'
                                                'Отправьте ваши координаты снова, а мы их обработаем 🚀')

            img_name = call.data.split()[1]
            mask = self.img_to_mask[img_name]
            func = self.img_to_func[img_name]

            self.bot.answer_callback_query(call.id, 'Принято 👍')
            self.bot.edit_message_reply_markup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
            self.send_text_message(chat_id, "Экспортируем результат в формат OSM...")

            Thread(target=__send_osm, args=[chat_id, mask, func]).start()

        def __send_osm(chat_id, mask, func) -> None:
            """
            Method to generate and send .osm file to user.
            :param chat_id: user id
            :param mask: predicted mask
            :param func: function for converting coordinates
            """

            def send_document(chat_id, document):
                Thread(target=send_document_with_retry, kwargs={
                    'bot': self.bot,
                    'chat_id': chat_id,
                    'document': document,
                    'max_attempts': ForestBot.max_attempts
                }).start()

            file_name = f"{round(time.time() * 100000)}.osm"
            file_path = Path(f'osm/{file_name}')
            result = generate_osm(mask, func)

            with open(file_path, 'w') as f:
                ET.ElementTree(result).write(f, encoding='unicode', xml_declaration=True)

            f = open(file_path, 'rb')
            send_document(chat_id=chat_id, document=f)

        @self.bot.callback_query_handler(func=is_processing_call)
        def callback_for_processing_choice(call):
            msg_id = call.message.message_id
            chat_id = call.from_user.id
            answer, image_name = call.data.split()
            date = call.message.date

            self.bot.edit_message_reply_markup(chat_id=chat_id, message_id=msg_id, reply_markup=None)

            if answer == 'y':
                if time.time() - date > ForestBot.out_date_time:
                    self.bot.answer_callback_query(call.id, 'Сообщение устарело ⌛')
                    self.send_text_message(chat_id, 'Похоже, прошло слишком много времени 😱\n'
                                                    'Отправьте ваши координаты снова, а мы их обработаем 🚀')
                else:
                    self.bot.answer_callback_query(call.id, 'Принято 👍')
                    self.send_text_message(chat_id, 'Начинаем поиск 🔍')
                    self.controller.request_queue.put(
                        Artifact(chat_id, image_name, self.user_thresholds.get(chat_id, self.default_threshold)))
            else:
                self.bot.answer_callback_query(call.id, 'Отмена 🚫')
                self.send_text_message(chat_id, 'Поиск отменен. Хотите изучить другую местность ?🤗'
                                                '\nПросто отправьте координаты или снимок!')

    def __handle_cords_input(self, chat_id, cords) -> None:
        """
        Method to process coordinates
        :param chat_id: user id
        :param cords: extracted coordinates from geoteg or text message
        """
        Thread(target=self.__send_loading_animation_message, kwargs={'chat_id': chat_id}).start()
        image_name = generate_image_name(chat_id)
        radius = self.user_radiuses_deg.get(chat_id, ForestBot.default_radius_deg)
        self.download_satellite_queue_size += 1
        Thread(
            target=self.__download_satellite,
            kwargs={
                'image_name': image_name,
                'cords': cords,
                'radius': radius,
                'download_dir': Path("input_photos"),
                'chat_id': chat_id
            }
        ).start()

    def __send_loading_animation_message(self, chat_id: int) -> None:
        """
        Method to show cool rotating globe in message
        :param chat_id: user id
        """
        states = ['🌍', '🌎', '🌏']
        message_text = "Ваши координаты приняты. Загружаем снимок "
        msg = self.bot.send_message(chat_id, message_text + states[0])
        if self.download_satellite_queue_size > ForestBot.min_download_size_to_notify:
            self.send_text_message(chat_id,
                                   f"В данный момент нам поступило достаточно много запросов на загрузку снимков.\n"
                                   f"Номер вашего запроса в очереди: {self.download_satellite_queue_size}")
        for i in range(1, 124):
            try:
                self.bot.edit_message_text(message_text + states[i % 3], chat_id, msg.id)
            except Exception as e:
                time.sleep(3)
            time.sleep(0.5)

    def __download_satellite(self, image_name, cords, radius, download_dir, chat_id) -> None:
        """
        Method to download satellite image on disk.
        """
        with self.download_satellite_lock:
            try:
                transform_func = download_rect(image_name=image_name, center=cords, radius=radius,
                                               download_dir=download_dir)
                self.img_to_func[image_name] = transform_func
                self.__send_image_with_retry(
                    result_path=download_dir / image_name,
                    chat_id=chat_id,
                    delete_result=False,
                    caption=f'Снимок местности по вашим координатам:\n{cords[0]}, {cords[1]}\n',
                    reply_markup=generate_buttons_continue(image_name)
                )
            except Exception as ex:
                print(f"Failed to load satellite images:\n{ex}")
                self.send_text_message(chat_id, "Не удалось обнаружить спутниковые снимки в данном районе. Похоже, "
                                                "Вы - отважный путешественник, раз решили отправиться туда!")
            finally:
                self.download_satellite_queue_size -= 1

    def __init_messages(self) -> None:
        """Loads basic messages from files."""
        msg_path = Path("forestbot/front/messages")

        with open(msg_path / "start_message.txt", encoding="UTF-8") as f:
            self.start_message = f.read()

        with open(msg_path / "accept_photo_message.txt", encoding="UTF-8") as f:
            self.accept_photo_message = f.read()

        with open(msg_path / "ready_img_message.txt", encoding="UTF-8") as f:
            self.ready_img_message = f.read()

        with open(msg_path / "failed_to_send_img_message.txt", encoding="UTF-8") as f:
            self.failed_to_send_message = f.read()

        with open(msg_path / "wrong_cords_message.txt", encoding="UTF-8") as f:
            self.wrong_cords_message = f.read()

        with open(msg_path / "wrong_file_format_message.txt", encoding="UTF-8") as f:
            self.wrong_file_format_message = f.read()

        with open(msg_path / "wrong_size_message.txt", encoding="UTF-8") as f:
            self.wrong_size_message = f.read()

        with open(msg_path / "help_message.txt", encoding="UTF-8") as f:
            self.help_message = f.read()

        with open(msg_path / "wrong_threshold.txt", encoding="UTF-8") as f:
            self.wrong_threshold = f.read()

        self.wrong_change_radius_message = "Для изменения радиуса снимка используйте команду таким образом:\n" \
                                           "/set_radius " \
                                           f"{{число в пределах " \
                                           f"[{ForestBot.min_radius_km}, {ForestBot.max_radius_km}]}}\n\n" \
                                           "Пример:\n/set_radius 2.5"

    def __send_prediction_callback(self, result_path: Path, chat_id: int, mask: np.ndarray, image_name=None) -> None:
        """
        Callback for completed prediction.
        :param Path result_path: path to the result image
        :param int chat_id: chat id
        """
        self.img_to_mask[image_name] = mask
        Thread(
            target=self.__send_image_with_retry,
            kwargs={
                'result_path': result_path,
                'chat_id': chat_id,
                'delete_result': True,
                'reply_markup': generate_buttons_osm(image_name) if image_name in self.img_to_func else None
            }
        ).start()

    def __send_image_with_retry(self, result_path: Path, chat_id: int, attempt: int = 0, caption: str = "Готово!🥳",
                                delete_result: bool = False, **kwargs) -> None:
        """
        Method for sending the processed image. Applies multiple retries on failed submission.
        :param Path result_path: path to the image
        :param int chat_id: chat id
        :param int attempt: attempt number (starts from 0)
        :param str caption: (optional) text message
        """
        try:
            # Try to read and send result
            with open(result_path, 'rb') as result:
                self.bot.send_photo(chat_id=chat_id, photo=result, caption=caption, **kwargs)
            if delete_result:
                try:
                    os.remove(result_path)
                    os.remove(Path('input_photos') / result_path.name)
                except Exception as e:
                    print(e)
        except Exception as exception:
            print(
                f"Attempt {attempt}/{ForestBot.max_attempts} failed. Trying again...\n"
                f"Chat id = {chat_id},\npath={result_path}\n{exception}\n\n"
            )

            if attempt < ForestBot.max_attempts:
                # Do another attempt with delay
                time.sleep(1)
                self.__send_image_with_retry(result_path=result_path, chat_id=chat_id, attempt=attempt + 1,
                                             caption=caption, **kwargs)
            else:
                # Maximum number of attempts made. Ask user to retry
                print('=' * 10, f"\nFailed to send\nchat_id = {chat_id}\nimg = {result_path}\n", '=' * 10, sep='')
                try:
                    os.remove(result_path)
                except Exception as e:
                    print(e)
                try:
                    # Try to ask user for retry if it is possible
                    self.send_text_message(chat_id, self.failed_to_send_message)
                except Exception as exception:
                    print('=' * 10, f"\nLost connection with chat id = {chat_id}\n{exception}\n", '=' * 10, sep='')
        else:
            if attempt:
                print(
                    f"!!!\nSuccessfully send by {attempt}th attempt.\nChat id = {chat_id}, img = {result_path}\n!!!\n")

    def send_text_message(self, chat_id: int, text: str) -> None:
        Thread(target=send_text_message_with_retry, kwargs={
            'bot': self.bot, 'chat_id': chat_id, 'text': text, 'max_attempts': ForestBot.max_attempts
        }).start()

    @classmethod
    def __is_image_size_correct(cls, photo) -> bool:
        return (cls.min_photo_size <= photo[-1].width <= cls.max_photo_size) and (
                cls.min_photo_size <= photo[-1].height <= cls.max_photo_size)

    @classmethod
    def __is_correct_format(cls, file_format: str) -> bool:
        return file_format in cls.valid_formats
