"""타입 힌트 기초.

Java: 타입은 컴파일러가 강제한다.
Python: 타입 힌트는 '설명'일 뿐 런타임에 강제되지 않는다.
        단, FastAPI/Pydantic은 이 힌트를 읽어서 실제 검증과 변환에 사용한다.
"""


def greet(name: str, times: int = 1) -> str:
    # Java: public String greet(String name, int times)
    # 기본값 인자(times=1)가 오버로딩을 대신한다.
    return " ".join([f"Hello, {name}!"] * times)


def find_title(titles: dict[int, str], post_id: int) -> str | None:
    # `str | None`은 Java의 @Nullable String에 해당한다.
    # dict.get()은 키가 없으면 예외 대신 None을 돌려준다. (dict[key]는 KeyError)
    return titles.get(post_id)


def add(a: int, b: int) -> int:
    # 힌트는 int지만 "1" + "2"를 넣어도 실행된다 → "12"
    return a + b
