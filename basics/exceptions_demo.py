"""예외 처리.

Python에는 checked exception이 없다. throws 선언도 없다.
모든 예외는 Java의 RuntimeException처럼 동작한다.
"""


class PostNotFoundError(Exception):
    # Java: class PostNotFoundException extends RuntimeException
    def __init__(self, post_id: int) -> None:
        super().__init__(f"Post {post_id} not found")
        self.post_id = post_id


_TITLES = {1: "첫 글"}


def get_title(post_id: int) -> str:
    try:
        return _TITLES[post_id]  # 없는 키 → KeyError
    except KeyError as e:
        # `from e`는 원인 예외를 연결한다 (Java의 new X(msg, cause))
        # 트레이스백에 "The above exception was the direct cause of ..."로 둘 다 출력된다
        raise PostNotFoundError(post_id) from e


def parse_page(raw: str) -> int:
    try:
        page = int(raw)  # "abc" → ValueError
    except ValueError:
        return 1
    else:
        # try 블록에서 예외가 '안 났을 때만' 실행된다
        return max(page, 1)
