"""컨텍스트 매니저 (with 문).

Java의 try-with-resources와 같다. 블록을 벗어날 때 정리 코드가 '반드시' 실행된다.
SQLAlchemy 세션, 파일, 락 등에 쓰인다.
"""

from collections.abc import Iterator
from contextlib import contextmanager


class FakeSession:
    def __init__(self) -> None:
        self.events: list[str] = []

    def commit(self) -> None:
        self.events.append("commit")

    def rollback(self) -> None:
        self.events.append("rollback")

    def close(self) -> None:
        self.events.append("close")


@contextmanager
def transaction(session: FakeSession) -> Iterator[FakeSession]:
    # @Transactional을 직접 구현하면 이런 모양이다.
    # yield 앞 = 블록 진입 시, yield 뒤 = 블록 종료 시
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise  # 예외를 삼키지 않고 다시 던진다
    finally:
        session.close()


class ManagedResource:
    # 클래스로 만드는 방법: __enter__ / __exit__ (Java의 AutoCloseable.close)
    def __init__(self, log: list[str]) -> None:
        self.log = log
        self.name = "resource"

    def __enter__(self) -> "ManagedResource":
        self.log.append("open")
        return self  # `with ... as x`의 x가 된다

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.log.append("close")
        return False  # False → 예외가 있었다면 그대로 전파
