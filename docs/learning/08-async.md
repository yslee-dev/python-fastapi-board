# 08. async 전환 — `async def`와 `await`가 실제로 바꾸는 것

```bash
git diff step-07 step-08 -- app/
git diff step-07 step-08 -- app/posts/service.py   # await가 붙은 줄과 안 붙은 줄을 비교
```

요즘 AI가 생성하는 FastAPI 코드는 대부분 이 단계의 모양이다. 기능은 07단계와 **완전히 같고**,
테스트 시나리오와 단언도 같다. 바뀐 것은 "DB를 기다리는 방식"뿐이다.

## 이번에 바뀐 것

| 위치 | 동기 (07단계) | async (08단계) |
|---|---|---|
| 엔진 | `create_engine(url)` | `create_async_engine(url)` |
| 세션 | `Session`, `sessionmaker` | `AsyncSession`, `async_sessionmaker` |
| `get_db` | `def` + `yield` | `async def` + `yield` |
| 엔드포인트 | `def create_post(...)` | `async def create_post(...)` |
| DB 호출 | `self.session.commit()` | `await self.session.commit()` |
| 테스트 클라이언트 | `TestClient` | `httpx.AsyncClient` + `ASGITransport` |
| 테스트 함수 | `def test_...` | `async def test_...` (pytest-asyncio가 실행) |

**`await`가 붙는 곳과 안 붙는 곳** (`service.py`, `repository.py`)

| `await` 있음 — DB와 통신 | `await` 없음 — 메모리 작업 |
|---|---|
| `await session.flush()` / `commit()` / `refresh()` | `session.add(post)` (세션에 등록만 함) |
| `await session.get(Post, id)` | `setattr(post, field, value)` |
| `await session.scalars(stmt)` / `scalar(...)` | `select(Post).order_by(...)` (쿼리 객체 조립만 함) |
| `await session.delete(post)` | `PostResponse.model_validate(post)` |

규칙: **네트워크/디스크를 기다리는 작업에만 `await`가 붙는다.** 그리고 `await`는 `async def` 안에서만 쓸 수 있으므로,
DB를 부르는 함수를 async로 바꾸면 **호출하는 쪽도 줄줄이 async가 된다** (repository → service → router).

**async에서 새로 생긴 제약**

- `expire_on_commit=False`가 사실상 필수다. 동기 세션은 만료된 속성에 접근하면 알아서 SELECT를 다시 하지만,
  async 세션은 그런 **암묵적 IO를 할 수 없다.** 대신 `MissingGreenlet` 에러가 난다.
- 그래서 `tests/test_post_repository.py`에서는 `db_session.expire_all()`로 만료시킨 뒤 `find_page`의 SELECT로 **명시적으로** 다시 읽는다.
- SQLAlchemy 2.1부터는 async를 쓰려면 `sqlalchemy[asyncio]`로 설치해야 한다 (`greenlet` 포함). 빠뜨리면
  `ImportError: The SQLAlchemy asyncio module requires that the Python 'greenlet' library is installed.`

## Spring이라면?

| FastAPI | Spring |
|---|---|
| `def` 엔드포인트 | Spring MVC — 요청마다 스레드풀의 스레드 하나가 끝까지 담당 |
| `async def` 엔드포인트 | Spring WebFlux — 이벤트 루프 스레드 몇 개가 모든 요청을 번갈아 처리 |
| `await x` | `Mono`/`Flux` 체인에서 결과가 나올 때까지 기다리는 지점 (단, 코드는 그냥 위에서 아래로 읽힌다) |
| `async def` 안의 `time.sleep()`, 동기 DB 호출 | WebFlux에서 블로킹 JDBC 호출 — 이벤트 루프 전체가 멈춘다 |

**중요:** FastAPI는 `def`로 만든 엔드포인트를 **자동으로 스레드풀에서 실행**한다. 그래서
- `def` 안의 블로킹 호출 → 안전하다 (Spring MVC처럼 동작)
- `async def` 안의 블로킹 호출 → **위험하다** (이벤트 루프를 막는다, 실습 7)

"async가 더 빠르다"가 아니라 "async는 기다리는 동안 다른 요청을 처리할 수 있다"이다. 대신 **기다리는 곳마다 정확히 `await`를 써야 한다.**

## 드라이버 메모: psycopg vs asyncpg

실무 코드에서는 `postgresql+asyncpg://...` URL을 자주 본다. 이 프로젝트는 **psycopg 3**를 유지했다.
psycopg 3는 동기/비동기를 모두 지원해서, URL 하나(`postgresql+psycopg://...`)로

- 앱은 `create_async_engine`(비동기)으로,
- Alembic(`alembic/env.py`)과 테스트의 테이블 생성은 `create_engine`(동기)으로

함께 쓸 수 있다. asyncpg로 바꾸려면 URL의 드라이버 부분을 바꾸고, Alembic `env.py`를 async 템플릿(`alembic init -t async`)으로 바꾸거나 동기용 URL을 따로 둬야 한다.

## 디버깅 포인트 — AI가 만든 async 코드 체크리스트

