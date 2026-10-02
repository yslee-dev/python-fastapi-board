# FastAPI 게시판 학습 프로젝트 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Spring 개발자가 FastAPI 코드를 읽고 디버깅하는 눈을 기르도록, 게시글 CRUD API를 9단계(step-00~08) 커밋으로 쌓아 올린다.

**Architecture:** 단계마다 `main` 브랜치에 커밋 하나 + 태그(`step-NN`) 하나를 만든다. 03단계에서 한 파일짜리 메모리 CRUD로 시작해 04단계에서 PostgreSQL로, 05단계에서 router/service/repository 레이어로 나누고, 06단계에서 테스트 픽스처를 고도화한 뒤, 07단계에서 디버깅 실습, 08단계에서 async로 전환한다. 단계마다 `docs/learning/NN-*.md` 학습 노트를 함께 커밋한다.

**Tech Stack:** Python 3.12, uv, FastAPI(`fastapi[standard]`), Pydantic v2, pydantic-settings, SQLAlchemy 2.0, psycopg 3, Alembic, PostgreSQL 16(docker compose), pytest, pytest-asyncio(08단계), ruff, VS Code + debugpy

**Spec:** `docs/superpowers/specs/2026-10-02-fastapi-board-learning-design.md`

## Global Constraints

- 모든 명령은 프로젝트 루트 `/Users/beplus/Desktop/etc/python-fastapi`에서 실행한다.
- Python은 `uv python pin 3.12`로 고정한다. 시스템 Python 3.10은 건드리지 않는다.
- 패키지 추가는 반드시 `uv add`(런타임) / `uv add --dev`(개발)로 한다. `pip install` 금지.
- PostgreSQL 16, 호스트 포트 **5433** → 컨테이너 5432, 사용자/비밀번호/DB: `board`/`board`/`board`, 테스트 DB: `board_test`.
- DB URL 형식: `postgresql+psycopg://board:board@localhost:5433/board` (테스트: `.../board_test`).
- 코드 주석, 학습 노트, 커밋 메시지는 한글. 변수명/함수명은 영어.
- 모든 커밋 메시지 끝에 빈 줄 + `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.
- 커밋 전에 항상 `uv run ruff check --fix . && uv run ruff format . && uv run ruff check .` 실행 후 통과 확인.
- 각 Task 끝에 `git tag step-NN`을 붙인다.
- 404 응답 본문은 정확히 `{"detail": "Post {id} not found"}`.
- 학습 노트는 4개 섹션 고정: `## 이번에 바뀐 것`, `## Spring이라면?`, `## 디버깅 포인트`, `## 직접 해볼 것`. 맨 위에 `git diff step-(N-1) step-N` 명령을 적는다.
- 학습용 저장소이므로 단계마다 브랜치/PR을 만들지 않고 `main`에 직접 커밋한다 (스펙 2절).

## Review Focus

1. PATCH에 `{"title": null}`처럼 null을 직접 보내면 → 422여야 한다 (DB NOT NULL 위반 500이 나면 안 됨). Task 3 `test_update_post_rejects_explicit_null`.
2. 제목/작성자/내용이 공백만 있으면 (`"   "`) → 422. Task 3 `test_create_post_rejects_blank_title`.
3. 같은 트랜잭션에서 여러 글을 만들어 `created_at`이 같아도 → id 내림차순으로 결정적 정렬. Task 6 `test_find_page_orders_newest_first_even_with_same_created_at`.
4. 마지막 페이지를 넘는 `page` → 200 + 빈 `items` + 올바른 `total`. Task 3 `test_list_posts_page_beyond_last_returns_empty_items`.
5. PATCH 본문에 `author`를 보내도 → 무시되고 작성자가 바뀌지 않는다. Task 3 `test_update_post_ignores_author`.

---

## 파일 구조 (최종)

```
pyproject.toml, uv.lock, .python-version, .gitignore, README.md, .env.example
docker-compose.yml, docker/init.sql                     (Task 4)
alembic.ini, alembic/env.py, alembic/versions/*.py      (Task 4)
basics/__init__.py + 주제별 모듈 8개                     (Task 1)
tests/basics/test_*.py 8개                               (Task 1)
app/__init__.py, app/main.py                             (Task 2~)
app/core/__init__.py, config.py, database.py, exceptions.py, logging.py   (Task 5, 7)
app/posts/__init__.py, router.py, schemas.py, models.py, repository.py, service.py  (Task 5)
tests/test_health.py, tests/test_posts.py                (Task 2, 3~)
tests/conftest.py, tests/test_post_repository.py         (Task 6)
.vscode/settings.json, extensions.json (Task 0), launch.json (Task 7)
docs/learning/00-setup.md ~ 08-async.md
```

---

### Task 0: step-00 프로젝트 셋업

**Files:**
- Create: `pyproject.toml`, `.python-version`(uv가 생성), `uv.lock`(uv가 생성), `.gitignore`, `README.md`, `.vscode/settings.json`, `.vscode/extensions.json`, `docs/learning/00-setup.md`

**Interfaces:**
- Produces: `uv run pytest`, `uv run ruff` 사용 가능. pytest는 `pythonpath = ["."]`로 `app`, `basics` 패키지를 import할 수 있다.

- [ ] **Step 1: pyproject.toml 작성**

```toml
[project]
name = "fastapi-board"
version = "0.1.0"
description = "Spring 개발자를 위한 FastAPI 게시판 CRUD 학습 프로젝트"
readme = "README.md"
requires-python = ">=3.12"
dependencies = []

[tool.ruff]
line-length = 100
target-version = "py312"
extend-exclude = ["alembic"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 2: Python 3.12 고정 + 개발 의존성 설치**

```bash
uv python pin 3.12
uv add --dev pytest ruff
uv run python --version
```
Expected: `Python 3.12.x` 출력, `.python-version`, `uv.lock`, `.venv/` 생성. `pyproject.toml`에 `[dependency-groups] dev = [...]`가 추가됨.

- [ ] **Step 3: .gitignore 작성**

```gitignore
# 가상환경 / 캐시
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/

# 환경 변수 (예시 파일만 커밋)
.env

# 로컬 서버 로그
*.log

# 에디터
.DS_Store
.idea/
```

- [ ] **Step 4: VS Code 설정 작성**

`.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  }
}
```

`.vscode/extensions.json`:
```json
{
  "recommendations": ["ms-python.python", "ms-python.debugpy", "charliermarsh.ruff"]
}
```

- [ ] **Step 5: README.md 작성**

```markdown
# FastAPI 게시판 학습 프로젝트

Spring 개발자가 FastAPI 코드를 읽고 디버깅하는 눈을 기르기 위한 단계별 학습 저장소입니다.

## 학습 방법

단계마다 커밋과 태그(`step-00` ~ `step-08`)가 있습니다.

```bash
git tag                          # 단계 목록
git diff step-02 step-03         # 단계 사이의 변화 보기
git checkout step-03             # 특정 단계로 이동 (돌아올 땐 git checkout main)
```

단계별 학습 노트는 `docs/learning/`에 있습니다.

## 준비물

- [uv](https://docs.astral.sh/uv/)
- Docker
- VS Code (추천 확장은 `.vscode/extensions.json` 참고)

## 자주 쓰는 명령

```bash
uv sync                  # 의존성 설치 (= ./gradlew dependencies)
uv run pytest            # 테스트 (= ./gradlew test)
uv run ruff check .      # 린트
uv run ruff format .     # 포맷
```
```

- [ ] **Step 6: 학습 노트 `docs/learning/00-setup.md` 작성**

반드시 포함할 내용:
- 맨 위: `git show step-00 --stat`
- **이번에 바뀐 것:** uv, `pyproject.toml`, `.python-version`, `uv.lock`, `.venv`가 각각 무엇인지
- **Spring이라면?:** 표로 대응 — `pyproject.toml`↔`build.gradle`, `uv.lock`↔`gradle.lockfile`, `.venv`↔(프로젝트 전용 JDK + 의존성 jar 폴더), `uv run X`↔`./gradlew X`, `uv add`↔`implementation(...)` 추가, `[dependency-groups] dev`↔`testImplementation`
- **디버깅 포인트:** `ModuleNotFoundError`가 나면 대부분 가상환경 밖의 python을 쓴 것 → `uv run`으로 실행했는지, VS Code 우측 하단 인터프리터가 `.venv`인지 확인. `which python` vs `uv run which python` 비교
- **직접 해볼 것:** `uv run python -c "import sys; print(sys.executable)"` 실행해 보기, `uv add httpx` 후 `pyproject.toml` 변화 확인하고 `uv remove httpx`로 되돌리기

- [ ] **Step 7: 검증**

```bash
uv run ruff check . && uv run ruff format --check . && uv run python --version
```
Expected: ruff 통과, `Python 3.12.x`

- [ ] **Step 8: 커밋 + 태그**

```bash
git add -A
git commit -m "chore: uv 기반 프로젝트 셋업 (step-00)

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
git tag step-00
```

---

### Task 1: step-01 파이썬 기초 예제

**Files:**
- Create: `basics/__init__.py`(빈 파일), `basics/type_hints.py`, `basics/collections_demo.py`, `basics/truthiness.py`, `basics/classes.py`, `basics/exceptions_demo.py`, `basics/decorators.py`, `basics/context_managers.py`, `basics/generators.py`
- Test: `tests/basics/test_type_hints.py`, `test_collections_demo.py`, `test_truthiness.py`, `test_classes.py`, `test_exceptions_demo.py`, `test_decorators.py`, `test_context_managers.py`, `test_generators.py`
- Create: `docs/learning/01-basics.md`

**Interfaces:**
- Produces: 이후 단계에서 import하지 않는다. 학습 노트 04/06단계가 `basics/generators.py`의 `get_session_like`, `basics/context_managers.py`의 `transaction`, `basics/decorators.py`의 `MiniRouter`를 참조한다.

- [ ] **Step 1: 테스트 8개 파일 먼저 작성**

`tests/basics/test_type_hints.py`:
```python
from basics.type_hints import add, find_title, greet


def test_greet_uses_default_argument():
    assert greet("철수") == "Hello, 철수!"
    assert greet("철수", times=2) == "Hello, 철수! Hello, 철수!"


def test_find_title_returns_none_when_missing():
    titles = {1: "첫 글"}
    assert find_title(titles, 1) == "첫 글"
    assert find_title(titles, 2) is None


def test_type_hints_are_not_enforced_at_runtime():
    # 타입 힌트는 int라고 되어 있지만 문자열을 넣어도 실행된다
    assert add("1", "2") == "12"
```

`tests/basics/test_collections_demo.py`:
```python
from basics.collections_demo import first_and_rest, index_by_id, merge, paginate, squares_of_even


def test_squares_of_even():
    assert squares_of_even([1, 2, 3, 4]) == [4, 16]


def test_index_by_id():
    posts = [{"id": 1, "title": "a"}, {"id": 2, "title": "b"}]
    assert index_by_id(posts) == {1: {"id": 1, "title": "a"}, 2: {"id": 2, "title": "b"}}


def test_paginate_uses_slicing():
    items = list(range(1, 11))
    assert paginate(items, page=1, size=3) == [1, 2, 3]
    assert paginate(items, page=4, size=3) == [10]
    assert paginate(items, page=5, size=3) == []


def test_first_and_rest_unpacking():
    assert first_and_rest([1, 2, 3]) == (1, [2, 3])


def test_merge_later_values_win():
    base = {"title": "원래 제목", "content": "원래 내용"}
    assert merge(base, {"title": "새 제목"}) == {"title": "새 제목", "content": "원래 내용"}
    assert base["title"] == "원래 제목"  # 원본은 바뀌지 않는다
```

`tests/basics/test_truthiness.py`:
```python
import pytest

from basics.truthiness import describe, is_blank


@pytest.mark.parametrize("value", [None, ""])
def test_is_blank_true(value):
    assert is_blank(value) is True


def test_is_blank_false():
    assert is_blank("글") is False


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, "none"), (0, "falsy"), ("", "falsy"), ([], "falsy"), ({}, "falsy"), (1, "truthy")],
)
def test_describe(value, expected):
    assert describe(value) == expected
