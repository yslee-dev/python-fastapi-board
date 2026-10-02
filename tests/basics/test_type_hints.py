from basics.type_hints import add, find_title, greet


def test_greet_uses_default_argument():
    assert greet("철수") == "Hello, 철수!"
    assert greet("철수", times=2) == "Hello, 철수! Hello, 철수!"


def test_find_title_returns_none_when_missing():
    titles = {1: "첫 글"}
    assert find_title(titles, 1) == "첫 글"
    assert find_title(titles, 2) is None


def test_type_hints_are_not_enforced_at_runtime():
    # 타입 힌트는 int라고 되어 있지만 문자열을 넣어도 실행된다
    assert add("1", "2") == "12"
