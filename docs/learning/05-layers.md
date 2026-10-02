# 05. 레이어 분리 — router / service / repository

```bash
git diff step-04 step-05 --stat
git diff step-04 step-05 -- tests/     # 테스트는 import 경로만 바뀌었다
```

**이번 단계의 핵심:** 코드 구조를 크게 바꿨지만 **테스트 본문은 한 줄도 바꾸지 않았다.**
그래도 56개 테스트가 모두 통과한다 → 동작이 그대로라는 증거다. 테스트가 리팩터링의 안전망 역할을 한다.

## 이번에 바뀐 것

```
app/
├── main.py              조립만 한다: 앱 생성, 예외 핸들러 등록, 라우터 등록
├── core/                도메인과 무관한 공통 부품
│   ├── config.py        설정 (Settings)
│   ├── database.py      engine, 세션, get_db, DbSession
│   └── exceptions.py    NotFoundError + 404 핸들러
└── posts/               게시글 도메인 (기능 단위 패키지)
    ├── router.py        HTTP 입출력
    ├── schemas.py       요청/응답 DTO
    ├── service.py       비즈니스 로직 + commit + 도메인 예외
    ├── repository.py    쿼리 (commit 하지 않음)
    └── models.py        ORM 모델
```

- **`__init__.py`** — 폴더를 "패키지"로 만든다. 그래야 `from app.posts.service import ...`처럼 import할 수 있다. 내용은 비어 있어도 된다.
- **`APIRouter(prefix="/posts")` + `app.include_router(...)`** — 라우트를 파일별로 나누고 `main.py`에서 모은다.
- **`Depends` 체인** — 엔드포인트 → `get_post_service` → `get_db` 순서로 의존성을 만든다.
- **도메인 예외** — 서비스는 `HTTPException`(HTTP 개념) 대신 `PostNotFoundError`(도메인 개념)를 던진다.
  `core/exceptions.py`의 핸들러가 이 예외를 404 응답으로 바꾼다.
- **`Settings`** — DB URL을 코드에 직접 쓰지 않고 환경 변수 / `.env`에서 읽는다. `.env.example`을 복사해서 `.env`를 만들면 된다 (`.env`는 커밋하지 않는다).

## Spring이라면?

| FastAPI | Spring |
|---|---|
| `router.py` + `APIRouter(prefix="/posts")` | `@RestController` + `@RequestMapping("/posts")` |
| `service.py`의 `PostService` | `@Service` |
| `repository.py`의 `PostRepository` | `JpaRepository` (여기서는 직접 구현) |
| `Depends(get_post_service)` | 생성자 주입 |
| `register_exception_handlers` + `@app.exception_handler` | `@RestControllerAdvice` + `@ExceptionHandler` |
| `Settings(BaseSettings)` | `@ConfigurationProperties` + `application.yml` |
| `.env` | `application-local.yml` / 환경 변수 |
| `app.include_router(...)` | 컴포넌트 스캔 |

**Spring과 다른 점 두 가지**

1. **빈이 싱글톤이 아니다.** `get_post_service()`는 **요청마다** 호출되어 `PostService`를 새로 만든다.
   요청마다 세션이 다르니 서비스도 요청마다 만드는 것이다.
2. **자동 스캔이 없다.** 라우터를 만들어도 `main.py`에서 `include_router`를 하지 않으면 존재하지 않는 것과 같다.

## 디버깅 포인트

**요청 하나가 지나가는 길** (`PATCH /posts/1`)

```
app/main.py              app.include_router(posts_router) 로 등록된 라우트 매칭
 → app/core/database.py  get_db(): 세션 열기 (yield 앞)          ← 의존성을 먼저 푼다
 → app/posts/router.py   get_post_service(db) → PostService(db)
 → app/posts/schemas.py  경로/쿼리/바디 검증 (PostUpdate)
                         실패하면 422 응답. 엔드포인트는 실행되지 않지만 get_db의 열기/닫기는 실행된다
 → app/posts/router.py   update_post(post_id, payload, service)
 → app/posts/service.py  update(): get() → repository.find_by_id()
                         없으면 PostNotFoundError → core/exceptions.py 핸들러 → 404
 → app/posts/service.py  setattr + session.commit() + session.refresh()
 → app/posts/router.py   반환한 Post를 response_model(PostResponse)로 직렬화
 → app/core/database.py  get_db(): 세션 닫기 (yield 뒤)
```

**주의:** FastAPI는 의존성(`Depends`)을 먼저 실행하고 그다음에 요청 값을 검증한다. 그래서 422로 끝나는 요청에서도
`get_db()`에 걸어 둔 브레이크포인트에서는 멈춘다. "엔드포인트 함수에서 안 멈추는데 `get_db`에서는 멈춘다"면 검증 실패를 의심한다.

AI가 만든 FastAPI 코드를 처음 열면 **`main.py`의 `include_router` → 해당 `router.py` → 엔드포인트가 쓰는 `Depends`** 순서로 따라가면 된다.

**자주 보는 에러**

| 증상 | 원인 |
|---|---|
| `ImportError: cannot import name 'X' from partially initialized module ... (most likely due to a circular import)` | 순환 import. 예: `models.py`가 `service.py`를 import하고 `service.py`가 다시 `models.py`를 import. import 방향은 router → service → repository → models 한 방향이어야 한다 |
| `404 {"detail":"Not Found"}` | 라우트 자체가 없다 (`include_router` 누락, 경로 오타) |
| `404 {"detail":"Post 1 not found"}` | 라우트는 있고, 우리 서비스가 "글이 없다"고 판단했다 |

같은 404여도 **메시지가 다르다.** 이 차이로 "라우팅 문제"인지 "데이터 문제"인지 바로 구분할 수 있다.

**지금 적용된 설정값 확인**

```bash
uv run python -c "from app.core.config import settings; print(settings)"
```

## 직접 해볼 것

1. `main.py`에서 `app.include_router(posts_router)`를 주석 처리하고 `uv run pytest -q`를 실행한다. 몇 개가, 어떤 응답으로 실패하는가?
2. `.env` 파일을 만들어 `DATABASE_URL=postgresql+psycopg://board:board@localhost:5999/board`(틀린 포트)로 설정하고
   서버를 띄운 뒤 `GET /posts`를 호출한다. 서버 로그의 에러를 읽는다. 끝나면 `.env`를 지운다.
3. `service.py`의 `PostNotFoundError`가 `NotFoundError` 대신 `Exception`을 상속하게 바꾸고 `GET /posts/999`를 호출한다. 응답이 어떻게 바뀌는가? 왜 그런가?
4. 끝나면 `git checkout -- app/`로 되돌린다.
