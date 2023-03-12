from typing import Union, Tuple

wrong_msg = (False, None)


def is_float(inp: str) -> bool:
    if inp is None:
        return False
    try:
        float(inp)
        return True
    except ValueError:
        return False


def get_radius_from_msg(message, min_value, max_value) -> Tuple[bool, Union[float, None]]:
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
    words = message.split(', ')
    if len(words) != 2:
        return wrong_msg
    if not is_float(words[0]) or not is_float(words[1]):
        return wrong_msg

    return True, (float(words[0]), float(words[1]))
