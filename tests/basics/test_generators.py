import pytest

from basics.generators import count_up_to, get_session_like


def test_count_up_to():
    assert list(count_up_to(3)) == [1, 2, 3]


def test_generator_is_lazy():
    gen = count_up_to(10**12)  # 1조 개를 미리 만들지 않는다
    assert next(gen) == 1
    assert next(gen) == 2


def test_dependency_style_generator_runs_cleanup_after_resume():
    events: list[str] = []
    gen = get_session_like(events)

    session = next(gen)  # FastAPI가 요청 처리 전에 하는 일
    assert session == "session"
    assert events == ["open"]

    with pytest.raises(StopIteration):  # FastAPI가 응답 후에 하는 일
        next(gen)
    assert events == ["open", "close"]
