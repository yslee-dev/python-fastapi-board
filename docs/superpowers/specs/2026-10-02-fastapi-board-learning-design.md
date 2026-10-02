# FastAPI 게시판 CRUD 학습 프로젝트 설계

- 작성일: 2026-10-02
- 상태: 승인 대기

## 1. 목적과 대상

### 목적
바이브 코딩으로 생성된 Python/FastAPI 코드를 **직접 읽고 디버깅할 수 있는 시각**을 기른다.

### 대상
- Java/Spring 백엔드 3년 차 개발자
- Python 문법과 생태계는 익숙하지 않음
- 모든 설명은 Spring 개념에 빗대어 작성한다

### 성공 기준
1. AI가 생성한 FastAPI 코드를 열었을 때 요청이 router → 검증 → service → repository → DB로 흐르는 과정을 따라갈 수 있다.
2. 데코레이터, `yield`, 컨텍스트 매니저, 타입 힌트, `Depends`가 무슨 일을 하는지 설명할 수 있다.
3. 트레이스백과 422 응답을 읽고 원인 위치를 찾을 수 있다.
4. VS Code 디버거로 요청 처리 중간에 멈춰 변수를 확인할 수 있다.
5. `async def` 코드와 동기 코드의 차이, 그리고 흔한 async 실수를 알아볼 수 있다.

## 2. 학습 방식

- `main` 브랜치에 **단계별 커밋**을 쌓고, 단계마다 git 태그(`step-00` ~ `step-08`)를 붙인다.
- `git diff step-03 step-04`처럼 단계 사이의 변화를 비교하며 학습한다.
- 단계마다 `docs/learning/NN-<name>.md` 학습 노트를 작성한다. 노트는 다음 네 항목으로 구성한다.
  - **이번에 바뀐 것**
  - **Spring이라면?**
  - **디버깅 포인트**
  - **직접 해볼 것**
- 학습용 저장소이므로 단계마다 브랜치나 PR을 만들지 않는다. 단계 구분은 태그로 한다.
- 코드 주석은 한글로, 학습에 필요한 만큼 일반 실무 코드보다 조금 더 자세히 작성한다. 다만 자세한 설명은 학습 노트에 둔다.

## 3. 기술 스택

| 역할 | 선택 | Spring 대응 |
|---|---|---|
| Python | 3.12 (`uv python pin`) | JDK 버전 |
| 패키지/가상환경 | uv + `pyproject.toml` | Gradle + `build.gradle` |
| 웹 프레임워크 | FastAPI + Uvicorn | Spring MVC + 내장 Tomcat |
| 검증/DTO | Pydantic v2 | Bean Validation + DTO |
| ORM | SQLAlchemy 2.0 (07단계까지 동기, 08단계에서 async) | JPA/Hibernate |
| DB 드라이버 | psycopg 3 (08단계에서 asyncpg 추가) | JDBC 드라이버 |
| 마이그레이션 | Alembic | Flyway/Liquibase |
| DB | PostgreSQL 16 (docker compose, 호스트 포트 5433) | 동일 |
| 설정 | pydantic-settings + `.env` | `application.yml` + `@ConfigurationProperties` |
| 테스트 | pytest + FastAPI TestClient (08단계에서 httpx AsyncClient) | JUnit + MockMvc |
| 린트/포맷 | ruff | Checkstyle/Spotless |
| 에디터/디버거 | VS Code + debugpy (`.vscode/launch.json`) | IntelliJ 디버거 |

## 4. 기능 범위

엔티티는 게시글(Post) 하나만 둔다. 댓글, 회원, 인증은 범위에서 제외한다.

### Post 필드

| 필드 | 타입 | 규칙 |
|---|---|---|
| `id` | int | PK, 자동 증가 |
| `title` | str | 필수, 1~100자 |
| `content` | str | 필수, 1자 이상 |
| `author` | str | 필수, 1~50자 |
| `created_at` | datetime | 생성 시 자동 설정 |
| `updated_at` | datetime | 생성/수정 시 자동 설정 |

### API

| Method | Path | 설명 | 성공 | 실패 |
|---|---|---|---|---|
| POST | `/posts` | 생성 | 201 + PostResponse | 422 |
| GET | `/posts?page=1&size=10` | 목록, 최신순 | 200 + PostListResponse | 422 (page < 1, size가 1~100 범위 밖) |
| GET | `/posts/{post_id}` | 단건 조회 | 200 + PostResponse | 404 |
| PATCH | `/posts/{post_id}` | 부분 수정 (`title`, `content`만 가능) | 200 + PostResponse | 404, 422 |
| DELETE | `/posts/{post_id}` | 삭제 | 204 | 404 |
| GET | `/health` | 헬스 체크 | 200 `{"status": "ok"}` | - |

