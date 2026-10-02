# 06. 테스트 고도화 — conftest와 롤백 격리

```bash
git diff step-05 step-06 -- tests/
uv run pytest -v
```

04단계에서는 테스트마다 테이블을 **만들고 지웠다** (느리고, 실제 프로젝트에서는 테이블이 수십 개라 감당이 안 된다).
이번 단계에서는 테이블을 한 번만 만들고, 테스트마다 **트랜잭션을 롤백**해서 깨끗한 상태를 만든다.

## 이번에 바뀐 것

- **`tests/conftest.py`** — 여기에 정의한 픽스처는 같은 폴더(와 하위 폴더)의 모든 테스트에서 **import 없이** 쓸 수 있다.
- **픽스처 3개와 의존 관계**

  ```
  client  ──의존──▶  db_session  ──의존──▶  engine
  (테스트마다)        (테스트마다)            (테스트 세션 전체에서 한 번)
  ```

- **`scope="session"`** — `engine` 픽스처는 pytest 실행 전체에서 한 번만 만들어진다. 기본값은 `function`(테스트마다).
- **픽스처의 `yield`** — 01단계 `get_session_like`와 같다. `yield` 앞은 준비, 뒤는 정리다.
- **바깥 트랜잭션 롤백** — 세션이 이미 트랜잭션이 열린 커넥션에 붙어 있으면, 서비스가 `commit()`을 불러도
  바깥 트랜잭션은 커밋되지 않는다 (세션이 그 트랜잭션의 주인이 아니기 때문). 그래서 테스트가 끝나면 통째로 롤백할 수 있다.
- **`join_transaction_mode="create_savepoint"`** — 세션의 작업을 항상 SAVEPOINT 안에서 한다.
  차이는 **`rollback()`**에서 드러난다. 이 설정이 있으면 `rollback()`은 마지막 `commit()` 이후의 변경만 되돌린다 (실제 DB와 같다).
  없으면 `rollback()`이 바깥 트랜잭션까지 통째로 되돌려서, **이미 `commit()`한 데이터까지 사라진다** — 실제 서버와 다르게 동작하는 테스트가 된다.
- **`app.dependency_overrides[get_db] = lambda: db_session`** — 앱이 `get_db()`를 부를 자리에 테스트 세션을 넣는다.
- **`tests/test_post_repository.py`** — HTTP를 거치지 않고 repository를 직접 테스트한다.
  같은 트랜잭션 안에서는 `now()`가 같은 값이므로, 정렬에 `id` 보조 기준이 꼭 필요하다는 것도 이 테스트가 증명한다.

**픽스처 실행 순서** (`--setup-show`의 실제 출력)

```
SETUP    S engine                                  ← S = session 스코프, 한 번만
        SETUP    F db_session (fixtures used: engine)   ← F = function 스코프, 테스트마다
        tests/test_post_repository.py::test_save_assigns_id .
        TEARDOWN F db_session                      ← 롤백
        SETUP    F db_session (fixtures used: engine)
        SETUP    F client (fixtures used: db_session)
        tests/test_posts.py::test_get_post .
        TEARDOWN F client
        TEARDOWN F db_session
TEARDOWN S engine                                  ← 마지막에 테이블 삭제
```

## Spring이라면?

| pytest | JUnit / Spring Test |
|---|---|
| 픽스처 (`@pytest.fixture`) | `@BeforeEach` + `@AfterEach`를 하나로 합치고, 결과를 **파라미터로 주입**받는 것 |
| `scope="session"` | `@BeforeAll` / Spring 테스트 컨텍스트 캐싱 |
| 테스트 함수 인자 `client` | 필드 주입 `@Autowired MockMvc mockMvc` |
| `conftest.py` | 공통 테스트 설정 클래스 / 테스트용 `@Configuration` |
| 트랜잭션 롤백 격리 | 테스트 메서드의 `@Transactional` (끝나면 자동 롤백) |
| `app.dependency_overrides[...]` | `@MockBean` / `@TestConfiguration` |
| `@pytest.mark.parametrize` | `@ParameterizedTest` + `@ValueSource` |

## 디버깅 포인트

**자주 쓰는 pytest 옵션**

| 명령 | 용도 |
|---|---|
| `uv run pytest -x` | 첫 실패에서 멈춘다 |
| `uv run pytest -vv` | 실패한 assert의 값을 자세히 보여준다 |
| `uv run pytest -k update` | 이름에 `update`가 들어간 테스트만 실행 |
| `uv run pytest -s` | `print()` 출력을 보여준다 (기본은 숨김) |
| `uv run pytest --setup-show` | 픽스처가 언제 만들어지고 정리되는지 보여준다 |
| `uv run pytest --lf` | 지난번에 실패한 테스트만 다시 실행 |

**`fixture 'xxx' not found`** — 픽스처 이름 오타이거나, `conftest.py`가 테스트 파일보다 상위 폴더에 없는 경우다.
에러 메시지 아래에 `available fixtures:` 목록이 나오므로 그걸 보고 고친다.

**⚠️ 이 테스트 구조의 한계 — 꼭 기억할 것**

테스트에서 앱과 테스트가 **같은 세션 하나**를 공유한다. 그래서 서비스에서 `commit()`을 빼먹어도,
같은 세션 안에서는 방금 추가한 데이터가 보이므로 **테스트가 통과해 버린다.**
실제 서버에서는 요청마다 세션이 달라서 데이터가 사라진다. 07단계 실습 1번에서 직접 확인한다.

## 직접 해볼 것

1. `uv run pytest --setup-show tests/test_post_repository.py`로 픽스처 생성/정리 순서를 관찰한다.
2. `create_savepoint`의 효과를 직접 확인한다. 아래 임시 테스트를 `tests/test_tmp_probe.py`로 만들고 실행한다.

   ```python
   from app.posts.models import Post
   from app.posts.repository import PostRepository


   def test_probe(db_session):
       repo = PostRepository(db_session)
       repo.save(Post(title="a", content="c", author="x"))
       db_session.commit()      # 서비스가 커밋했다고 치고
       repo.save(Post(title="b", content="c", author="x"))
       db_session.rollback()    # 이후 작업이 실패해서 롤백
       print("남은 글:", repo.count())
   ```

   ```bash
   uv run pytest -s tests/test_tmp_probe.py      # 남은 글: 1  ← 커밋한 a는 남는다 (실제 DB와 같음)
   ```

   이제 `conftest.py`에서 `join_transaction_mode="create_savepoint",` 줄을 지우고 다시 실행하면 `남은 글: 0`이 나온다.
   롤백이 바깥 트랜잭션까지 되돌려 **커밋한 a까지 사라진 것**이다. 반면 `uv run pytest -q`로 기존 테스트를 돌리면 모두 통과한다 —
   지금 서비스 코드는 `rollback()`을 직접 부르지 않기 때문이다. "테스트 격리 설정은 평소엔 티가 안 나다가 특정 코드 경로에서만 다르게 동작한다"는 점을 기억하자.
   (08단계 이후 코드에서 해 본다면 함수를 `async def`로, 세션 호출에 `await`를 붙인다.)
   끝나면 `git checkout -- tests/ && rm tests/test_tmp_probe.py`로 되돌린다.
