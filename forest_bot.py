import telebot
from telebot.async_telebot import AsyncTeleBot
import asyncio
import time
import urllib.request
from dummy.controller import Controller, Artifact
from threading import Thread
from pathlib import Path


class ForestBot:
    """
    Entity for interaction with Telegram users and their messages.
    """
    max_attempts = 3  # Max number of attempts to send the result

    def __init__(self):
        # TODO: hide token to env
        with open("token.txt", 'r') as token_file:
            token = token_file.readline()

        self.bot = telebot.TeleBot(token)
        # self.bot = telebot.async_telebot.AsyncTeleBot(token)
        self.__init_messages()
        self.__add_handlers()
        self.controller = Controller(self.__send_prediction_callback)
        Thread(target=self.controller.observe_updates).start()
        #Thread(target=asyncio.run, args=(self.controller.observe_updates(),)).start()

    def start(self) -> None:

        # asyncio.run(self.bot.polling(none_stop=True))
        self.bot.polling(none_stop=True)

    def __add_handlers(self) -> None:
        """Method for initialize message handlers from Telegram."""

        @self.bot.message_handler(commands=['start'])
        def handle_start_message(message) -> None:
            self.bot.send_message(message.chat.id, self.start_message)

        def test_document_message_is_image(message):
            return message.document.mime_type.split('/')[0] == 'image'

        @self.bot.message_handler(func=test_document_message_is_image, content_types=['document'])
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

            # A pair of image and id is added to the processing queue
            self.controller.request_queue.put(Artifact(message.chat.id, image_name))

    def __init_messages(self) -> None:
        """Loads basic messages from files."""
        # TODO: do DRY. JSON?
        with open("messages/start_message.txt", encoding="UTF-8") as f:
            self.start_message = f.read()

        with open("messages/accept_photo_message.txt", encoding="UTF-8") as f:
            self.accept_photo_message = f.read()

        with open("messages/accept_cords_message.txt", encoding="UTF-8") as f:
            self.accept_cords_message = f.read()

        with open("messages/ready_img_message.txt", encoding="UTF-8") as f:
            self.ready_img_message = f.read()

        with open("messages/failed_to_send_img_message.txt", encoding="UTF-8") as f:
            self.failed_to_send_message = f.read()

    def __send_prediction_callback(self, result_path: Path, chat_id: int) -> None:
        """
        Callback for completed prediction.
        :param Path result_path: path to the result image
        :param int chat_id: chat id
        """
        # Thread(target=self.__send_result_with_retry, args=[result_path, chat_id]).start()
        # TODO: 2 methods -> 1 method if use async instead of threading
        self.__send_result_with_retry(result_path, chat_id)

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
