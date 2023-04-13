import pytest
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
