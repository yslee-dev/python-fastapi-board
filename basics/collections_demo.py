"""리스트/딕셔너리 다루기. AI 코드에 가장 많이 나오는 문법들."""


def squares_of_even(numbers: list[int]) -> list[int]:
    # 리스트 컴프리헨션
    # Java: numbers.stream().filter(n -> n % 2 == 0).map(n -> n * n).toList()
    return [n * n for n in numbers if n % 2 == 0]


def index_by_id(posts: list[dict]) -> dict[int, dict]:
    # 딕셔너리 컴프리헨션
    # Java: posts.stream().collect(Collectors.toMap(p -> p.get("id"), p -> p))
    return {post["id"]: post for post in posts}


def paginate(items: list, page: int, size: int) -> list:
    # 슬라이싱 items[start:end] — end는 포함하지 않는다 (List.subList와 같음)
    # 범위를 넘어가도 IndexError 없이 빈 리스트를 돌려준다
    start = (page - 1) * size
    return items[start : start + size]


def first_and_rest(items: list) -> tuple:
    # 언패킹: 왼쪽 변수 개수에 맞춰 값을 나눠 담는다. *rest는 나머지 전부
    first, *rest = items
    return first, rest


def merge(base: dict, updates: dict) -> dict:
    # ** 언패킹으로 새 딕셔너리를 만든다. 같은 키는 뒤에 오는 값이 이긴다
    # PATCH(부분 수정)를 구현할 때 자주 보이는 패턴
    return {**base, **updates}
