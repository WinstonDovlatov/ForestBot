from typing import Union, Tuple

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


def get_number_from_msg(message, min_value: float, max_value: float) -> Tuple[bool, Union[float, None]]:
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