```

`tests/basics/test_classes.py`:
```python
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
```

`tests/basics/test_exceptions_demo.py`:
```python
import pytest

from basics.exceptions_demo import PostNotFoundError, get_title, parse_page


def test_get_title_success():
    assert get_title(1) == "첫 글"


def test_get_title_raises_domain_exception_with_cause():
    with pytest.raises(PostNotFoundError) as exc_info:
        get_title(999)
    assert str(exc_info.value) == "Post 999 not found"
    assert exc_info.value.post_id == 999
    assert isinstance(exc_info.value.__cause__, KeyError)


@pytest.mark.parametrize(("raw", "expected"), [("3", 3), ("0", 1), ("-5", 1), ("abc", 1)])
def test_parse_page(raw, expected):
    assert parse_page(raw) == expected
```

`tests/basics/test_decorators.py`:
```python
from basics.decorators import CALL_LOG, MiniRouter, add


def test_log_calls_wraps_function():
    CALL_LOG.clear()
    assert add(1, 2) == 3
    assert CALL_LOG == ["add called with (1, 2)", "add returned 3"]


def test_functools_wraps_keeps_name():
    assert add.__name__ == "add"


def test_mini_router_registers_handlers():
    router = MiniRouter()

    @router.get("/health")
    def health():
        return {"status": "ok"}

    assert router.handle("/health") == (200, {"status": "ok"})
    assert router.handle("/nope") == (404, None)
    # 데코레이터가 원래 함수를 그대로 돌려주므로 직접 호출도 된다
    assert health() == {"status": "ok"}
```

`tests/basics/test_context_managers.py`:
```python
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
```

`tests/basics/test_generators.py`:
```python
import pytest

from basics.generators import count_up_to, get_session_like


def test_count_up_to():
    assert list(count_up_to(3)) == [1, 2, 3]


def test_generator_is_lazy():
    gen = count_up_to(10**12)  # 1조 개를 미리 만들지 않는다
    assert next(gen) == 1
    assert next(gen) == 2


def test_dependency_style_generator_runs_cleanup_after_resume():
    events: list[str] = []
    gen = get_session_like(events)

    session = next(gen)  # FastAPI가 요청 처리 전에 하는 일
    assert session == "session"
    assert events == ["open"]

    with pytest.raises(StopIteration):  # FastAPI가 응답 후에 하는 일
        next(gen)
    assert events == ["open", "close"]
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `uv run pytest tests/basics -q`
Expected: 8개 파일 모두 `ModuleNotFoundError: No module named 'basics'` (수집 에러)

- [ ] **Step 3: `basics/__init__.py`(빈 파일)와 모듈 8개 구현**

`basics/type_hints.py`:
```python
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
```

`basics/collections_demo.py`:
```python
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
```

`basics/truthiness.py`:
```python
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
```

`basics/classes.py`:
```python
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
```

`basics/exceptions_demo.py`:
```python
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
```

`basics/decorators.py`:
```python
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
```

`basics/context_managers.py`:
```python
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
```

`basics/generators.py`:
```python
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
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `uv run pytest tests/basics -v`
Expected: 전부 PASS (parametrize 포함 약 25개)

- [ ] **Step 5: 학습 노트 `docs/learning/01-basics.md` 작성**

반드시 포함할 내용:
- 맨 위: `git diff step-00 step-01 --stat`, 추천 읽기 순서(type_hints → collections_demo → truthiness → classes → exceptions_demo → decorators → context_managers → generators)
- **이번에 바뀐 것:** 모듈별 한 줄 요약
- **Spring이라면?:** 표 — 리스트 컴프리헨션↔Stream, `@dataclass`↔Lombok `@Data`, `str | None`↔`@Nullable`, `raise X from e`↔`new X(msg, cause)`, 데코레이터↔AOP/어노테이션 등록, `with`↔try-with-resources, `@contextmanager`↔`@Transactional`의 내부 동작, `yield`↔(대응 없음: Iterator를 손으로 구현하는 것과 비슷)
- **디버깅 포인트:** 이 단계의 패턴이 FastAPI에서 어디에 나오는지 미리 연결 — `@app.get`(MiniRouter), `Depends(get_db)` + yield(get_session_like), pytest 픽스처 yield, `if not x`로 0을 놓치는 버그, 가변 기본값 버그, 트레이스백의 "direct cause" 문구
- **직접 해볼 것:** `tests/basics/test_generators.py`에 브레이크포인트 없이 `uv run pytest tests/basics/test_generators.py -v -s`를 돌리고 `get_session_like`에 `print`를 넣어 실행 순서 관찰하기; `add`에서 `@functools.wraps`를 지우고 어떤 테스트가 왜 깨지는지 확인하기

- [ ] **Step 6: 린트 + 커밋 + 태그**

```bash
uv run ruff check --fix . && uv run ruff format . && uv run ruff check . && uv run pytest -q
git add -A
git commit -m "docs: 파이썬 기초 문법 예제와 테스트 추가 (step-01)

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
git tag step-01
```

---

### Task 2: step-02 FastAPI Hello

**Files:**
- Create: `app/__init__.py`(빈 파일), `app/main.py`, `tests/test_health.py`, `docs/learning/02-hello.md`
- Modify: `pyproject.toml`(uv add로 자동), `README.md`(서버 실행 명령 추가)

**Interfaces:**
- Produces: `app.main.app: FastAPI`, `GET /health → {"status": "ok"}`

- [ ] **Step 1: FastAPI 설치**

```bash
uv add "fastapi[standard]"
```
Expected: `fastapi`, `uvicorn`, `httpx`, `fastapi-cli` 등이 설치됨

- [ ] **Step 2: 실패하는 테스트 작성** — `tests/test_health.py`

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 3: 실패 확인**

Run: `uv run pytest tests/test_health.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 4: 구현** — `app/__init__.py`(빈 파일), `app/main.py`

```python
"""애플리케이션 진입점. Spring의 @SpringBootApplication 클래스에 해당한다."""

from fastapi import FastAPI

app = FastAPI(title="Board API")


@app.get("/health")
def health() -> dict[str, str]:
    # 반환한 dict는 FastAPI가 JSON으로 직렬화한다 (@RestController + Jackson)
    return {"status": "ok"}
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `uv run pytest -q`
Expected: 전부 PASS

- [ ] **Step 6: 실제 서버 실행 확인**

```bash
uv run fastapi dev app/main.py --port 8000 > server.log 2>&1 &
sleep 4
curl -s localhost:8000/health
curl -s -o /dev/null -w "%{http_code}\n" localhost:8000/docs
kill %1
```
Expected: `{"status":"ok"}`, `200`.

- [ ] **Step 7: README에 실행 섹션 추가**

`## 자주 쓰는 명령` 코드 블록에 다음 줄 추가:
```bash
uv run fastapi dev app/main.py   # 개발 서버 (자동 재시작) → http://localhost:8000/docs
```

- [ ] **Step 8: 학습 노트 `docs/learning/02-hello.md` 작성**

반드시 포함할 내용:
- 맨 위: `git diff step-01 step-02`
- **이번에 바뀐 것:** `app = FastAPI()`, `@app.get`, Uvicorn(ASGI 서버), `fastapi dev`의 자동 리로드, `/docs`(Swagger UI)와 `/openapi.json`
- **Spring이라면?:** `FastAPI()`↔`SpringApplication`, `@app.get("/health")`↔`@GetMapping("/health")`, Uvicorn↔내장 Tomcat, `/docs`↔springdoc-openapi, `TestClient`↔MockMvc. `@app.get`이 01단계 `MiniRouter.get`과 같은 원리임을 연결
- **디버깅 포인트:** 서버 로그 한 줄(`INFO: 127.0.0.1 - "GET /health HTTP/1.1" 200 OK`) 읽는 법, 404 `{"detail":"Not Found"}`는 경로 매칭 실패, 405는 메서드 불일치, 포트 충돌 시 `[Errno 48] Address already in use` → `lsof -i :8000`
- **직접 해볼 것:** `/hello/{name}` 엔드포인트를 직접 추가해 보고 `/docs`에서 호출해 보기 (커밋하지 않음)

- [ ] **Step 9: 린트 + 커밋 + 태그**

```bash
uv run ruff check --fix . && uv run ruff format . && uv run ruff check . && uv run pytest -q
git add -A
git commit -m "feat: FastAPI 앱과 헬스 체크 엔드포인트 추가 (step-02)

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
git tag step-02
```

---

### Task 3: step-03 메모리 CRUD (한 파일)

**Files:**
- Modify: `app/main.py` (전체 교체)
- Create: `tests/test_posts.py`, `docs/learning/03-memory-crud.md`

**Interfaces:**
- Consumes: `app.main.app`
- Produces:
  - 스키마 이름(이후 단계에서 그대로 유지): `PostCreate(title, content, author)`, `PostUpdate(title?, content?)`, `PostResponse(id, title, content, author, created_at, updated_at)`, `PostListResponse(items, total, page, size)`
  - API 계약 (스펙 4절): `POST /posts`→201, `GET /posts?page&size`→200, `GET/PATCH/DELETE /posts/{post_id}`→200/200/204, 없으면 404 `{"detail": "Post {id} not found"}`
  - `tests/test_posts.py`의 테스트 **본문**은 이후 07단계까지 바뀌지 않는다. `client` 픽스처만 단계마다 바뀐다.

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/test_posts.py`

```python
import pytest
from fastapi.testclient import TestClient

from app import main


@pytest.fixture
def client() -> TestClient:
    # 메모리 저장소를 테스트마다 비운다
    main._posts.clear()
    main._next_id = 1
    return TestClient(main.app)


def create_post(client: TestClient, **overrides: str) -> dict:
    payload = {"title": "제목", "content": "내용", "author": "홍길동"} | overrides
    response = client.post("/posts", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# --- 생성 ---


def test_create_post(client):
    response = client.post("/posts", json={"title": "첫 글", "content": "안녕", "author": "홍길동"})

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["title"] == "첫 글"
    assert body["content"] == "안녕"
    assert body["author"] == "홍길동"
    assert body["created_at"]
    assert body["updated_at"]


def test_create_post_rejects_too_long_title(client):
    response = client.post("/posts", json={"title": "a" * 101, "content": "c", "author": "a"})

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", "title"]
    assert error["type"] == "string_too_long"


def test_create_post_rejects_blank_title(client):
    response = client.post("/posts", json={"title": "   ", "content": "c", "author": "a"})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "title"]


