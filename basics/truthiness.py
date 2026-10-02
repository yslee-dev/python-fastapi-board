"""None과 truthy/falsy.

Python의 if는 boolean이 아닌 값도 받는다.
falsy(거짓 취급): None, False, 0, "", [], {}, set()
그 외는 모두 truthy.
"""


def is_blank(value: str | None) -> bool:
    # None과 ""를 한 번에 검사한다 (Java의 StringUtils.isEmpty)
    return not value


def describe(value: object) -> str:
    # None 비교는 항상 `is None`을 쓴다 (== None 아님)
    if value is None:
        return "none"
    # 주의: 0도 falsy다. `if not post_id:`로 검사하면 id=0을 '없음'으로 오해하는 버그가 된다
    if not value:
        return "falsy"
    return "truthy"