- `PostListResponse`: `{"items": [...], "total": int, "page": int, "size": int}`
- PATCH 요청에서 보내지 않은 필드는 바꾸지 않는다 (`model_dump(exclude_unset=True)`).
- `author`는 생성 후 수정할 수 없다.

## 5. 최종 디렉터리 구조 (05단계 이후)

```
python-fastapi/
├── pyproject.toml          # build.gradle
├── uv.lock
├── .python-version
├── docker-compose.yml      # PostgreSQL 16
├── docker/
│   └── init.sql            # board_test DB 생성
├── .env.example
├── alembic.ini
├── alembic/                # Flyway
│   ├── env.py
│   └── versions/
├── basics/                 # 01단계: 파이썬 기초 예제
├── app/
│   ├── __init__.py
│   ├── main.py             # @SpringBootApplication
│   ├── core/
│   │   ├── config.py       # application.yml
│   │   ├── database.py     # DataSource + 세션 관리
│   │   └── exceptions.py   # @ControllerAdvice
│   └── posts/
│       ├── router.py       # @RestController
│       ├── schemas.py      # Request/Response DTO
│       ├── models.py       # @Entity
│       ├── repository.py   # Repository
│       └── service.py      # @Service
├── tests/
│   ├── conftest.py
│   └── test_posts.py
├── .vscode/
│   ├── launch.json
│   └── settings.json
└── docs/learning/          # 단계별 학습 노트
```

## 6. 단계별 로드맵

| 태그 | 단계 | 내용 | 핵심 학습 포인트 |
|---|---|---|---|
| `step-00` | setup | uv 프로젝트, Python 3.12 고정, ruff, pytest, `.gitignore`, VS Code 기본 설정 | 가상환경, `pyproject.toml`, `uv run`, `uv add` |
| `step-01` | basics | `basics/` 예제 모듈과 pytest 테스트 | 타입 힌트, list/dict comprehension, `None`과 truthy/falsy, 클래스와 `@dataclass`, 예외, 데코레이터, 컨텍스트 매니저(`with`), 제너레이터(`yield`) |
| `step-02` | hello | FastAPI 앱, `/health`, Swagger UI | 데코레이터 기반 라우팅, Uvicorn 실행, `/docs` 자동 문서 |
| `step-03` | memory-crud | dict 저장소로 Post CRUD 전체 구현 (한 파일 안에서) | Pydantic 모델, path/query 파라미터, `HTTPException`, 422 응답 읽는 법 |
| `step-04` | database | docker compose PostgreSQL, SQLAlchemy 모델, Alembic 첫 마이그레이션, 저장소를 DB로 교체 | `Depends(get_db)` + `yield`를 이용한 세션 수명 관리, ORM 객체 → Pydantic 변환(`from_attributes`) |
| `step-05` | layers | `app/posts/` 패키지로 router/service/repository 분리, 전역 예외 핸들러, pydantic-settings 설정 | 의존성 주입 체인, 커스텀 예외 → 404 매핑, 설정 주입 |
| `step-06` | tests | `conftest.py` 픽스처, 테스트 DB, API 테스트 | 픽스처와 `yield`, `dependency_overrides`, 트랜잭션 롤백 격리 |
| `step-07` | debugging | `.vscode/launch.json`, 로깅 설정, 버그 실습 문서 | 트레이스백 읽기, 브레이크포인트, `breakpoint()`, 흔한 AI 코드 버그 패턴 |
| `step-08` | async | `async def` + `AsyncSession` + asyncpg로 전환, 테스트도 async로 전환 | async/await가 실제로 바꾸는 것, 이벤트 루프 블로킹 같은 흔한 실수 |

### 01 basics 세부 사항
- `basics/` 아래에 주제별 모듈을 둔다. 예: `type_hints.py`, `collections_demo.py`, `decorators.py`, …
  - 숫자로 시작하는 파일명은 import할 수 없고, `types.py`처럼 표준 라이브러리와 같은 이름은 표준 모듈을 가리므로 쓰지 않는다. 학습 순서는 학습 노트에서 안내한다.
- 모듈마다 같은 내용을 Java로 쓰면 어떻게 되는지 주석으로 비교한다.
- 실행 결과는 `print` 대신 `tests/basics/`의 pytest assert로 확인할 수 있게 해서 그대로 실행되는 예제로 만든다.

