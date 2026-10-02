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
- **`join_transaction_mode="create_savepoint"`** — 서비스가 `commit()`을 불러도 진짜 커밋이 아니라 SAVEPOINT만 확정된다.
  그래서 테스트가 끝나면 바깥 트랜잭션을 통째로 롤백할 수 있다.
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
2. `conftest.py`에서 `join_transaction_mode="create_savepoint",` 줄을 지우고 `uv run pytest -q`를 **두 번** 실행한다.
   무엇이 깨지는지, 왜 그런지 생각해 본다. (힌트: 서비스의 `commit()`이 바깥 트랜잭션을 진짜로 커밋해 버린다)
   끝나면 원복하고 테스트 DB를 정리한다.

   ```bash
   git checkout -- tests/
   docker compose exec db psql -U board -d board_test -c 'drop table if exists posts'
   ```
