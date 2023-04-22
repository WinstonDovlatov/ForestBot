import pytest
from unittest.mock import Mock
from forestbot.front.utils import *


class MockBot:
    def __init__(self, n_exceptions):
        self.send_message = Mock()
        self.send_message.side_effect = [Exception()] * n_exceptions + [None]


@pytest.mark.parametrize(
    ("input_string", "excepted_answer"),
    (
            ('1', True),
            ('1.0', True),
            ('1.012300123', True),
            ('-123.0123', True),
            ("one", False),
            ("", False)
    )
)
def test_is_float(input_string, excepted_answer):
    assert is_float(input_string) == excepted_answer


@pytest.mark.parametrize(
    ("input_string", "min_value", "max_value", "excepted_answer"),
    (
            ("/set_radius @bc", 1, 2, (False, None)),
            ("/set_radius", 1, 2, (False, None)),
            ("/set_radius 3", 1, 2, (False, None)),
            ("/set_radius 1", 2, 3, (False, None)),
            ("/set_radius 0.5", 0.5, 2, (True, 0.5)),
            ("/set_radius 2.5", 0, 2.5, (True, 2.5)),
            ("/set_radius 0.33", 0.33, 0.33, (True, 0.33))
    )
)
def test_get_radius(input_string, min_value, max_value, excepted_answer):
    assert excepted_answer == get_radius_from_msg(input_string, min_value, max_value)


@pytest.mark.parametrize(
    ("input_string", "excepted_answer"),
    (
            ("1,2,3", (False, None)),
            ("1", (False, None)),
            ("hehe, 23", (False, None)),
            ("100, hoho", (False, None)),
            ("aa bb", (False, None)),
            ("50, 50", (True, (50, 50))),
            ("50.25, -50.35", (True, (50.25, -50.35))),
            ("-100, 10", (False, None)),
            ("100, 10", (False, None)),
            ("10, 190", (False, None)),
            ("10, -190", (False, None)),
            ("-100, 190", (False, None)),

    )
)
def test_get_cords(input_string, excepted_answer):
    assert excepted_answer == get_cords_from_msg(input_string)


@pytest.mark.parametrize(
    "n_exceptions", (1, 3, 5)
)
def test_correct_send_text_message_with_retry(n_exceptions):
    mock_bot = MockBot(n_exceptions)
    send_text_message_with_retry(bot=mock_bot, chat_id=0, text="text", delay=0.001)
    assert mock_bot.send_message.call_count == n_exceptions + 1


@pytest.mark.parametrize(
    "max_attempts", (1, 3, 5)
)
def test_failed_send_text_message_with_retry(max_attempts):
    mock_bot = MockBot(n_exceptions=max_attempts + 5)
    send_text_message_with_retry(bot=mock_bot, chat_id=0, text="text", max_attempts=max_attempts, delay=0.001)
    assert mock_bot.send_message.call_count == max_attempts
