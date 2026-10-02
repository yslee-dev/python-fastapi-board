"""제너레이터 (yield).

yield가 있는 함수는 호출해도 바로 실행되지 않고 '제너레이터 객체'를 돌려준다.
next()를 부를 때마다 다음 yield까지 실행되고 거기서 일시정지한다.
FastAPI의 `Depends` + yield, pytest 픽스처가 모두 이 원리를 쓴다.
"""

from collections.abc import Iterator


def count_up_to(limit: int) -> Iterator[int]:
    n = 1
    while n <= limit:
        yield n  # 값을 하나 내보내고 여기서 멈춘다
        n += 1


def get_session_like(events: list[str]) -> Iterator[str]:
    """FastAPI의 get_db()가 동작하는 방식 그대로.

    1. FastAPI가 next()로 yield까지 실행 → 세션을 엔드포인트에 주입
    2. 응답을 만든 뒤 한 번 더 진행 → finally의 정리 코드 실행
    """
    events.append("open")
    try:
        yield "session"
    finally:
        events.append("close")
