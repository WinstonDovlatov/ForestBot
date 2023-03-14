import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def generate_buttons(image_name) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("🧭 Найти лесные дороги 🧭", callback_data=f"y {image_name}"),
               InlineKeyboardButton("Отмена 🚫", callback_data=f"n {image_name}"))
    return markup


def test_document_message_is_image(message) -> bool:
    return message.document.mime_type.split('/')[0] == 'image'

def test_document_message_not_image(message) -> bool:
    return not test_document_message_is_image(message)