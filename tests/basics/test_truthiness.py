import pytest

from basics.truthiness import describe, is_blank


@pytest.mark.parametrize("value", [None, ""])
def test_is_blank_true(value):
    assert is_blank(value) is True


def test_is_blank_false():
    assert is_blank("글") is False


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, "none"), (0, "falsy"), ("", "falsy"), ([], "falsy"), ({}, "falsy"), (1, "truthy")],
)
def test_describe(value, expected):
    assert describe(value) == expected