1. **DB 호출 앞에 `await`가 있는가?** 없으면 실습 6처럼 코루틴 객체가 그대로 흘러간다.
2. **`async def` 안에 블로킹 호출이 없는가?** `time.sleep`, `requests.get`, 동기 `Session`, 큰 파일 동기 읽기 등. 있으면 실습 7.
3. **`MissingGreenlet`** — async 세션에서 lazy loading이나 만료된 속성에 접근했다는 신호다. 관계는 `selectinload`로 미리 읽고, 속성은 `refresh`로 명시적으로 읽는다.
4. **`RuntimeWarning: coroutine '...' was never awaited`** — 이 경고는 **무조건 버그**다. 어디서 났는지 함수 이름이 메시지에 들어 있다.

---

## 버그 실습

**공통 방법:** 코드를 바꾸고 재현한 뒤 `git checkout -- app/`로 되돌린다.

### 실습 6: `await` 누락 — 코루틴 객체가 응답으로 흘러간다

**바꿀 코드** `app/posts/service.py`

```diff
     async def get(self, post_id: int) -> Post:
-        post = await self.repository.find_by_id(post_id)
+        post = self.repository.find_by_id(post_id)
         if post is None:
```

**재현:** `uv run pytest tests/test_posts.py::test_get_post_not_found -x -W default`

**실제 출력 (핵심 줄)**

```
E   fastapi.exceptions.ResponseValidationError: 1 validation error:
E     {'type': 'model_attributes_type', 'loc': ('response',),
E      'msg': 'Input should be a valid dictionary or object to extract fields from',
E      'input': <coroutine object PostRepository.find_by_id at 0x10a34c110>}
E     File ".../app/posts/router.py", line 43, in get_post
1 failed
sys:1: RuntimeWarning: coroutine 'PostRepository.find_by_id' was never awaited
```

**읽는 법:** `input`에 `<coroutine object ...>`가 보인다 → **값 대신 "아직 실행 안 된 작업"이 들어왔다.**
마지막 줄의 `RuntimeWarning`이 정확히 어떤 함수의 `await`를 빠뜨렸는지 알려 준다.

**원인:** `async def` 함수를 `await` 없이 부르면 실행되지 않고 **코루틴 객체**만 돌려준다. 이 객체는 `None`이 아니므로
`if post is None` 검사를 그냥 통과한다. 404가 나와야 할 요청이 500이 된다.
**타입 힌트(`-> Post | None`)는 이걸 막아 주지 않는다** — 01단계에서 본 "힌트는 런타임에 강제되지 않는다"가 여기서 다시 나온다.

### 실습 7: 이벤트 루프 블로킹 — 상관없는 API까지 느려진다

**바꿀 코드** `app/posts/router.py`

```diff
 async def get_post(post_id: int, service: PostServiceDep) -> Post:
+    import time
+
+    time.sleep(3)
     return await service.get(post_id)
```

**재현:** 서버를 띄우고, 느린 요청을 보낸 직후 `/health`의 응답 시간을 잰다.

```bash
curl -s -o /dev/null localhost:8000/posts/1 &
sleep 0.3
curl -s -o /dev/null -w "health: %{time_total}s\n" localhost:8000/health
```

**실제 출력**

```
time.sleep(3)          → health: 2.680517s     ← /health는 아무 잘못이 없는데 기다렸다
await asyncio.sleep(3) → health: 0.001472s     ← 기다리는 동안 다른 요청을 처리했다
```

**읽는 법:** 에러도 트레이스백도 없다. 증상은 **"서버 전체가 가끔 이유 없이 느려진다"**이다.
특정 API만 느린 게 아니라 **동시에 들어온 모든 요청이** 느려진다면 이벤트 루프 블로킹을 의심한다.

**원인:** async 서버는 이벤트 루프 하나가 모든 요청을 번갈아 처리한다. `time.sleep`은 루프 자체를 3초간 멈추게 해서
다른 요청이 끼어들 틈이 없다. `await asyncio.sleep`은 "3초 뒤에 깨워 줘"라고 루프에 양보한다.
**AI 코드에서 보이는 모양:** `async def` 엔드포인트 안에서 `requests.get(...)`(동기 HTTP 클라이언트)을 호출하는 코드. `httpx.AsyncClient`를 `await`로 써야 한다.
같은 함수를 `def`로 선언하면 FastAPI가 스레드풀에서 실행하므로 이 문제가 생기지 않는다.

## 직접 해볼 것

1. `git diff step-07 step-08 -- app/posts/service.py`를 보면서, `await`가 붙은 줄과 안 붙은 줄(`session.add`, `setattr`)이 왜 다른지 소리 내어 설명해 본다.
2. 실습 6, 7을 직접 재현하고 `git checkout -- app/`로 되돌린다.
3. 실습 7에서 `async def get_post`를 `def get_post`로 바꾸면(내부의 `await`도 제거해야 하므로 서비스 호출은 지금 구조에선 불가능하다)
   왜 이 프로젝트에서는 그렇게 할 수 없는지 생각해 본다. (힌트: 서비스가 async라서 호출하려면 `await`가 필요하다 → async는 위로 전염된다)