def test_create_post_requires_author(client):
    response = client.post("/posts", json={"title": "t", "content": "c"})

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", "author"]
    assert error["type"] == "missing"


# --- 조회 ---


def test_get_post(client):
    created = create_post(client)

    response = client.get(f"/posts/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_post_not_found(client):
    response = client.get("/posts/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Post 999 not found"}


def test_get_post_with_non_integer_id(client):
    response = client.get("/posts/abc")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "post_id"]


# --- 목록 ---


def test_list_posts_newest_first_with_pagination(client):
    for title in ["1", "2", "3"]:
        create_post(client, title=title)

    first_page = client.get("/posts", params={"page": 1, "size": 2}).json()
    second_page = client.get("/posts", params={"page": 2, "size": 2}).json()

    assert [p["title"] for p in first_page["items"]] == ["3", "2"]
    assert first_page["total"] == 3
    assert first_page["page"] == 1
    assert first_page["size"] == 2
    assert [p["title"] for p in second_page["items"]] == ["1"]


def test_list_posts_uses_default_paging(client):
    body = client.get("/posts").json()

    assert body == {"items": [], "total": 0, "page": 1, "size": 10}


def test_list_posts_page_beyond_last_returns_empty_items(client):
    create_post(client)

    body = client.get("/posts", params={"page": 5}).json()

    assert body["items"] == []
    assert body["total"] == 1


@pytest.mark.parametrize("params", [{"page": 0}, {"size": 0}, {"size": 101}])
def test_list_posts_rejects_invalid_paging(client, params):
    response = client.get("/posts", params=params)

    assert response.status_code == 422


# --- 수정 ---


