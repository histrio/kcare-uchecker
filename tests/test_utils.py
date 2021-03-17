import uchecker

from mock import patch, mock_open


def test_normalize():
    assert uchecker.normalize("test") == "test"
    assert uchecker.normalize(b"test") == "test"
    assert uchecker.normalize(chr(40960) + 'test' + chr(40960)) == "ꀀtestꀀ"


def test_check_output():
    assert uchecker.check_output(["echo", "1"]) == "1\n"
    assert uchecker.check_output(["false", ]) == ""
