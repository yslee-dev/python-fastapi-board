# 01. 파이썬 기초 — FastAPI 코드를 읽기 위한 최소한의 문법

```bash
git diff step-00 step-01 --stat
uv run pytest tests/basics -v      # 예제가 실제로 어떻게 동작하는지 테스트로 확인
```

**추천 읽기 순서:** 각 모듈(`basics/*.py`)과 짝이 되는 테스트(`tests/basics/test_*.py`)를 나란히 열어 두고 읽는다.

1. `type_hints.py` → 2. `collections_demo.py` → 3. `truthiness.py` → 4. `classes.py`
→ 5. `exceptions_demo.py` → 6. `decorators.py` → 7. `context_managers.py` → 8. `generators.py`

## 이번에 바뀐 것

| 모듈 | 한 줄 요약 |
|---|---|
| `type_hints.py` | 타입 힌트는 런타임에 강제되지 않는다. 하지만 FastAPI/Pydantic은 이 힌트를 읽어서 검증한다 |
| `collections_demo.py` | 리스트/딕셔너리 컴프리헨션, 슬라이싱, 언패킹(`*rest`, `**dict`) |
| `truthiness.py` | `None`, `0`, `""`, `[]`, `{}`는 모두 falsy. None 비교는 `is None` |
| `classes.py` | `self`, `__init__`, `__repr__`, `@dataclass`, 가변 기본값 함정 |
| `exceptions_demo.py` | 커스텀 예외, `raise ... from e`, `try/except/else` |
| `decorators.py` | `@x`는 `f = x(f)`와 같다. `@app.get("/path")`를 직접 흉내 낸 `MiniRouter` |
| `context_managers.py` | `with`, `@contextmanager`로 만든 미니 `@Transactional` |
| `generators.py` | `yield`로 멈췄다 다시 이어지는 함수. FastAPI `get_db()`와 같은 구조 |

## Spring이라면?

| Python | Java / Spring |
|---|---|
| `[n * n for n in xs if n % 2 == 0]` | `xs.stream().filter(...).map(...).toList()` |
| `{p["id"]: p for p in posts}` | `Collectors.toMap(...)` |
| `items[start:end]` | `list.subList(start, end)` (단, 범위를 넘어도 예외가 없다) |
| `str \| None` | `@Nullable String` / `Optional<String>` |
| `@dataclass` | Lombok `@Data` (또는 `record`) |
| `__repr__` | `toString()` |
| `self` | `this` (단, 메서드 첫 인자로 **명시적으로** 받는다) |
| `class X(Exception)` | `class X extends RuntimeException` (checked exception이 없다) |
| `raise X(...) from e` | `throw new X(msg, e)` |
| 데코레이터 | AOP `@Around` / `@GetMapping` 같은 어노테이션 기반 등록 |
| `with` 문 | try-with-resources |
| `@contextmanager` + `yield` | `@Transactional`이 내부에서 하는 일(시작 → 커밋/롤백 → 정리) |
| `yield` (제너레이터) | 직접 대응 없음. `Iterator`를 손으로 구현하는 것과 비슷하지만 함수 실행이 "일시정지"된다는 점이 다르다 |

**Java와 가장 다른 점 한 가지:** 어노테이션은 "메타데이터"라서 누군가(Spring)가 읽어야 의미가 생기지만,
데코레이터는 **그 자리에서 즉시 실행되는 함수 호출**이다. `@app.get("/health")`가 붙은 함수는
모듈이 import되는 순간 `app`에 등록된다.

## 디버깅 포인트

이 단계의 패턴이 앞으로 FastAPI 코드 어디에서 나오는지 미리 연결해 두자.

| 여기서 본 것 | 나중에 나오는 곳 |
|---|---|
| `MiniRouter.get(path)` 데코레이터 | 02단계 `@app.get("/health")`, 05단계 `@router.post("")` |
| `get_session_like()`의 `yield` + `finally` | 04단계 `get_db()` — 요청 전에 세션을 열고, 응답 후에 닫는다 |
| `transaction()` 컨텍스트 매니저 | 04단계 이후 `commit` / `rollback` / `close`의 순서 |
| `PostNotFoundError` | 05단계 서비스의 도메인 예외 → 404로 변환 |
| `str \| None`, `dict.get()` | `session.get(Post, id)`가 없으면 `None`을 돌려주는 것 |

AI가 만든 코드에서 자주 보이는 버그:

- **`if not post_id:`** — `0`도 falsy라서 id가 0이면 "없음"으로 취급된다. `if post_id is None:`이 맞다.
- **가변 기본값** — `def f(items=[])`는 호출할 때마다 같은 리스트를 공유한다 (`test_mutable_default_argument_is_shared`).
- **트레이스백의 "The above exception was the direct cause of the following exception"** — `raise ... from e`로 연결된 것이다. 아래쪽이 최종 예외, 위쪽이 원인이다.

## 직접 해볼 것

1. `basics/generators.py`의 `get_session_like`에 `print("open")`, `print("close")`를 넣고
   `uv run pytest tests/basics/test_generators.py -v -s`로 실행 순서를 관찰한다. (`-s`는 print 출력을 보여준다)
2. `basics/decorators.py`에서 `@functools.wraps(func)` 줄을 지우고 `uv run pytest tests/basics -q`를 실행한다.
   어떤 테스트가 깨지는지, 왜 깨지는지 설명해 본다. 끝나면 `git checkout -- basics/`로 되돌린다.
3. `uv run python`으로 대화형 셸을 열고 `[n * n for n in range(10) if n % 3 == 0]`처럼 직접 입력해 본다.