def test_update_post_partially(client):
    created = create_post(client, title="원래 제목", content="원래 내용")

    response = client.patch(f"/posts/{created['id']}", json={"title": "새 제목"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "새 제목"
    assert body["content"] == "원래 내용"  # 보내지 않은 필드는 유지
    assert body["author"] == "홍길동"


def test_update_post_rejects_explicit_null(client):
    created = create_post(client)

    response = client.patch(f"/posts/{created['id']}", json={"title": None})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "title"]


def test_update_post_ignores_author(client):
    created = create_post(client, author="홍길동")

    response = client.patch(f"/posts/{created['id']}", json={"author": "임꺽정"})

    assert response.status_code == 200
    assert response.json()["author"] == "홍길동"


def test_update_post_not_found(client):
    response = client.patch("/posts/999", json={"title": "새 제목"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Post 999 not found"}


# --- 삭제 ---


def test_delete_post(client):
    created = create_post(client)

    response = client.delete(f"/posts/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/posts/{created['id']}").status_code == 404


def test_delete_post_not_found(client):
    response = client.delete("/posts/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Post 999 not found"}
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/test_posts.py -q`
Expected: FAIL — `AttributeError: module 'app.main' has no attribute '_posts'`

- [ ] **Step 3: 구현** — `app/main.py` 전체 교체

```python
"""03단계: 메모리(dict) 저장소로 만든 게시글 CRUD.

모든 코드를 한 파일에 두어 '요청 → 검증 → 처리 → 응답' 흐름을 한눈에 본다.
05단계에서 router / service / repository로 나눈다.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

app = FastAPI(title="Board API")


# --- 스키마 (DTO) ---


class PostCreate(BaseModel):
    # 요청 바디 DTO. Field 제약은 Bean Validation의 @Size, @NotBlank 역할
    # str_strip_whitespace: 앞뒤 공백 제거 → "   "는 ""가 되어 min_length에서 걸린다
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=50)


class PostUpdate(BaseModel):
    # PATCH용 DTO. 모든 필드가 선택. author는 수정 불가라 아예 없다
    # (정의되지 않은 필드가 들어오면 Pydantic은 기본적으로 조용히 무시한다)
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1)

    @field_validator("title", "content")
    @classmethod
    def reject_explicit_null(cls, value: str | None) -> str:
        # 필드를 '안 보낸' 경우엔 실행되지 않고, null을 '직접 보낸' 경우에만 실행된다
        if value is None:
            raise ValueError("null로 수정할 수 없습니다")
        return value


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author: str
    created_at: datetime
    updated_at: datetime


class PostListResponse(BaseModel):
    items: list[PostResponse]
    total: int
    page: int
    size: int


# --- 저장소 (메모리) ---

_posts: dict[int, PostResponse] = {}
_next_id = 1


def _find_or_404(post_id: int) -> PostResponse:
    post = _posts.get(post_id)
    if post is None:
        # HTTPException을 던지면 FastAPI가 {"detail": ...} 응답으로 바꿔준다
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post {post_id} not found")
    return post


# --- 엔드포인트 ---


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate) -> PostResponse:
    # payload: 요청 JSON이 PostCreate로 검증·변환된 객체 (@RequestBody @Valid)
    global _next_id  # 모듈 변수를 '재할당'하려면 필요하다. 없으면 UnboundLocalError
    now = datetime.now(UTC)
    post = PostResponse(id=_next_id, **payload.model_dump(), created_at=now, updated_at=now)
    _posts[post.id] = post
    _next_id += 1
    return post


@app.get("/posts")
def list_posts(
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> PostListResponse:
    # 경로에 없는 단순 타입 인자는 쿼리 파라미터가 된다 (@RequestParam)
    ordered = sorted(_posts.values(), key=lambda p: p.id, reverse=True)
    start = (page - 1) * size
    return PostListResponse(
        items=ordered[start : start + size], total=len(ordered), page=page, size=size
    )


@app.get("/posts/{post_id}")
def get_post(post_id: int) -> PostResponse:
    # 경로의 {post_id}와 이름이 같은 인자가 경로 변수가 된다 (@PathVariable)
    return _find_or_404(post_id)


@app.patch("/posts/{post_id}")
def update_post(post_id: int, payload: PostUpdate) -> PostResponse:
    post = _find_or_404(post_id)
    # exclude_unset=True: 클라이언트가 '실제로 보낸' 필드만 꺼낸다
    changes = payload.model_dump(exclude_unset=True)
    updated = post.model_copy(update={**changes, "updated_at": datetime.now(UTC)})
    _posts[post_id] = updated
    return updated


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int) -> None:
    _find_or_404(post_id)
    del _posts[post_id]
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `uv run pytest -q`
Expected: 전부 PASS. 실패하면 `-x -vv`로 첫 실패만 보고 고친다.

- [ ] **Step 5: 학습 노트 `docs/learning/03-memory-crud.md` 작성**

반드시 포함할 내용:
- 맨 위: `git diff step-02 step-03 -- app/`
- **이번에 바뀐 것:** 스키마 4개의 역할, 경로/쿼리/바디 파라미터를 FastAPI가 어떻게 구분하는지(경로에 있음→path, BaseModel→body, 나머지→query), `Annotated[int, Query(ge=1)]`, `HTTPException`, `exclude_unset`, `model_copy(update=...)`, `global`
- **Spring이라면?:** `BaseModel`↔DTO+Bean Validation, `Field(min_length, max_length)`↔`@Size`, 422↔400 `MethodArgumentNotValidException`(FastAPI는 422를 쓴다), `HTTPException`↔`ResponseStatusException`, 반환 타입 힌트↔`ResponseEntity<PostResponse>`
- **디버깅 포인트:** 422 응답 구조 해부 — `detail[].loc`(어디: `["body","title"]`, `["path","post_id"]`, `["query","size"]`), `type`(왜: `missing`, `string_too_long`, `int_parsing`, `value_error`), `msg`, `input`. 실제로 `curl`로 422를 하나 발생시켜 출력 전문을 붙여넣고 각 필드에 주석 달기
- **직접 해볼 것:** `exclude_unset=True`를 지우고 어떤 테스트가 왜 깨지는지 확인 / `global _next_id` 줄을 지우고 생기는 `UnboundLocalError` 트레이스백 읽기 / `/docs`에서 POST로 글 만들기

- [ ] **Step 6: 린트 + 커밋 + 태그**

```bash
uv run ruff check --fix . && uv run ruff format . && uv run ruff check . && uv run pytest -q
git add -A
git commit -m "feat: 메모리 저장소 기반 게시글 CRUD API 추가 (step-03)

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
git tag step-03
```

---

### Task 4: step-04 PostgreSQL + SQLAlchemy + Alembic

**Files:**
- Create: `docker-compose.yml`, `docker/init.sql`, `app/database.py`, `app/models.py`, `alembic.ini`(alembic init), `alembic/env.py`(교체), `alembic/versions/<rev>_create_posts_table.py`(autogenerate), `docs/learning/04-database.md`
- Modify: `app/main.py`, `tests/test_posts.py`(픽스처만 교체), `README.md`

**Interfaces:**
- Consumes: Task 3의 스키마/엔드포인트 계약, `tests/test_posts.py` 테스트 본문
- Produces:
  - `app.database`: `DATABASE_URL: str`, `engine`, `SessionLocal`, `class Base(DeclarativeBase)`, `def get_db() -> Iterator[Session]`
  - `app.models.Post` (테이블 `posts`: `id`, `title VARCHAR(100)`, `content TEXT`, `author VARCHAR(50)`, `created_at`, `updated_at` — 모두 NOT NULL, timestamptz)

- [ ] **Step 1: 포트 확인 후 DB 컨테이너 파일 작성**

```bash
lsof -i :5433 || echo "5433 free"
```
Expected: `5433 free`. 사용 중이면 멈추고 사람에게 보고한다.

`docker-compose.yml`:
```yaml
services:
  db:
    image: postgres:16
    container_name: fastapi-board-db
    environment:
      POSTGRES_USER: board
      POSTGRES_PASSWORD: board
      POSTGRES_DB: board
    ports:
      - "5433:5432"
    volumes:
      - db-data:/var/lib/postgresql/data
      # 컨테이너 최초 생성 시 한 번만 실행된다 (테스트 DB 생성)
      - ./docker/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U board -d board"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  db-data:
```

`docker/init.sql`:
```sql
-- 테스트 전용 DB. 테스트는 이 DB에서만 테이블을 만들고 지운다.
CREATE DATABASE board_test OWNER board;
```

- [ ] **Step 2: DB 기동 확인**

```bash
docker compose up -d --wait
docker compose exec db psql -U board -d board -c '\l' | grep board_test
```
Expected: `board_test` 행 출력

- [ ] **Step 3: 의존성 설치**

```bash
uv add sqlalchemy "psycopg[binary]" alembic
```

- [ ] **Step 4: 테스트 픽스처를 DB용으로 교체 (테스트 본문은 그대로)** — `tests/test_posts.py` 상단의 import와 `client` 픽스처만 아래로 교체

```python
import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+psycopg://board:board@localhost:5433/board_test"
)
test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def client() -> Iterator[TestClient]:
    # 04단계의 단순한 방식: 테스트마다 테이블을 만들고 지운다 (06단계에서 개선)
    Base.metadata.create_all(test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # get_db 대신 테스트 DB 세션을 주입한다 (@MockBean / @TestConfiguration 역할)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(test_engine)
```

`create_post` 헬퍼와 `def test_...` 함수들은 **한 글자도 바꾸지 않는다.**

- [ ] **Step 5: 실패 확인**

Run: `uv run pytest tests/test_posts.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.database'`

- [ ] **Step 6: `app/database.py` 작성**

```python
"""DB 연결과 세션 관리. Spring의 DataSource + EntityManager 설정에 해당한다."""

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# 05단계에서 pydantic-settings로 옮긴다
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://board:board@localhost:5433/board")

# engine = 커넥션 풀 (HikariDataSource)
engine = create_engine(DATABASE_URL)

# SessionLocal() 호출마다 새 세션(= 영속성 컨텍스트, EntityManager)을 만든다
# expire_on_commit=False: commit 후에도 객체 속성을 다시 조회하지 않고 그대로 쓴다
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """모든 ORM 모델의 부모. Base.metadata에 테이블 정의가 모인다."""


def get_db() -> Iterator[Session]:
    # 요청 하나당 세션 하나. FastAPI가 yield 앞을 요청 전에, 뒤를 응답 후에 실행한다
    # (01단계 basics/generators.py의 get_session_like와 같은 구조)
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

- [ ] **Step 7: `app/models.py` 작성**

```python
"""ORM 모델. JPA의 @Entity에 해당한다."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Post(Base):
    __tablename__ = "posts"

    # Mapped[int]처럼 Optional이 아니면 NOT NULL 컬럼이 된다
    id: Mapped[int] = mapped_column(primary_key=True)  # @Id @GeneratedValue
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(String(50))
    # server_default: INSERT 시 DB가 now()로 채운다 (@CreationTimestamp)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # onupdate: ORM으로 UPDATE할 때 now()로 바꾼다 (@UpdateTimestamp)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

- [ ] **Step 8: `app/main.py`를 DB 버전으로 교체**

스키마 `PostCreate`, `PostUpdate`, `PostListResponse`는 Task 3과 동일하게 두고, `PostResponse`에만 `model_config = ConfigDict(from_attributes=True)`를 추가한다. 메모리 저장소(`_posts`, `_next_id`, 기존 `_find_or_404`)와 엔드포인트 5개를 아래로 교체한다. 파일 전체:

```python
"""04단계: PostgreSQL에 저장하는 게시글 CRUD.

03단계와 비교해서 저장소만 dict → DB로 바뀌었다. 스키마와 API 계약은 그대로다.
"""

from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Post

app = FastAPI(title="Board API")

# 매번 `db: Session = Depends(get_db)`라고 쓰는 대신 별칭을 만든다
DbSession = Annotated[Session, Depends(get_db)]


# --- 스키마 (DTO) ---


class PostCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=50)


class PostUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1)

    @field_validator("title", "content")
    @classmethod
    def reject_explicit_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("null로 수정할 수 없습니다")
        return value


class PostResponse(BaseModel):
    # from_attributes: dict가 아닌 ORM 객체의 속성(post.title)에서 값을 읽을 수 있게 한다
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    author: str
    created_at: datetime
    updated_at: datetime


class PostListResponse(BaseModel):
    items: list[PostResponse]
    total: int
    page: int
    size: int


# --- 헬퍼 ---


def _find_or_404(db: Session, post_id: int) -> Post:
    post = db.get(Post, post_id)  # PK 조회 (em.find)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post {post_id} not found")
    return post


# --- 엔드포인트 ---


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, db: DbSession) -> Post:
    # response_model을 지정하면 반환한 ORM 객체를 PostResponse 모양으로 직렬화한다
    post = Post(**payload.model_dump())
    db.add(post)  # em.persist
    db.commit()  # @Transactional이 없으므로 직접 커밋해야 저장된다
    db.refresh(post)  # DB가 채운 id, created_at을 다시 읽어온다
    return post


@app.get("/posts", response_model=PostListResponse)
def list_posts(
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> PostListResponse:
    stmt = (
        select(Post)
        .order_by(Post.created_at.desc(), Post.id.desc())  # 같은 시각이면 id로 결정
        .offset((page - 1) * size)
        .limit(size)
    )
    posts = db.scalars(stmt).all()
    total = db.scalar(select(func.count()).select_from(Post)) or 0
    return PostListResponse(
        items=[PostResponse.model_validate(post) for post in posts],
        total=total,
        page=page,
        size=size,
    )


@app.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: DbSession) -> Post:
    return _find_or_404(db, post_id)


@app.patch("/posts/{post_id}", response_model=PostResponse)
def update_post(post_id: int, payload: PostUpdate, db: DbSession) -> Post:
    post = _find_or_404(db, post_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(post, field, value)  # post.title = value 와 같다 (더티 체킹 대상이 됨)
    db.commit()
    db.refresh(post)
    return post


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: DbSession) -> None:
    post = _find_or_404(db, post_id)
    db.delete(post)
    db.commit()
```

- [ ] **Step 9: 테스트 통과 확인**

Run: `uv run pytest -q`
Expected: 전부 PASS (DB 컨테이너가 떠 있어야 함)

- [ ] **Step 10: Alembic 초기화 + env.py 교체**

```bash
uv run alembic init alembic
```

`alembic/env.py` 전체를 아래로 교체:
```python
"""Alembic 실행 환경. Flyway 설정에 해당한다."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app import models  # noqa: F401  모델을 import해야 Base.metadata에 테이블이 등록된다
from app.database import DATABASE_URL, Base

config = context.config
# alembic.ini 대신 앱과 같은 DB URL을 쓴다
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# autogenerate가 비교할 '기대 스키마'
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

`alembic.ini`의 `sqlalchemy.url = driver://user:pass@localhost/dbname` 줄은 그대로 둔다 (env.py가 덮어쓴다).

- [ ] **Step 11: 첫 마이그레이션 생성 + 적용**

```bash
uv run alembic revision --autogenerate -m "create posts table"
uv run alembic upgrade head
docker compose exec db psql -U board -d board -c '\d posts'
```
Expected: 생성된 `alembic/versions/*_create_posts_table.py`의 `upgrade()`에 `op.create_table('posts', ...)`가 있고 6개 컬럼이 모두 `nullable=False`. `\d posts` 출력에 6개 컬럼과 `posts_pkey`. 다르면 멈추고 모델을 확인한다.

- [ ] **Step 12: 실제 서버로 CRUD 확인**

```bash
uv run fastapi dev app/main.py --port 8000 > server.log 2>&1 &
sleep 4
curl -s -X POST localhost:8000/posts -H 'Content-Type: application/json' \
  -d '{"title":"첫 글","content":"안녕하세요","author":"홍길동"}'
curl -s "localhost:8000/posts?page=1&size=10"
curl -s -X PATCH localhost:8000/posts/1 -H 'Content-Type: application/json' -d '{"title":"수정"}'
curl -s -o /dev/null -w "%{http_code}\n" -X DELETE localhost:8000/posts/1
curl -s localhost:8000/posts/1
kill %1
```
Expected: 201 본문(id=1) → 목록 total 1 → 수정된 제목 → `204` → `{"detail":"Post 1 not found"}`. id가 1이 아니면(이전에 데이터가 있었다면) 그 id로 바꿔서 확인한다.

- [ ] **Step 13: README에 DB 섹션 추가**

```markdown
## DB (04단계부터)

```bash
docker compose up -d --wait      # PostgreSQL 16 (localhost:5433)
uv run alembic upgrade head      # 마이그레이션 적용 (= flyway migrate)
docker compose down              # 중지 (데이터 유지)
docker compose down -v           # 중지 + 데이터 삭제
```
```

- [ ] **Step 14: 학습 노트 `docs/learning/04-database.md` 작성**

반드시 포함할 내용:
- 맨 위: `git diff step-03 step-04 -- app/ tests/`
- **이번에 바뀐 것:** engine/SessionLocal/Session 관계, `Mapped`/`mapped_column`, `select()` 2.0 스타일, `db.get`, `add/commit/refresh/delete`, `Depends(get_db)`와 `Annotated` 별칭, `from_attributes`, Alembic autogenerate, 테스트 픽스처가 바뀌어도 테스트 본문은 그대로라는 점
- **Spring이라면?:** engine↔HikariDataSource, Session↔EntityManager(영속성 컨텍스트), `db.get`↔`em.find`, `db.add`↔`em.persist`, `setattr` 후 commit↔더티 체킹, `commit()` 직접 호출↔`@Transactional`이 해주던 일, Alembic↔Flyway(차이: autogenerate가 모델과 DB를 비교해 마이그레이션을 '만들어' 준다), `dependency_overrides`↔`@MockBean`
- **디버깅 포인트:** `get_db` 실행 순서를 01단계 `get_session_like`와 나란히 비교, `psycopg.OperationalError: connection ... failed`→DB 컨테이너 상태(`docker compose ps`)·포트 확인, `relation "posts" does not exist`→`alembic upgrade head` 누락, SQL 로그 보는 법(`create_engine(..., echo=True)`로 바꿔 보기)
- **직접 해볼 것:** `echo=True`로 바꾸고 POST 한 번에 어떤 SQL이 나가는지 서버 로그로 확인 / `db.commit()`을 지우고 POST 후 GET하면 어떻게 되는지 확인(07단계 예고) / `docker compose exec db psql -U board -d board`로 직접 `select * from posts;`

- [ ] **Step 15: 린트 + 커밋 + 태그**

```bash
uv run ruff check --fix . && uv run ruff format . && uv run ruff check . && uv run pytest -q
git add -A
git commit -m "feat: PostgreSQL, SQLAlchemy, Alembic으로 저장소 전환 (step-04)

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
git tag step-04
```

---

### Task 5: step-05 레이어 분리 + 설정 + 전역 예외 핸들러

**Files:**
- Create: `app/core/__init__.py`, `app/core/config.py`, `app/core/database.py`, `app/core/exceptions.py`, `app/posts/__init__.py`, `app/posts/schemas.py`, `app/posts/models.py`, `app/posts/repository.py`, `app/posts/service.py`, `app/posts/router.py`, `.env.example`, `docs/learning/05-layers.md`
- Delete: `app/database.py`, `app/models.py`
- Modify: `app/main.py`, `alembic/env.py`(import 경로), `tests/test_posts.py`(import 2줄 + URL 출처만)

**Interfaces:**
- Consumes: Task 4의 Post 모델, 스키마, 테스트
- Produces (Task 6~8이 사용):
  - `app.core.config.settings: Settings` — `database_url: str`, `test_database_url: str`
  - `app.core.database`: `engine`, `SessionLocal`, `Base`, `get_db() -> Iterator[Session]`, `DbSession = Annotated[Session, Depends(get_db)]`
  - `app.core.exceptions`: `class NotFoundError(Exception)`, `register_exception_handlers(app: FastAPI) -> None`
  - `app.posts.models.Post`
  - `app.posts.schemas`: `PostCreate`, `PostUpdate`, `PostResponse`, `PostListResponse`
  - `app.posts.repository.PostRepository(session)`: `save(post) -> Post`, `find_by_id(post_id) -> Post | None`, `find_page(offset, limit) -> list[Post]`, `count() -> int`, `delete(post) -> None`
  - `app.posts.service.PostNotFoundError(post_id)`, `PostService(session)`: `create(data) -> Post`, `get(post_id) -> Post`, `get_page(page, size) -> tuple[list[Post], int]`, `update(post_id, data) -> Post`, `delete(post_id) -> None`
  - `app.posts.router.router: APIRouter`, `get_post_service(db) -> PostService`

리팩터링 단계이므로 **테스트 본문은 바꾸지 않는다.** 기존 테스트가 안전망이다.

- [ ] **Step 1: 기존 테스트가 통과하는 상태인지 확인**

Run: `uv run pytest -q`
Expected: 전부 PASS

- [ ] **Step 2: 의존성 설치 + 설정 작성**

```bash
uv add pydantic-settings
```

`app/core/__init__.py`, `app/posts/__init__.py`: 빈 파일.

`app/core/config.py`:
```python
"""애플리케이션 설정. Spring의 application.yml + @ConfigurationProperties에 해당한다.

우선순위: 환경 변수 > .env 파일 > 아래 기본값
필드 database_url은 환경 변수 DATABASE_URL과 매칭된다 (대소문자 무시).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://board:board@localhost:5433/board"
    test_database_url: str = "postgresql+psycopg://board:board@localhost:5433/board_test"


settings = Settings()
```

`.env.example`:
```
DATABASE_URL=postgresql+psycopg://board:board@localhost:5433/board
TEST_DATABASE_URL=postgresql+psycopg://board:board@localhost:5433/board_test
```

- [ ] **Step 3: `app/core/database.py` 작성** (`app/database.py` 내용 이동 + 설정 사용 + `DbSession` 이동)

```python
"""DB 연결과 세션 관리. Spring의 DataSource + EntityManager 설정에 해당한다."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# engine = 커넥션 풀 (HikariDataSource)
engine = create_engine(settings.database_url)

# expire_on_commit=False: commit 후에도 객체 속성을 다시 조회하지 않고 그대로 쓴다
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """모든 ORM 모델의 부모. Base.metadata에 테이블 정의가 모인다."""


def get_db() -> Iterator[Session]:
    # 요청 하나당 세션 하나. yield 앞은 요청 전, 뒤는 응답 후에 실행된다
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]
```

- [ ] **Step 4: `app/core/exceptions.py` 작성**

```python
"""전역 예외 처리. Spring의 @RestControllerAdvice + @ExceptionHandler에 해당한다."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class NotFoundError(Exception):
    """'대상이 없음' 계열 도메인 예외의 부모. 핸들러가 404로 바꾼다."""


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    def handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        # 서비스는 HTTP를 모르고 도메인 예외만 던진다. HTTP 변환은 여기서 한다
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})
```

- [ ] **Step 5: `app/posts/models.py`, `app/posts/schemas.py` 작성**

`app/posts/models.py`: Task 4의 `app/models.py`와 동일하되 import만 `from app.core.database import Base`로 바꾼다. 전체:
```python
"""게시글 ORM 모델. JPA의 @Entity에 해당한다."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

`app/posts/schemas.py`:
```python
"""게시글 요청/응답 DTO."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PostCreate(BaseModel):
    # str_strip_whitespace: 앞뒤 공백 제거 → "   "는 ""가 되어 min_length에서 걸린다
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=50)


class PostUpdate(BaseModel):
    # author는 수정 불가라 필드가 없다. 정의되지 않은 필드는 조용히 무시된다
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1)

    @field_validator("title", "content")
    @classmethod
    def reject_explicit_null(cls, value: str | None) -> str:
        # 필드를 '안 보낸' 경우엔 실행되지 않고, null을 '직접 보낸' 경우에만 실행된다
        if value is None:
            raise ValueError("null로 수정할 수 없습니다")
        return value


class PostResponse(BaseModel):
    # from_attributes: ORM 객체의 속성(post.title)에서 값을 읽을 수 있게 한다
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    author: str
    created_at: datetime
    updated_at: datetime


class PostListResponse(BaseModel):
    items: list[PostResponse]
    total: int
    page: int
    size: int
```

- [ ] **Step 6: `app/posts/repository.py` 작성**

```python
"""게시글 DB 접근. Spring Data의 Repository에 해당한다.

쿼리만 담당하고 commit은 하지 않는다. 트랜잭션 경계는 서비스가 정한다.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.posts.models import Post


class PostRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, post: Post) -> Post:
        self.session.add(post)
        self.session.flush()  # INSERT를 지금 보내서 id를 받는다 (commit은 아님)
        return post

    def find_by_id(self, post_id: int) -> Post | None:
        return self.session.get(Post, post_id)

    def find_page(self, offset: int, limit: int) -> list[Post]:
        stmt = (
            select(Post)
            .order_by(Post.created_at.desc(), Post.id.desc())  # 같은 시각이면 id로 결정
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def count(self) -> int:
        return self.session.scalar(select(func.count()).select_from(Post)) or 0

    def delete(self, post: Post) -> None:
        self.session.delete(post)
```

- [ ] **Step 7: `app/posts/service.py` 작성**

```python
"""게시글 비즈니스 로직. Spring의 @Service에 해당한다.

@Transactional이 없으므로 변경 작업은 여기서 직접 commit 한다.
"""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.posts.models import Post
from app.posts.repository import PostRepository
from app.posts.schemas import PostCreate, PostUpdate


class PostNotFoundError(NotFoundError):
    def __init__(self, post_id: int) -> None:
        super().__init__(f"Post {post_id} not found")
        self.post_id = post_id


class PostService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = PostRepository(session)

    def create(self, data: PostCreate) -> Post:
        post = self.repository.save(Post(**data.model_dump()))
        self.session.commit()
        self.session.refresh(post)  # DB가 채운 created_at 등을 다시 읽는다
        return post

    def get(self, post_id: int) -> Post:
        post = self.repository.find_by_id(post_id)
        if post is None:
            raise PostNotFoundError(post_id)
        return post

    def get_page(self, page: int, size: int) -> tuple[list[Post], int]:
        posts = self.repository.find_page(offset=(page - 1) * size, limit=size)
        return posts, self.repository.count()

    def update(self, post_id: int, data: PostUpdate) -> Post:
        post = self.get(post_id)
        # exclude_unset=True: 클라이언트가 실제로 보낸 필드만 반영한다
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(post, field, value)
        self.session.commit()
        self.session.refresh(post)
        return post

    def delete(self, post_id: int) -> None:
        post = self.get(post_id)
        self.repository.delete(post)
        self.session.commit()
```

- [ ] **Step 8: `app/posts/router.py` 작성**

```python
"""게시글 API. Spring의 @RestController에 해당한다.

HTTP 입출력만 담당하고 로직은 서비스에 맡긴다.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import DbSession
from app.posts.models import Post
from app.posts.schemas import PostCreate, PostListResponse, PostResponse, PostUpdate
from app.posts.service import PostService

router = APIRouter(prefix="/posts", tags=["posts"])  # @RequestMapping("/posts")


def get_post_service(db: DbSession) -> PostService:
    # 의존성 체인: 엔드포인트 → get_post_service → get_db
    # Spring이 생성자 주입으로 해주던 일을 함수로 명시한다
    return PostService(db)


PostServiceDep = Annotated[PostService, Depends(get_post_service)]


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, service: PostServiceDep) -> Post:
    return service.create(payload)


@router.get("", response_model=PostListResponse)
def list_posts(
    service: PostServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> PostListResponse:
    posts, total = service.get_page(page, size)
    return PostListResponse(
        items=[PostResponse.model_validate(post) for post in posts],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int, service: PostServiceDep) -> Post:
    return service.get(post_id)


@router.patch("/{post_id}", response_model=PostResponse)
def update_post(post_id: int, payload: PostUpdate, service: PostServiceDep) -> Post:
    return service.update(post_id, payload)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, service: PostServiceDep) -> None:
    service.delete(post_id)
```

- [ ] **Step 9: `app/main.py` 교체 + 옛 파일 삭제**

```python
"""애플리케이션 진입점. 라우터와 예외 핸들러를 조립한다."""

from fastapi import FastAPI

from app.core.exceptions import register_exception_handlers
from app.posts.router import router as posts_router

app = FastAPI(title="Board API")
register_exception_handlers(app)
app.include_router(posts_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

```bash
git rm app/database.py app/models.py
```

- [ ] **Step 10: alembic/env.py와 테스트의 import 경로 수정**

`alembic/env.py`의 두 import 줄을 교체:
```python
from app.core.config import settings
from app.core.database import Base
from app.posts import models  # noqa: F401  모델을 import해야 Base.metadata에 테이블이 등록된다
```
그리고 `config.set_main_option("sqlalchemy.url", DATABASE_URL)`를 `config.set_main_option("sqlalchemy.url", settings.database_url)`로 바꾼다.

`tests/test_posts.py` 상단에서 `import os`와 `TEST_DATABASE_URL = os.getenv(...)` 블록을 지우고 import를 다음으로 바꾼다:
```python
from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

test_engine = create_engine(settings.test_database_url)
```
테스트 함수 본문은 그대로 둔다.

- [ ] **Step 11: 테스트 + 마이그레이션 일치 확인**

```bash
uv run pytest -q
uv run alembic check
```
Expected: 테스트 전부 PASS. `alembic check` → `No new upgrade operations detected.` (모델 이동 후에도 스키마 변화 없음)

- [ ] **Step 12: 서버로 404 핸들러 확인**

```bash
uv run fastapi dev app/main.py --port 8000 > server.log 2>&1 &
sleep 4
curl -s localhost:8000/posts/999999
curl -s localhost:8000/openapi.json | python3 -c "import json,sys; print(sorted(json.load(sys.stdin)['paths']))"
kill %1
```
Expected: `{"detail":"Post 999999 not found"}`, `['/health', '/posts', '/posts/{post_id}']`

- [ ] **Step 13: 학습 노트 `docs/learning/05-layers.md` 작성**

반드시 포함할 내용:
- 맨 위: `git diff step-04 step-05 --stat`, `git diff step-04 step-05 -- tests/` (테스트 본문이 안 바뀐 것 강조)
- **이번에 바뀐 것:** 패키지 구조와 각 파일 책임, `APIRouter(prefix)` + `include_router`, `Depends` 체인, 도메인 예외 → 핸들러 → 404, `Settings`, `__init__.py`의 의미, `.env` / `.env.example`
- **Spring이라면?:** router↔`@RestController`, service↔`@Service`, repository↔`JpaRepository`, `Depends(get_post_service)`↔생성자 주입(차이: 싱글톤 빈이 아니라 **요청마다** 새로 만든다), `register_exception_handlers`↔`@RestControllerAdvice`, `Settings`↔`@ConfigurationProperties`, `include_router`↔컴포넌트 스캔(차이: 자동 스캔이 없어 직접 등록해야 한다)
- **디버깅 포인트:** 요청 하나가 거치는 파일/함수 순서를 스펙 7절 흐름도와 함께 적기, 순환 import 에러(`ImportError: cannot import name ... (most likely due to a circular import)`) 읽는 법, 라우터 등록 누락 시 404 `{"detail":"Not Found"}`(우리 핸들러의 404와 메시지가 다름에 주목), 설정값 확인은 `uv run python -c "from app.core.config import settings; print(settings)"`
- **직접 해볼 것:** `app.include_router(posts_router)`를 주석 처리하고 테스트 결과 보기 / `.env`를 만들어 `DATABASE_URL`을 틀린 포트로 바꾸고 서버 기동 후 에러 읽기(끝나면 `.env` 삭제) / `PostNotFoundError`를 `NotFoundError`가 아닌 `Exception`을 상속하게 바꾸면 응답이 어떻게 되는지

- [ ] **Step 14: 린트 + 커밋 + 태그**

```bash
uv run ruff check --fix . && uv run ruff format . && uv run ruff check . && uv run pytest -q
git add -A
git commit -m "refactor: router/service/repository 레이어 분리와 설정, 전역 예외 핸들러 도입 (step-05)

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
git tag step-05
```

---

### Task 6: step-06 테스트 고도화 (conftest + SAVEPOINT 롤백)

**Files:**
- Create: `tests/conftest.py`, `tests/test_post_repository.py`, `docs/learning/06-tests.md`
- Modify: `tests/test_posts.py` (상단 픽스처/엔진 코드 삭제, 테스트 본문 유지)

**Interfaces:**
- Consumes: `settings.test_database_url`, `Base`, `get_db`, `app`, `PostRepository`, `Post`
- Produces (Task 7, 8이 사용): 픽스처 `engine`(session 스코프), `db_session: Session`, `client: TestClient`

- [ ] **Step 1: `tests/conftest.py` 작성**

```python
"""pytest 공용 픽스처. 같은 폴더의 테스트 파일들이 import 없이 자동으로 쓴다.

격리 전략 (Spring 테스트의 @Transactional 롤백과 같은 효과):
1. 테스트 세션 전체에서 테이블은 한 번만 만든다.
2. 테스트마다 커넥션에서 바깥 트랜잭션을 열고, 끝나면 롤백한다.
3. 서비스가 commit()을 불러도 SAVEPOINT만 확정되므로 바깥 트랜잭션은 롤백할 수 있다.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.posts import models  # noqa: F401  Base.metadata에 posts 테이블 등록


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    engine = create_engine(settings.test_database_url)
    Base.metadata.drop_all(engine)  # 이전 실행이 비정상 종료됐을 때를 대비
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Iterator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        autoflush=False,
        expire_on_commit=False,
    )
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()  # 테스트가 만든 데이터를 전부 되돌린다
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

- [ ] **Step 2: `tests/test_posts.py`에서 로컬 픽스처 제거**

파일 상단을 아래 import만 남기고, 기존 `test_engine`, `TestingSessionLocal`, `client` 픽스처와 관련 import(`Iterator`, `pytest` 외 `create_engine`, `sessionmaker`, `settings`, `Base`, `get_db`, `app`)를 삭제한다. `pytest`는 `parametrize`에 쓰이므로 남긴다:
```python
import pytest
from fastapi.testclient import TestClient
```
`create_post` 헬퍼와 테스트 함수 본문은 그대로 둔다.

- [ ] **Step 3: 기존 테스트가 새 픽스처로 통과하는지 확인**

Run: `uv run pytest tests/test_posts.py -v`
Expected: 전부 PASS. 특히 `test_list_posts_newest_first_with_pagination`이 통과해야 한다 — 이제 모든 INSERT가 한 트랜잭션 안이라 `created_at`이 같고, `id.desc()` 보조 정렬 덕분에 순서가 맞는다.

- [ ] **Step 4: repository 테스트 작성** — `tests/test_post_repository.py`

```python
from sqlalchemy.orm import Session

from app.posts.models import Post
from app.posts.repository import PostRepository


def make_post(title: str) -> Post:
    return Post(title=title, content="내용", author="홍길동")


def test_save_assigns_id(db_session: Session):
    repository = PostRepository(db_session)

    post = repository.save(make_post("제목"))

    assert post.id is not None
    assert repository.find_by_id(post.id) is post  # 같은 세션 = 같은 객체 (1차 캐시)


def test_find_page_orders_newest_first_even_with_same_created_at(db_session: Session):
    repository = PostRepository(db_session)
    for title in ["t0", "t1", "t2"]:
        repository.save(make_post(title))

    posts = repository.find_page(offset=0, limit=10)

    # 한 트랜잭션 안의 now()는 같은 값이므로 id 내림차순이 순서를 결정한다
    assert len({post.created_at for post in posts}) == 1
    assert [post.title for post in posts] == ["t2", "t1", "t0"]
    assert repository.count() == 3


def test_each_test_starts_with_empty_table(db_session: Session):
    # 다른 테스트가 만든 데이터가 롤백되었는지 확인 (실행 순서와 무관하게 0이어야 한다)
    assert PostRepository(db_session).count() == 0
```

- [ ] **Step 5: 전체 테스트 + 격리 확인**

```bash
uv run pytest -q
uv run pytest -q   # 두 번째 실행: 이전 실행의 데이터가 남아 있지 않아야 한다
docker compose exec db psql -U board -d board_test -c '\dt'
```
Expected: 전부 PASS (두 번 실행해도 결과 동일). 마지막 명령은 `Did not find any relations.` (세션 종료 시 drop_all)

- [ ] **Step 6: 학습 노트 `docs/learning/06-tests.md` 작성**

반드시 포함할 내용:
- 맨 위: `git diff step-05 step-06 -- tests/`
- **이번에 바뀐 것:** `conftest.py`의 자동 주입, 픽스처 스코프(`session` vs 기본 `function`), 픽스처 간 의존(`client`→`db_session`→`engine`), 픽스처의 yield(01단계 generators와 같은 원리), SAVEPOINT 격리, `dependency_overrides`
- **Spring이라면?:** 픽스처↔`@BeforeEach`/`@AfterEach`를 하나로 합친 것 + 파라미터 주입, `scope="session"`↔`@BeforeAll`/Spring 테스트 컨텍스트 캐싱, 롤백 격리↔테스트의 `@Transactional`, `conftest.py`↔공통 테스트 설정 클래스, `parametrize`↔`@ParameterizedTest`
- **디버깅 포인트:** `fixture 'xxx' not found`의 의미, 픽스처 실행 순서 보기 `uv run pytest --setup-show tests/test_post_repository.py`, 실패 시 `-x -vv`, 특정 테스트만 `-k 이름`, `print`를 보려면 `-s`; **주의:** 테스트가 서비스와 같은 세션을 공유하므로 `commit()` 누락 버그를 이 테스트들은 못 잡는다는 한계(07단계 실습 1번과 연결)
- **직접 해볼 것:** `--setup-show`로 픽스처 생성/정리 순서 관찰 / `join_transaction_mode="create_savepoint"`를 지우고 테스트를 두 번 돌려 무엇이 깨지는지 확인(끝나면 원복, `docker compose exec db psql -U board -d board_test -c 'drop table if exists posts'`로 정리)

- [ ] **Step 7: 린트 + 커밋 + 태그**

```bash
uv run ruff check --fix . && uv run ruff format . && uv run ruff check . && uv run pytest -q
git add -A
git commit -m "test: conftest 픽스처와 SAVEPOINT 롤백 격리 도입, repository 테스트 추가 (step-06)

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
git tag step-06
```

---

### Task 7: step-07 디버깅 (VS Code 디버거, 로깅, 버그 실습)

**Files:**
- Create: `.vscode/launch.json`, `app/core/logging.py`, `docs/learning/07-debugging.md`
- Modify: `app/core/config.py`(`log_level` 추가), `.env.example`, `app/main.py`(로깅 초기화), `app/posts/service.py`(로그 추가), `tests/test_posts.py`(로그 테스트 1개 추가)

**Interfaces:**
- Consumes: Task 5 서비스, Task 6 `client` 픽스처
- Produces: `app.core.logging.setup_logging(level: str) -> None`, `settings.log_level: str`(기본 `"INFO"`), 로거 이름 `app.posts.service`, 로그 메시지 `"게시글 생성 id=%s"`, `"게시글 수정 id=%s fields=%s"`, `"게시글 삭제 id=%s"`

- [ ] **Step 1: 실패하는 로그 테스트 추가** — `tests/test_posts.py` 맨 아래

```python
# --- 로깅 ---


def test_create_post_writes_info_log(client, caplog):
    with caplog.at_level("INFO", logger="app.posts.service"):
        created = create_post(client)

    assert f"게시글 생성 id={created['id']}" in caplog.text
```

Run: `uv run pytest tests/test_posts.py::test_create_post_writes_info_log -v`
Expected: FAIL — `AssertionError` (로그 없음)

- [ ] **Step 2: 로깅 설정 구현**

`app/core/config.py`의 `Settings`에 필드 추가:
```python
    log_level: str = "INFO"
```
`.env.example`에 `LOG_LEVEL=INFO` 줄 추가.

`app/core/logging.py`:
```python
"""로깅 설정. Spring의 logback 설정 + logging.level에 해당한다."""

import logging


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        # 어느 파일 몇 번째 줄에서 찍힌 로그인지 보이게 한다 (디버깅에 가장 유용)
        format="%(asctime)s %(levelname)-5s [%(name)s] %(filename)s:%(lineno)d - %(message)s",
    )
```

`app/main.py`에 추가 (app 생성 전):
```python
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging(settings.log_level)
```

`app/posts/service.py`: 상단에 `import logging`과 `logger = logging.getLogger(__name__)`(= `"app.posts.service"`, SLF4J의 `LoggerFactory.getLogger(getClass())`) 추가. 그리고:
- `create`의 `return post` 직전: `logger.info("게시글 생성 id=%s", post.id)`
- `update`의 `for` 문 직전에 `changes = data.model_dump(exclude_unset=True)`로 꺼내고 `for field, value in changes.items():`로 바꾼 뒤, `return post` 직전: `logger.info("게시글 수정 id=%s fields=%s", post.id, sorted(changes))`
- `delete`의 `commit()` 뒤: `logger.info("게시글 삭제 id=%s", post_id)`

로그 메시지에 f-string 대신 `%s` 인자를 쓴다 (SLF4J의 `{}` 플레이스홀더와 같은 이유).

- [ ] **Step 3: 테스트 통과 확인**

Run: `uv run pytest -q`
Expected: 전부 PASS

- [ ] **Step 4: `.vscode/launch.json` 작성**

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI: 서버 디버그",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--port", "8000"],
      "envFile": "${workspaceFolder}/.env",
      "justMyCode": true
    },
    {
      "name": "Pytest: 현재 파일 디버그",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-x", "-vv"],
      "justMyCode": true
    }
  ]
}
```

검증: `python3 -c "import json; json.load(open('.vscode/launch.json'))"` 에러 없음. (`.env`가 없어도 debugpy는 경고만 하고 실행된다 — 학습 노트에 명시)

- [ ] **Step 5: 버그 시나리오 재현 및 실제 출력 수집**

각 시나리오마다: 코드 수정 → 재현 명령 실행 → **실제 출력의 핵심 줄**을 기록 → `git checkout -- app/` 로 원복 → `git status`가 깨끗한지 확인. 서버가 필요한 시나리오는 `uv run fastapi dev app/main.py --port 8000 > server.log 2>&1 &`로 띄우고 `server.log`에서 트레이스백을 읽는다 (DB는 `board` 사용).

| # | 수정 | 재현 | 예상 증상 |
|---|---|---|---|
| 1 | `service.create`에서 `self.session.commit()` 삭제 | 서버: POST 후 응답의 id로 GET | POST는 201 + id, GET은 404. `uv run pytest -q`는 **통과** (같은 세션 공유) |
| 2 | `schemas.PostResponse`에서 `model_config = ...` 줄 삭제 | 서버: POST 1개 후 `GET /posts` | 500, 로그에 `pydantic_core._pydantic_core.ValidationError` … `PostResponse` … `Input should be a valid dictionary or instance of PostResponse` (단건 GET은 FastAPI가 from_attributes로 직렬화하므로 정상일 수 있음 — 실제 결과를 기록) |
| 3 | `schemas.PostCreate.author`를 `author: int` 로 변경 | `curl -X POST ... -d '{"title":"t","content":"c","author":"홍길동"}'` | 422, `loc: ["body","author"]`, `type: "int_parsing"` |
| 4 | `service.get`에서 `if post is None: raise ...` 두 줄 삭제 | `curl -X PATCH localhost:8000/posts/999999 -d '{"title":"x"}' -H 'Content-Type: application/json'` | 500, 로그 마지막 줄 `AttributeError: 'NoneType' object has no attribute 'title'`, 바로 위 줄이 `service.py`의 `setattr` |
| 5 | `service.update`에서 `exclude_unset=True` 삭제 | `uv run pytest tests/test_posts.py::test_update_post_partially -x` | 실패. 원인 예외 `psycopg.errors.NotNullViolation` (content가 None으로 덮어써짐) → `sqlalchemy.exc.IntegrityError` |

예상과 다르게 나오면 실제 결과를 기준으로 문서를 쓰고, 차이를 학습 노트에 "예상과 달랐던 점"으로 남긴다.

- [ ] **Step 6: 학습 노트 `docs/learning/07-debugging.md` 작성**

반드시 포함할 내용:
- 맨 위: `git diff step-06 step-07`
- **이번에 바뀐 것:** launch.json 두 설정, 로깅 포맷, `settings.log_level`
- **Spring이라면?:** debugpy↔JDWP 원격 디버깅, `logging.getLogger(__name__)`↔`LoggerFactory.getLogger(getClass())`, `%s`↔`{}`, `LOG_LEVEL`↔`logging.level.root`
- **디버깅 포인트 — 트레이스백 읽는 법:** Java 스택 트레이스와 순서가 **반대**(Python은 맨 아래가 예외, 위로 갈수록 호출자) / 내 코드(`app/...`) 줄만 먼저 찾기 / `The above exception was the direct cause` 와 `During handling of the above exception, another exception occurred`의 차이 / 422는 트레이스백이 없고 응답 본문을 본다
- **디버거 사용법:** F5로 "FastAPI: 서버 디버그" 실행 → `service.py`의 `create`에 브레이크포인트 → `/docs`에서 POST → 변수 패널에서 `data`, `post` 확인, 호출 스택 패널에서 router → service 흐름 확인 / 조건부 브레이크포인트(`post_id == 999`) / 코드에 `breakpoint()` 한 줄 넣고 `uv run pytest -s`로 pdb 진입(`n`, `s`, `p 변수`, `c`, `q`) / "Pytest: 현재 파일 디버그"로 실패 테스트에서 멈추기
- **버그 실습 5개:** Step 5 표의 각 시나리오를 `### 실습 N: 제목` / 바꿀 코드(diff 형태) / 재현 명령 / 실제 출력(Step 5에서 수집한 핵심 줄) / 읽는 법 / 원인 / 실무 AI 코드에서 이 버그가 보이는 모양 순서로 작성. 1번에는 "테스트가 통과해도 버그가 있을 수 있다 — 테스트가 서비스와 세션을 공유하기 때문"이라는 설명 포함
- **직접 해볼 것:** 각 실습을 직접 재현 후 `git checkout -- app/`로 원복