### 07 debugging 세부 사항
- 버그는 커밋하지 않는다. `docs/learning/07-debugging.md`에 "이 줄을 이렇게 바꿔 보세요 → 이런 트레이스백이 나옵니다 → 읽는 법 → 원인"을 따라 하는 실습으로 구성한다.
- 실습 시나리오 (최소 5개):
  1. `commit()` 누락 → 응답은 성공했는데 DB에 저장되지 않음
  2. Response 스키마의 `from_attributes` 누락 → 직렬화 에러
  3. 필드 타입 오타 → 422 응답의 `loc` 읽기
  4. `None` 체크 누락 → `AttributeError: 'NoneType' object has no attribute ...`
  5. PATCH에서 `exclude_unset` 누락 → 보내지 않은 필드가 null로 덮어써짐
  6. (08단계 문서) async 함수 안에서 `await` 누락 → coroutine 객체가 반환됨

## 7. 요청 흐름 (05단계 기준)

```
HTTP 요청
 → router.py      경로 매칭, Pydantic으로 Body/Query 검증 (실패 시 422 자동 응답)
 → Depends(get_db) 세션 열기 (get_db의 yield 앞부분)
 → service.py     비즈니스 로직, 대상이 없으면 PostNotFoundError 발생
 → repository.py  SQLAlchemy 2.0 select() 쿼리
 → service.py     변경 작업이면 session.commit()
 → response_model(PostResponse)로 직렬화 (ORM 객체 → JSON)
 → get_db의 yield 뒷부분에서 세션 닫기 (예외 발생 시 rollback)
```

- **트랜잭션 경계는 service 계층에서 명시적으로 `commit()` 한다.** Spring의 `@Transactional`처럼 자동으로 처리되지 않는다는 점을 코드에서 드러나게 한다.
- repository는 세션을 받아 쿼리만 수행하고 commit하지 않는다.

## 8. 에러 처리

- 도메인 예외 `PostNotFoundError(post_id)`는 `app/core/exceptions.py`의 핸들러가 404 `{"detail": "Post {id} not found"}`로 변환한다.
- 검증 에러는 FastAPI 기본 422 응답을 그대로 쓴다.
- 응답 형식은 FastAPI 기본 형식인 `{"detail": ...}`을 유지한다.

## 9. 테스트 전략

- `docker/init.sql`로 같은 PostgreSQL 컨테이너 안에 테스트 전용 DB `board_test`를 만든다.
- 테스트 세션 시작 시 `Base.metadata.create_all()`로 테이블을 만들고, 끝나면 `drop_all()` 한다.
- 테스트마다 커넥션 단위 트랜잭션을 열고 끝나면 롤백해서 격리한다. 이때 service의 `commit()`이 바깥 트랜잭션을 확정하지 않도록 SAVEPOINT 방식(`join_transaction_mode="create_savepoint"`)을 쓴다.
- `app.dependency_overrides[get_db]`로 테스트 세션을 주입한다.
- 다룰 케이스: 생성 성공, 생성 검증 실패(422), 목록 페이지네이션, 단건 조회 성공/404, 부분 수정(보내지 않은 필드 유지)/404, 삭제 성공/404.
- 08단계 async 전환 후에도 같은 시나리오가 모두 통과해야 한다.

## 10. 환경과 실행

- Python 3.12는 `uv python pin 3.12`로 프로젝트 전용으로 설치한다. 시스템 Python 3.10은 건드리지 않는다.
- DB 실행: `docker compose up -d` (호스트 포트 5433 → 컨테이너 5432)
- 마이그레이션: `uv run alembic upgrade head`
- 서버: `uv run fastapi dev app/main.py` (07단계에서 VS Code 디버그 실행 설정 추가)
- 테스트: `uv run pytest`
- 린트: `uv run ruff check . && uv run ruff format --check .`
- 접속 정보는 `.env`로 관리하고, `.env.example`만 커밋한다.

## 11. 완료 기준

- 단계마다 `uv run pytest`와 `ruff check`가 통과한 상태로 커밋하고 태그를 붙인다. 00단계는 테스트가 없으므로 `ruff check`와 `uv run python --version`(3.12 확인)만 검증한다. 02, 03단계는 그 시점에 있는 테스트를 기준으로 한다.
- 04단계 이후 단계는 docker compose DB에 연결해 Swagger UI 또는 curl로 CRUD 전체가 동작하는지 확인한다.
- 모든 단계에 학습 노트가 있다.

## 12. 범위 밖

- 인증/인가, 회원, 댓글, 파일 업로드
- 운영 배포 설정 (Dockerfile로 앱 컨테이너화, CI)
- 커서 기반 페이지네이션, 검색
