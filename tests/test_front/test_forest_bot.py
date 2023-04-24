import pytest
from unittest.mock import Mock
import telebot

from forestbot.front.utils import *
from forestbot.front.forest_bot import ForestBot
from tests.test_front.common import MockBot


@pytest.fixture(scope='session')
def forestbot():
    forestbot = object.__new__(ForestBot)
    forestbot.user_thresholds = dict()
    forestbot.bot = telebot.TeleBot("123")
    forestbot._ForestBot__add_handlers()
    forestbot._ForestBot__init_messages()
    return forestbot


@pytest.fixture(scope='session')
def handlers(forestbot):
    return forestbot.bot.message_handlers


def get_command_function(handlers, command):
    handler = list(filter(lambda x: x['filters'].get('commands', [None])[0] == command, handlers))[0]['function']
    return handler


def generate_message(command: str, text: str = ""):
    result = Mock()
    result.text = f"/{command} {text}"
    result.chat.id = MockBot.chat_id
    return result


@pytest.mark.parametrize(
    'message_text', ("", "abc", "abc abc abc", "0", "1", "-1", "-1.232", "1.234")
)
def test_handle_threshold_wrong_format(forestbot, handlers, message_text):
    with open("forestbot/front/messages/wrong_threshold.txt", 'r', encoding="UTF-8") as inp:
        wrong_threshold_message = inp.read()
    command = "set_sensitivity"
    message = generate_message(command, message_text)
    handler = get_command_function(handlers=handlers, command=command)
    forestbot.bot = MockBot()
    handler(message)
    args, kwargs = forestbot.bot.send_message.call_args
    assert kwargs['chat_id'] == MockBot.chat_id
    assert kwargs['text'] == wrong_threshold_message


@pytest.mark.parametrize(
    'sensitivity', (0.1, 0.3, 0.55, 0.9)
)
def test_handle_threshold_correct(forestbot, handlers, sensitivity):
    command = "set_sensitivity"
    forestbot.user_thresholds = dict()
    message = generate_message(command, str(sensitivity))
    handler = get_command_function(handlers=handlers, command=command)
    forestbot.bot = MockBot()
    handler(message)
    args, kwargs = forestbot.bot.send_message.call_args
    assert kwargs['chat_id'] == MockBot.chat_id
    assert kwargs['text'] == f"Установлена новая чувствительность: {sensitivity:.2f}"
    assert forestbot.user_thresholds[MockBot.chat_id] == pytest.approx(1 - sensitivity)


def test_handle_start_message(forestbot, handlers):
    with open("forestbot/front/messages/start_message.txt", 'r', encoding="UTF-8") as inp:
        start_message = inp.read()
    command = "start"
    message = generate_message(command)
    handler = get_command_function(handlers=handlers, command=command)
    forestbot.bot = MockBot()
    handler(message)
    args, kwargs = forestbot.bot.send_message.call_args
    assert kwargs['chat_id'] == MockBot.chat_id
    assert kwargs['text'] == start_message


def test_handle_help_message(forestbot, handlers):
    with open("forestbot/front/messages/help_message.txt", 'r', encoding="UTF-8") as inp:
        help_message = inp.read()
    command = "help"
    message = generate_message(command)
    handler = get_command_function(handlers=handlers, command=command)
    forestbot.bot = MockBot()
    handler(message)
    args, kwargs = forestbot.bot.send_message.call_args
    assert kwargs['chat_id'] == MockBot.chat_id
    assert kwargs['text'] == help_message


@pytest.mark.parametrize(
    'message_text', ("", "abc", "abc abc abc", f"{ForestBot.min_radius_km * 0.9}", f"{ForestBot.max_radius_km * 1.1}")
)
def test_handle_change_radius_message_incorrect(forestbot, handlers, message_text):
    command = "set_radius"
    message = generate_message(command, message_text)
    handler = get_command_function(handlers=handlers, command=command)
    forestbot.bot = MockBot()
    handler(message)
    args, kwargs = forestbot.bot.send_message.call_args
    assert kwargs['chat_id'] == MockBot.chat_id
    assert kwargs['text'] == forestbot.wrong_change_radius_message


@pytest.mark.parametrize(
    'message_text', (f"{ForestBot.min_radius_km}", f"{ForestBot.max_radius_km}",
                     f"{(ForestBot.max_radius_km + ForestBot.min_radius_km) / 2}")
)
def test_handle_change_radius_message_correct(forestbot, handlers, message_text):
    forestbot.user_radiuses_deg = dict()
    command = "set_radius"
    message = generate_message(command, message_text)
    handler = get_command_function(handlers=handlers, command=command)
    forestbot.bot = MockBot()
    handler(message)
    args, kwargs = forestbot.bot.send_message.call_args
    assert kwargs['chat_id'] == MockBot.chat_id
    assert kwargs['text'] == f"Радиус снимка успешно установлен: {round(float(message_text), 2)} км"
    assert forestbot.user_radiuses_deg[MockBot.chat_id] == pytest.approx(convert_km_to_deg(float(message_text)))


@pytest.mark.parametrize(
    "content_type", ('audio', 'sticker', 'video', 'video_note', 'voice', 'contact', 'web_app_data')
)
def test_handle_other_types(forestbot, handlers, content_type):
    handler = list(filter(lambda x: 'sticker' in x['filters']['content_types'], handlers))[0]['function']
    message = Mock()
    message.content_type = content_type
    message.chat.id = MockBot.chat_id
    forestbot.bot = MockBot()
    handler(message)
    args, kwargs = forestbot.bot.send_message.call_args
    assert kwargs['chat_id'] == MockBot.chat_id
    assert kwargs['text'] == forestbot.wrong_file_format_message


if __name__ == '__main__':
    print()