- [ ] **Step 7: 린트 + 커밋 + 태그**

```bash
git status --short   # app/ 아래에 실습용 수정이 남아 있지 않은지 확인
uv run ruff check --fix . && uv run ruff format . && uv run ruff check . && uv run pytest -q
git add -A
git commit -m "feat: VS Code 디버거 설정, 로깅, 디버깅 실습 문서 추가 (step-07)

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
git tag step-07
```

---

### Task 8: step-08 async 전환

**Files:**
- Modify: `app/core/database.py`, `app/posts/repository.py`, `app/posts/service.py`, `app/posts/router.py`, `tests/conftest.py`, `tests/test_posts.py`, `tests/test_post_repository.py`, `pyproject.toml`
- Create: `docs/learning/08-async.md`
- 변경 없음 확인: `alembic/env.py`(동기 psycopg로 그대로 동작), `app/core/exceptions.py`, `app/posts/schemas.py`, `app/posts/models.py`, `tests/test_health.py`

**Interfaces:**
- Consumes: Task 7까지의 전체
- Produces: `get_db() -> AsyncIterator[AsyncSession]`, `DbSession = Annotated[AsyncSession, Depends(get_db)]`, repository/service의 DB 접근 메서드가 모두 `async def`(단 `PostRepository.save`는 `async`, 메서드 이름/인자는 Task 5와 동일), 픽스처 `db_session: AsyncSession`, `client: httpx.AsyncClient`

