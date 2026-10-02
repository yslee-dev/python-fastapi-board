import pytest

from basics.exceptions_demo import PostNotFoundError, get_title, parse_page


def test_get_title_success():
    assert get_title(1) == "첫 글"


def test_get_title_raises_domain_exception_with_cause():
    with pytest.raises(PostNotFoundError) as exc_info:
        get_title(999)
    assert str(exc_info.value) == "Post 999 not found"
    assert exc_info.value.post_id == 999
    assert isinstance(exc_info.value.__cause__, KeyError)


@pytest.mark.parametrize(("raw", "expected"), [("3", 3), ("0", 1), ("-5", 1), ("abc", 1)])
def test_parse_page(raw, expected):
    assert parse_page(raw) == expected
