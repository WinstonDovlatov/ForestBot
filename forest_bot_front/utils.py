from typing import Union, Tuple
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time

wrong_msg = (False, None)


def is_float(inp: str) -> bool:
    """
    Test is input string could be converted to float
    :param str inp: testing string
    :return bool: true if given string could be float, false otherwise
    """
    if inp is None:
        return False
    try:
        float(inp)
        return True
    except ValueError:
        return False


def get_radius_from_msg(message, min_value: float, max_value: float) -> Tuple[bool, Union[float, None]]:
    """
    Extract radius value from /set_radius message if it is possible
    :param message: input message from telebot
    :param min_value: minimum allowable value
    :param max_value: maximum allowable value
    :return: (True, radius) if radius could be extracted and allowable. (False, None) otherwise
    """
    words = message.text.split()

    if len(words) != 2:
        return wrong_msg
    if not is_float(words[1]):
        return wrong_msg

    value = float(words[1])
    if min_value <= value <= max_value:
        return True, value
    else:
        return wrong_msg


def get_cords_from_msg(message) -> Tuple[bool, Union[None, Tuple[float, float]]]:
    """
    Extract coordinates values from corresponding message if it is possible
    :param message: input message from bot
    :return: (True, (latitude_value, longitute_value)) in case of success. (False, None) otherwise
    """
    words = message.split(', ')
    if len(words) != 2:
        return wrong_msg
    if not is_float(words[0]) or not is_float(words[1]):
        return wrong_msg

    latitude_value = float(words[0])
    longitute_value = float(words[1])

    if not -90 < latitude_value < 90 or not -180 < longitute_value < 180:
        return wrong_msg

    return True, (float(words[0]), float(words[1]))


def convert_deg_to_km(deg: float) -> float:
    return 111.1348 * deg


def convert_km_to_deg(km: float) -> float:
    return km / 111.1348


def generate_buttons_continue(image_name) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("🧭 Найти лесные дороги 🧭", callback_data=f"y {image_name}"),
               InlineKeyboardButton("Отмена 🚫", callback_data=f"n {image_name}"))
    return markup


def generate_buttons_osm(image_name) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🌎 Экспортировать в OSM 🌎", callback_data=f"osm {image_name}"))
    return markup

def test_document_message_is_image(message) -> bool:
    return message.document.mime_type.split('/')[0] == 'image'


def test_document_message_not_image(message) -> bool:
    return not test_document_message_is_image(message)


def generate_image_name(chat_id: int, file_format: str = 'png') -> str:
    return f"input_image&id={chat_id}&time={round(time.time() * 100000)}.{file_format}"


def is_image_size_correct(photo, min_size, max_size) -> bool:
    return (min_size <= photo[-1].width <= max_size) and (min_size <= photo[-1].height <= max_size)


def is_processing_call(call) -> bool:
    # TODO: оч плохо, надо переписать
    return (call.data[0] == 'y') or (call.data[0] == 'n')


def is_osm_call(call) -> bool:
    # TODO: оч плохо, надо переписать
    return call.data.split()[0] == 'osm'