- [ ] **Step 1: 의존성 + pytest 설정**

```bash
uv add --dev pytest-asyncio
```
`pyproject.toml`의 `[tool.pytest.ini_options]`에 추가:
```toml
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```
(psycopg 3는 이미 async를 지원하므로 드라이버 추가 설치는 없다. URL도 `postgresql+psycopg://` 그대로.)

- [ ] **Step 2: 테스트를 async로 먼저 전환** (실패하는 테스트)

`tests/conftest.py` 전체 교체:
```python
"""pytest 공용 픽스처 (async 버전).

격리 전략은 06단계와 같다. 테이블 생성/삭제는 동기 엔진으로 한 번만 하고,
테스트마다 async 커넥션에서 바깥 트랜잭션을 열고 롤백한다.
"""

from collections.abc import AsyncIterator, Iterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.posts import models  # noqa: F401  Base.metadata에 posts 테이블 등록


@pytest.fixture(scope="session")
def create_tables() -> Iterator[None]:
    engine = create_engine(settings.test_database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
async def db_session(create_tables: None) -> AsyncIterator[AsyncSession]:
    # 테스트마다 이벤트 루프가 새로 만들어지므로 엔진도 테스트마다 만든다
    engine = create_async_engine(settings.test_database_url, poolclass=NullPool)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            autoflush=False,
            expire_on_commit=False,
        )
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    # TestClient 대신 같은 이벤트 루프에서 도는 AsyncClient를 쓴다
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

`tests/test_posts.py` 전체 교체 (시나리오와 단언은 Task 3~7과 동일, `async`/`await`만 추가):
```python
import pytest
from httpx import AsyncClient


