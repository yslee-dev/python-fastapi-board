import pytest

from basics.context_managers import FakeSession, ManagedResource, transaction


def test_transaction_commits_and_closes_on_success():
    session = FakeSession()
    with transaction(session) as s:
        s.events.append("work")
    assert session.events == ["work", "commit", "close"]


def test_transaction_rolls_back_and_closes_on_error():
    session = FakeSession()
    with pytest.raises(ValueError), transaction(session):
        raise ValueError("실패")
    assert session.events == ["rollback", "close"]


def test_class_based_context_manager():
    log: list[str] = []
    with ManagedResource(log) as resource:
        log.append(f"using {resource.name}")
    assert log == ["open", "using resource", "close"]
