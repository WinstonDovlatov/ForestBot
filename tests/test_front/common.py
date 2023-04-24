from unittest.mock import Mock


class MockBot:
    chat_id = 1230123
    sample_text = "sample text"

    def __init__(self):
        self.send_document = Mock()
        self.send_message = Mock()

    def init_send_message(self, n_exceptions):
        self.send_message.side_effect = [Exception()] * n_exceptions + [None]

    def init_send_document(self, n_exceptions):
        self.send_document.side_effect = [Exception()] * n_exceptions + [None]
