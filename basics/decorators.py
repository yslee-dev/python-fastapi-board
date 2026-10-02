"""데코레이터.

@decorator 문법은 `func = decorator(func)`와 완전히 같다.
함수를 받아서 (보통은 감싼) 함수를 돌려주는 함수일 뿐이다.
Spring의 AOP(@Around)나 어노테이션 기반 등록과 비슷한 역할을 한다.
"""

import functools
from collections.abc import Callable
from typing import Any

CALL_LOG: list[str] = []


def log_calls(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)  # 감싼 함수의 이름/문서를 원래 함수 것으로 유지
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # *args: 위치 인자 전부(튜플), **kwargs: 키워드 인자 전부(딕셔너리)
        CALL_LOG.append(f"{func.__name__} called with {args}")
        result = func(*args, **kwargs)
        CALL_LOG.append(f"{func.__name__} returned {result!r}")
        return result

    return wrapper


@log_calls
def add(a: int, b: int) -> int:
    return a + b


class MiniRouter:
    """FastAPI의 @app.get("/path")가 하는 일을 흉내 낸 미니 구현.

    인자를 받는 데코레이터 = '데코레이터를 돌려주는 함수'다.
    """

    def __init__(self) -> None:
        self.routes: dict[str, Callable[[], Any]] = {}

    def get(self, path: str) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
        def decorator(func: Callable[[], Any]) -> Callable[[], Any]:
            self.routes[path] = func  # 경로 → 함수를 등록만 하고
            return func  # 원래 함수를 그대로 돌려준다

        return decorator

    def handle(self, path: str) -> tuple[int, Any]:
        handler = self.routes.get(path)
        if handler is None:
            return 404, None
        return 200, handler()