async def create_post(client: AsyncClient, **overrides: str) -> dict:
    payload = {"title": "제목", "content": "내용", "author": "홍길동"} | overrides
    response = await client.post("/posts", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# --- 생성 ---


async def test_create_post(client):
    response = await client.post(
        "/posts", json={"title": "첫 글", "content": "안녕", "author": "홍길동"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["title"] == "첫 글"
    assert body["content"] == "안녕"
    assert body["author"] == "홍길동"
    assert body["created_at"]
    assert body["updated_at"]


async def test_create_post_rejects_too_long_title(client):
    response = await client.post("/posts", json={"title": "a" * 101, "content": "c", "author": "a"})

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", "title"]
    assert error["type"] == "string_too_long"


async def test_create_post_rejects_blank_title(client):
    response = await client.post("/posts", json={"title": "   ", "content": "c", "author": "a"})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "title"]


async def test_create_post_requires_author(client):
    response = await client.post("/posts", json={"title": "t", "content": "c"})

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", "author"]
    assert error["type"] == "missing"


# --- 조회 ---


async def test_get_post(client):
    created = await create_post(client)

    response = await client.get(f"/posts/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


async def test_get_post_not_found(client):
    response = await client.get("/posts/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Post 999 not found"}


async def test_get_post_with_non_integer_id(client):
    response = await client.get("/posts/abc")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "post_id"]


# --- 목록 ---


async def test_list_posts_newest_first_with_pagination(client):
    for title in ["1", "2", "3"]:
        await create_post(client, title=title)

    first_page = (await client.get("/posts", params={"page": 1, "size": 2})).json()
    second_page = (await client.get("/posts", params={"page": 2, "size": 2})).json()

    assert [p["title"] for p in first_page["items"]] == ["3", "2"]
    assert first_page["total"] == 3
    assert first_page["page"] == 1
    assert first_page["size"] == 2
    assert [p["title"] for p in second_page["items"]] == ["1"]


async def test_list_posts_uses_default_paging(client):
    body = (await client.get("/posts")).json()

    assert body == {"items": [], "total": 0, "page": 1, "size": 10}


async def test_list_posts_page_beyond_last_returns_empty_items(client):
    await create_post(client)

    body = (await client.get("/posts", params={"page": 5})).json()

    assert body["items"] == []
    assert body["total"] == 1


@pytest.mark.parametrize("params", [{"page": 0}, {"size": 0}, {"size": 101}])
async def test_list_posts_rejects_invalid_paging(client, params):
    response = await client.get("/posts", params=params)

    assert response.status_code == 422


# --- 수정 ---


async def test_update_post_partially(client):
    created = await create_post(client, title="원래 제목", content="원래 내용")

    response = await client.patch(f"/posts/{created['id']}", json={"title": "새 제목"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "새 제목"
    assert body["content"] == "원래 내용"
    assert body["author"] == "홍길동"


async def test_update_post_rejects_explicit_null(client):
    created = await create_post(client)

    response = await client.patch(f"/posts/{created['id']}", json={"title": None})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "title"]


async def test_update_post_ignores_author(client):
    created = await create_post(client, author="홍길동")

    response = await client.patch(f"/posts/{created['id']}", json={"author": "임꺽정"})

    assert response.status_code == 200
    assert response.json()["author"] == "홍길동"


async def test_update_post_not_found(client):
    response = await client.patch("/posts/999", json={"title": "새 제목"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Post 999 not found"}


# --- 삭제 ---


async def test_delete_post(client):
    created = await create_post(client)

    response = await client.delete(f"/posts/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert (await client.get(f"/posts/{created['id']}")).status_code == 404


async def test_delete_post_not_found(client):
    response = await client.delete("/posts/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Post 999 not found"}


# --- 로깅 ---


async def test_create_post_writes_info_log(client, caplog):
    with caplog.at_level("INFO", logger="app.posts.service"):
        created = await create_post(client)

    assert f"게시글 생성 id={created['id']}" in caplog.text
```

`tests/test_post_repository.py` 전체 교체:
```python
from sqlalchemy.ext.asyncio import AsyncSession

from app.posts.models import Post
from app.posts.repository import PostRepository


def make_post(title: str) -> Post:
    return Post(title=title, content="내용", author="홍길동")


async def test_save_assigns_id(db_session: AsyncSession):
    repository = PostRepository(db_session)

    post = await repository.save(make_post("제목"))

    assert post.id is not None
    assert await repository.find_by_id(post.id) is post


async def test_find_page_orders_newest_first_even_with_same_created_at(db_session: AsyncSession):
    repository = PostRepository(db_session)
    for title in ["t0", "t1", "t2"]:
        await repository.save(make_post(title))
    db_session.expire_all()  # server_default로 채워진 created_at을 다시 읽게 한다

    posts = await repository.find_page(offset=0, limit=10)

    assert len({post.created_at for post in posts}) == 1
    assert [post.title for post in posts] == ["t2", "t1", "t0"]
    assert await repository.count() == 3


async def test_each_test_starts_with_empty_table(db_session: AsyncSession):
    assert await PostRepository(db_session).count() == 0
```

> 참고: `server_default`로 DB가 채운 `created_at`은 INSERT 후 '아직 안 읽은' 상태다. 동기 세션은 접근 시 알아서 SELECT하지만 async 세션은 암묵적 IO를 할 수 없어 `MissingGreenlet` 에러가 난다. `expire_all()` 후 `find_page`의 SELECT로 모든 속성을 명시적으로 다시 읽게 한다. 이 차이를 학습 노트에 적는다.

- [ ] **Step 3: 실패 확인**

Run: `uv run pytest -q`
Expected: 대부분 FAIL — 예: `TypeError: object Post can't be used in 'await' expression` 또는 동기 세션에 AsyncSession이 주입되어 `AttributeError`/`MissingGreenlet`. (`tests/basics`, `test_health.py`는 PASS)

- [ ] **Step 4: `app/core/database.py` async로 교체**

```python
"""DB 연결과 세션 관리 (async 버전)."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# psycopg 3는 같은 URL로 동기/비동기 모두 쓸 수 있다
engine = create_async_engine(settings.database_url)

# async에서는 expire_on_commit=False가 사실상 필수다
# (commit 후 속성 접근 시 암묵적 SELECT를 할 수 없기 때문)
SessionLocal = async_sessionmaker(engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """모든 ORM 모델의 부모. Base.metadata에 테이블 정의가 모인다."""


async def get_db() -> AsyncIterator[AsyncSession]:
    session = SessionLocal()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


DbSession = Annotated[AsyncSession, Depends(get_db)]
```

- [ ] **Step 5: `app/posts/repository.py` async로 교체**

```python
"""게시글 DB 접근 (async 버전).

DB와 통신하는 메서드는 모두 await가 필요하다. session.add()는 메모리 작업이라 동기다.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.posts.models import Post


class PostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, post: Post) -> Post:
        self.session.add(post)
        await self.session.flush()
        return post

    async def find_by_id(self, post_id: int) -> Post | None:
        return await self.session.get(Post, post_id)

    async def find_page(self, offset: int, limit: int) -> list[Post]:
        stmt = (
            select(Post)
            .order_by(Post.created_at.desc(), Post.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(await self.session.scalars(stmt))

    async def count(self) -> int:
        return await self.session.scalar(select(func.count()).select_from(Post)) or 0

    async def delete(self, post: Post) -> None:
        await self.session.delete(post)
```

- [ ] **Step 6: `app/posts/service.py` async로 교체**

```python
"""게시글 비즈니스 로직 (async 버전)."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.posts.models import Post
from app.posts.repository import PostRepository
from app.posts.schemas import PostCreate, PostUpdate

logger = logging.getLogger(__name__)


class PostNotFoundError(NotFoundError):
    def __init__(self, post_id: int) -> None:
        super().__init__(f"Post {post_id} not found")
        self.post_id = post_id


class PostService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = PostRepository(session)

    async def create(self, data: PostCreate) -> Post:
        post = await self.repository.save(Post(**data.model_dump()))
        await self.session.commit()
        await self.session.refresh(post)
        logger.info("게시글 생성 id=%s", post.id)
        return post

    async def get(self, post_id: int) -> Post:
        post = await self.repository.find_by_id(post_id)
        if post is None:
            raise PostNotFoundError(post_id)
        return post

    async def get_page(self, page: int, size: int) -> tuple[list[Post], int]:
        posts = await self.repository.find_page(offset=(page - 1) * size, limit=size)
        return posts, await self.repository.count()

    async def update(self, post_id: int, data: PostUpdate) -> Post:
        post = await self.get(post_id)
        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(post, field, value)
        await self.session.commit()
        await self.session.refresh(post)
        logger.info("게시글 수정 id=%s fields=%s", post.id, sorted(changes))
        return post

    async def delete(self, post_id: int) -> None:
        post = await self.get(post_id)
        await self.repository.delete(post)
        await self.session.commit()
        logger.info("게시글 삭제 id=%s", post_id)
```

- [ ] **Step 7: `app/posts/router.py` async로 교체**

```python
"""게시글 API (async 버전). 함수가 async def가 되고 서비스 호출에 await가 붙는다."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import DbSession
from app.posts.models import Post
from app.posts.schemas import PostCreate, PostListResponse, PostResponse, PostUpdate
from app.posts.service import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


def get_post_service(db: DbSession) -> PostService:
    # 객체를 만들기만 하고 IO가 없으므로 동기 함수로 둬도 된다
    return PostService(db)


PostServiceDep = Annotated[PostService, Depends(get_post_service)]


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(payload: PostCreate, service: PostServiceDep) -> Post:
    return await service.create(payload)


@router.get("", response_model=PostListResponse)
async def list_posts(
    service: PostServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> PostListResponse:
    posts, total = await service.get_page(page, size)
    return PostListResponse(
        items=[PostResponse.model_validate(post) for post in posts],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, service: PostServiceDep) -> Post:
    return await service.get(post_id)


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(post_id: int, payload: PostUpdate, service: PostServiceDep) -> Post:
    return await service.update(post_id, payload)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, service: PostServiceDep) -> None:
    await service.delete(post_id)
```

- [ ] **Step 8: 테스트 통과 확인**

Run: `uv run pytest -q`
Expected: 전부 PASS (Task 7과 테스트 개수 동일). `RuntimeWarning: coroutine ... was never awaited` 경고가 없어야 한다 — 있으면 `await` 누락이므로 고친다.

- [ ] **Step 9: 마이그레이션과 실제 서버 확인**

```bash
uv run alembic check
uv run fastapi dev app/main.py --port 8000 > server.log 2>&1 &
sleep 4
curl -s -X POST localhost:8000/posts -H 'Content-Type: application/json' \
  -d '{"title":"async 글","content":"내용","author":"홍길동"}'
curl -s "localhost:8000/posts?size=1"
curl -s localhost:8000/posts/999999
kill %1
grep -n "게시글 생성" server.log
```
Expected: `alembic check` → `No new upgrade operations detected.`, 201 본문, 목록 1건, 404 본문, 로그에 `게시글 생성 id=` 줄과 `service.py:<줄번호>`

- [ ] **Step 10: async 실수 시나리오 재현 및 실제 출력 수집** (Task 7 Step 5와 같은 방식, 끝나면 `git checkout -- app/`)

| # | 수정 | 재현 | 예상 증상 |
|---|---|---|---|
| 6 | `service.get`에서 `await self.repository.find_by_id(post_id)`의 `await` 삭제 | `uv run pytest tests/test_posts.py::test_get_post_not_found -x` | 실패 (404 대신 500 등). 경고 `RuntimeWarning: coroutine 'PostRepository.find_by_id' was never awaited`. coroutine 객체는 None이 아니라서 None 체크를 통과해 버린다 |
| 7 | `router.get_post` 맨 앞에 `import time; time.sleep(3)` 추가 | 서버에서 `GET /posts/1`과 `GET /health`를 동시에 호출 (`curl ... & curl ...`)하고 `time`으로 측정 | async def 안의 동기 sleep이 이벤트 루프 전체를 막아 `/health`도 약 3초 지연. `await asyncio.sleep(3)`으로 바꾸면 `/health`는 즉시 응답 |

- [ ] **Step 11: 학습 노트 `docs/learning/08-async.md` 작성**

반드시 포함할 내용:
- 맨 위: `git diff step-07 step-08 -- app/`
- **이번에 바뀐 것:** `async def`/`await`, `AsyncSession`, `create_async_engine`, async 픽스처와 `httpx.AsyncClient`, `expire_on_commit=False`가 필수가 된 이유, `expire_all()`이 필요했던 이유(`MissingGreenlet`)
- **Spring이라면?:** 동기 FastAPI(`def`)↔Spring MVC(요청마다 스레드풀 스레드), async FastAPI↔Spring WebFlux(이벤트 루프), `await`↔`Mono` 체인에서 값이 나올 때까지 기다리는 지점, 이벤트 루프 블로킹↔WebFlux에서 블로킹 JDBC 호출. FastAPI는 `def` 엔드포인트를 자동으로 스레드풀에서 돌리므로 **`def`는 안전하고 `async def` 안의 동기 IO가 위험**하다는 점 강조
- **드라이버 메모:** 실무 코드에서는 `postgresql+asyncpg://`를 자주 본다. 이 프로젝트는 psycopg 3가 동기/비동기를 모두 지원해 URL 하나로 Alembic(동기)과 앱(비동기)을 함께 쓰려고 psycopg를 유지했다. asyncpg로 바꾸면 URL 드라이버 부분과 Alembic env.py(async 템플릿)를 바꿔야 한다
- **디버깅 포인트:** AI가 만든 async 코드 체크리스트 — (1) DB 호출 앞에 `await`가 있는가 (2) `async def` 안에 `requests`, `time.sleep`, 동기 세션 같은 블로킹 호출이 없는가 (3) `MissingGreenlet`은 lazy loading/만료된 속성 접근 신호 (4) `coroutine ... was never awaited` 경고는 무조건 버그
- **버그 실습 2개:** Step 10 표의 6, 7번을 Task 7 노트와 같은 형식(바꿀 코드 / 재현 / 실제 출력 / 읽는 법 / 원인 / AI 코드에서의 모양)으로 작성
- **직접 해볼 것:** `git diff step-07 step-08 -- app/posts/service.py`를 보며 `await`가 붙은 줄과 안 붙은 줄(`session.add`, `setattr`)의 차이 설명해 보기

- [ ] **Step 12: 최종 검증 + 커밋 + 태그**

```bash
git status --short   # 실습용 수정이 남아 있지 않은지 확인
uv run ruff check --fix . && uv run ruff format . && uv run ruff check . && uv run ruff format --check . && uv run pytest -q
git add -A
git commit -m "feat: SQLAlchemy AsyncSession 기반 async 전환 (step-08)

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
git tag step-08
git tag   # step-00 ~ step-08 9개 확인
```

---

## Self-Review 결과

- **스펙 커버리지:** 2절(태그, 학습 노트 4섹션) → 모든 Task / 3절 스택 → Task 0,2,4,5,8 / 4절 API·필드 규칙 → Task 3 테스트 / 5절 구조 → Task 5 (+ `app/core/logging.py` 추가, Task 7) / 6절 로드맵 9단계 → Task 0~8 / 6절 07 실습 5개 + 08 실습 → Task 7 Step 5, Task 8 Step 10 / 7절 흐름·명시적 commit → Task 5 / 8절 에러 → Task 5 / 9절 테스트 전략 → Task 6, 8 / 10절 실행 명령 → README(Task 0,2,4) / 11절 완료 기준 → 각 Task 마지막 Step
- **타입 일관성:** `PostRepository.save/find_by_id/find_page/count/delete`, `PostService.create/get/get_page/update/delete`, `get_post_service`, `DbSession`, 픽스처 `engine/db_session/client`(Task 8에서 `engine` → `create_tables`로 이름 변경, 테스트는 `db_session`/`client`만 사용) 일치 확인
- **Review Focus:** 5개 모두 Task 3 또는 Task 6에 테스트로 존재
