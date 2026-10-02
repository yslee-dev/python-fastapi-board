"""클래스와 dataclass."""

from dataclasses import dataclass, field
from datetime import datetime


class Counter:
    # Java와 달리 필드를 따로 선언하지 않고 __init__에서 self.x = ...로 만든다
    def __init__(self, start: int = 0) -> None:  # 생성자
        self.value = start  # this.value = start

    def increment(self) -> int:
        # 모든 인스턴스 메서드는 첫 인자로 self(= this)를 명시적으로 받는다
        self.value += 1
        return self.value

    def __repr__(self) -> str:  # toString()
        return f"Counter(value={self.value})"


@dataclass
class PostRecord:
    # Lombok @Data와 비슷하다: __init__, __repr__, __eq__를 자동 생성
    id: int
    title: str
    # 리스트 같은 가변 기본값은 반드시 default_factory로 (인스턴스마다 새로 생성)
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


def append_to_shared_default(item: int, bucket: list[int] = []) -> list[int]:  # noqa: B006
    # 함정: 기본값 []는 함수가 '정의될 때' 한 번만 만들어진다.
    # 그래서 호출할 때마다 같은 리스트가 재사용된다. (ruff B006 경고가 이걸 잡아준다)
    bucket.append(item)
    return bucket
