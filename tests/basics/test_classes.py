from datetime import datetime

from basics.classes import Counter, PostRecord, append_to_shared_default


def test_counter_keeps_state_on_self():
    counter = Counter(start=10)
    assert counter.increment() == 11
    assert repr(counter) == "Counter(value=11)"


def test_dataclass_generates_eq_and_repr():
    fixed = datetime(2026, 1, 1)
    a = PostRecord(id=1, title="제목", created_at=fixed)
    b = PostRecord(id=1, title="제목", created_at=fixed)
    assert a == b
    assert "PostRecord(id=1, title='제목'" in repr(a)


def test_dataclass_default_factory_does_not_share_list():
    a = PostRecord(id=1, title="a")
    b = PostRecord(id=2, title="b")
    a.tags.append("python")
    assert b.tags == []


def test_mutable_default_argument_is_shared():
    first = append_to_shared_default(1)
    second = append_to_shared_default(2)
    assert first is second  # 같은 리스트 객체를 계속 재사용한다 (버그의 원인)
    assert second[-2:] == [1, 2]
