import pytest
from pathlib import Path
from tests.test_front.common import MockBot
from forestbot.front.utils import *


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
    mock_bot = MockBot()
    mock_bot.init_send_message(n_exceptions)
    send_text_message_with_retry(bot=mock_bot, chat_id=MockBot.chat_id, text=MockBot.sample_text, delay=0.001)
    assert mock_bot.send_message.call_count == n_exceptions + 1
    calls = mock_bot.send_message.call_args_list
    for call in calls:
        _, kwargs = call
        assert kwargs['chat_id'] == MockBot.chat_id
        assert kwargs['text'] == MockBot.sample_text


@pytest.mark.parametrize(
    "max_attempts", (1, 3, 5)
)
def test_failed_send_text_message_with_retry(max_attempts):
    mock_bot = MockBot()
    mock_bot.init_send_message(n_exceptions=max_attempts + 5)
    send_text_message_with_retry(bot=mock_bot, chat_id=MockBot.chat_id, text="text", max_attempts=max_attempts,
                                 delay=0.001)
    assert mock_bot.send_message.call_count == max_attempts


def test_send_document_file_closed_and_deleted():
    mock_bot = MockBot()
    mock_bot.init_send_document(3)
    path = Path("test_send_document_file_close.txt")
    document = open(path, 'w+')
    send_document_with_retry(bot=mock_bot, chat_id=MockBot.chat_id, document=document, delay=0.01, max_attempts=10)
    assert document.closed
    assert not os.path.exists(path)


@pytest.mark.parametrize(
    "n_exceptions", (1, 3, 5)
)
def test_correct_send_document_file(n_exceptions):
    mock_bot = MockBot()
    mock_bot.init_send_document(n_exceptions)
    path = Path("test_send_document.txt")
    document = open(path, 'w+')
    send_document_with_retry(bot=mock_bot, chat_id=MockBot.chat_id, document=document, delay=0.01, max_attempts=10)
    assert mock_bot.send_document.call_count == n_exceptions + 1
    calls = mock_bot.send_document.call_args_list
    for call in calls:
        _, kwargs = call
        assert kwargs['chat_id'] == MockBot.chat_id
        assert kwargs['document'] == document


@pytest.mark.parametrize(
    "deg", (1, 1.5, 2)
)
def test_convert_deg_to_km(deg):
    assert convert_deg_to_km(deg) == pytest.approx(111.1348 * deg)


@pytest.mark.parametrize(
    "km", (2, 3, 7)
)
def test_convert_km_to_deg(km):
    assert convert_km_to_deg(km) == pytest.approx(km / 111.1348)
