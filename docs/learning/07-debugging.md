# 07. 디버깅 — 디버거, 로그, 그리고 일부러 고장 내 보기

```bash
git diff step-06 step-07
```

이 단계가 프로젝트의 핵심이다. 아래 **버그 실습 5개**는 모두 AI가 만든 FastAPI 코드에서 실제로 자주 보이는 버그다.
출력은 이 저장소에서 직접 재현한 **실제 출력**이다.

## 이번에 바뀐 것

- **`.vscode/launch.json`** — VS Code 디버그 실행 설정 2개
  - `FastAPI: 서버 디버그` — Uvicorn을 디버거 아래에서 실행한다 (자동 리로드 없음)
  - `Pytest: 현재 파일 디버그` — 지금 열린 테스트 파일을 디버거 아래에서 실행한다
  - `envFile`에 `.env`가 지정되어 있다. `.env`가 없으면 경고만 나오고 기본 설정값으로 실행된다.
- **`app/core/logging.py`** — 로그 포맷에 **파일명:줄 번호**를 넣었다.
- **`settings.log_level`** — 환경 변수 `LOG_LEVEL`로 로그 레벨을 바꾼다 (기본 `INFO`).
- **`app/posts/service.py`** — 생성/수정/삭제 시 INFO 로그를 남긴다.

```
2026-10-02 15:30:12,583 INFO  [app.posts.service] service.py:34 - 게시글 생성 id=2
                              ^ 로거 이름         ^ 파일:줄     ^ 메시지
```

## Spring이라면?

| Python | Java / Spring |
|---|---|
| debugpy (VS Code 디버거) | IntelliJ 디버거 / JDWP |
| `logging.getLogger(__name__)` | `LoggerFactory.getLogger(getClass())` |
| `logger.info("id=%s", post.id)` | `log.info("id={}", post.getId())` |
| `LOG_LEVEL=DEBUG` | `logging.level.root=DEBUG` |
| `breakpoint()` | (대응 없음) 코드 한 줄로 그 자리에서 대화형 디버거 진입 |

## 트레이스백 읽는 법

**Java 스택 트레이스와 순서가 반대다.**

```
Java:   Exception: 메시지          ← 맨 위가 예외
          at 가장 안쪽 호출
          at ...
          at 가장 바깥 호출

Python: Traceback (most recent call last):
          File 가장 바깥 호출        ← 위로 갈수록 바깥 (프레임워크 코드)
          File ...
          File 가장 안쪽 호출        ← 맨 아래쪽이 실제로 터진 곳
        AttributeError: 메시지     ← 맨 아래가 예외
```

**읽는 순서**

1. **맨 마지막 줄**부터 본다. 예외 종류와 메시지.
2. 위로 올라가며 **내 코드(`app/...`) 경로가 처음 나오는 곳**을 찾는다. `.venv/...`는 라이브러리라 일단 건너뛴다.
3. 예외가 여러 개 연결되어 있으면 사이의 문구를 본다.
   - `The above exception was the direct cause of the following exception:` — `raise X from e`. **위가 원인**, 아래가 결과.
   - `During handling of the above exception, another exception occurred:` — `except` 블록 안에서 **또 다른 예외**가 났다. 대개 위쪽이 진짜 원인이다.
4. **422는 트레이스백이 없다.** 검증 실패는 정상 흐름이라 서버 로그에는 한 줄만 남는다. 응답 본문의 `loc`, `type`을 본다 (03단계).

## 디버거 사용법 (VS Code)

1. 왼쪽 "실행 및 디버그"(`Cmd+Shift+D`) → `FastAPI: 서버 디버그` 선택 → F5
2. `app/posts/service.py`의 `create` 메서드 첫 줄 왼쪽 여백을 클릭해 브레이크포인트(빨간 점)를 건다.
3. 브라우저에서 `http://localhost:8000/docs` → `POST /posts` 실행
4. VS Code가 멈추면:
   - **변수** 패널: `data`(검증된 `PostCreate`), `self.session` 등을 펼쳐 본다.
   - **호출 스택** 패널: `create_post`(router) → `create`(service) 흐름을 확인한다.
   - **디버그 콘솔**: `data.model_dump()`처럼 식을 직접 실행해 본다.
   - F10(다음 줄), F11(함수 안으로), Shift+F11(함수 밖으로), F5(계속)
5. **조건부 브레이크포인트**: 빨간 점 우클릭 → "Edit Condition" → `post_id == 999`
6. **테스트 디버깅**: 실패하는 테스트 파일을 열고 `Pytest: 현재 파일 디버그`로 실행 → 실패 지점 근처에 브레이크포인트

**`breakpoint()` (터미널에서 바로)**

코드에 `breakpoint()` 한 줄을 넣고 `uv run pytest -s tests/test_posts.py::test_create_post`를 실행하면 그 줄에서 `(Pdb)` 프롬프트가 뜬다.

| 명령 | 뜻 |
|---|---|
| `p data` | 변수 출력 |
| `pp data.model_dump()` | 보기 좋게 출력 |
| `n` | 다음 줄 |
| `s` | 함수 안으로 |
| `w` | 현재 호출 스택 |
| `c` | 계속 실행 |
| `q` | 종료 |

`-s`를 빼먹으면 pytest가 입력을 막아서 에러가 난다. 실습이 끝나면 `breakpoint()` 줄은 반드시 지운다.

---

## 버그 실습

**공통 방법:** 코드를 바꾼 뒤 서버를 띄운다 (`uv run fastapi dev app/main.py`). 끝나면 `git checkout -- app/`로 되돌린다.

### 실습 1: `commit()` 누락 — 성공 응답인데 데이터가 없다

**바꿀 코드** `app/posts/service.py`

```diff
     def create(self, data: PostCreate) -> Post:
         post = self.repository.save(Post(**data.model_dump()))
-        self.session.commit()
         self.session.refresh(post)
```

**재현**

```bash
curl -s -X POST localhost:8000/posts -H 'Content-Type: application/json' \
  -d '{"title":"t","content":"c","author":"a"}'
curl -s localhost:8000/posts/2     # ← 위 응답의 id
uv run pytest -q
```

**실제 출력**

```
{"id":2,"title":"t","content":"c","author":"a","created_at":"...","updated_at":"..."}   ← 201
{"detail":"Post 2 not found"}                                                          ← 404
60 passed                                                                              ← 테스트는 통과!
```

서버 로그에도 `INFO [app.posts.service] service.py:34 - 게시글 생성 id=2`가 찍힌다.

**읽는 법:** 에러도 트레이스백도 없다. **"응답은 성공, 로그도 성공, 그런데 다음 요청에서 데이터가 없다"** 이것 자체가 단서다.

**원인:** `save()`의 `flush()`로 INSERT는 DB에 보내졌고 id도 받았다. 하지만 커밋하지 않은 채
`get_db()`의 `finally`에서 세션이 닫히면서 **롤백**되었다. (id 시퀀스는 롤백되지 않으므로 다음 글은 id=3이 된다.)

**테스트가 통과하는 이유:** 06단계 픽스처에서 테스트와 앱이 **같은 세션**을 쓰기 때문에, 커밋하지 않아도 같은 세션 안에서는 데이터가 보인다.
"테스트가 통과했다 ≠ 버그가 없다"의 대표적인 예다.

**AI 코드에서 보이는 모양:** `db.add(x)` 다음에 `db.commit()`이 없는 엔드포인트, 또는 `try:` 블록 안에서만 커밋하고 다른 분기에서는 빠뜨린 코드.

### 실습 2: `from_attributes` 누락 — 목록만 500

**바꿀 코드** `app/posts/schemas.py`

```diff
 class PostResponse(BaseModel):
-    model_config = ConfigDict(from_attributes=True)
-
     id: int
```

**재현:** POST로 글을 하나 만든 뒤 `curl -s localhost:8000/posts`, `curl -s localhost:8000/posts/<id>`

**실제 출력**

```
GET /posts       → 500 Internal Server Error
GET /posts/<id>  → 200 (정상!)
```

서버 로그 (핵심 줄만):

```
  File ".../app/posts/router.py", line 40, in list_posts
    items=[PostResponse.model_validate(post) for post in posts],
pydantic_core._pydantic_core.ValidationError: 1 validation error for PostResponse
  Input should be a valid dictionary or instance of PostResponse
  [type=model_type, input_value=<app.posts.models.Post object at 0x10dc7a7b0>, input_type=Post]
```

**읽는 법:** 맨 아래 `ValidationError ... for PostResponse` → 응답 DTO를 만들다 실패했다.
`input_type=Post` → **ORM 객체**를 넣었는데 dict가 아니라서 거절당했다. 바로 위 내 코드 줄은 `router.py:40`.

**원인:** `model_validate(post)`로 ORM 객체를 직접 변환하려면 `from_attributes=True`가 필요하다.
단건 조회가 정상인 이유는 FastAPI가 `response_model`로 직렬화할 때 내부적으로 `from_attributes`를 켜고 검증하기 때문이다.
**같은 설정 누락인데 엔드포인트마다 증상이 다르다** — AI 코드에서 "어떤 API는 되고 어떤 API는 안 되는" 버그의 전형이다.

### 실습 3: 필드 타입 오타 — 422의 `loc` 읽기

**바꿀 코드** `app/posts/schemas.py`

```diff
 class PostCreate(BaseModel):
     ...
-    author: str = Field(min_length=1, max_length=50)
+    author: int
```

**재현**

```bash
curl -s -X POST localhost:8000/posts -H 'Content-Type: application/json' \
  -d '{"title":"t","content":"c","author":"홍길동"}'
```

**실제 출력**

```json
{"detail":[{"type":"int_parsing","loc":["body","author"],
  "msg":"Input should be a valid integer, unable to parse string as an integer","input":"홍길동"}]}
```

**읽는 법:** `loc: ["body","author"]` → 요청 바디의 author. `type: int_parsing` → 정수로 바꿀 수 없다.
서버 로그에는 `"POST /posts HTTP/1.1" 422` 한 줄뿐이고 트레이스백은 없다.

**원인:** 스키마의 타입 힌트가 곧 검증 규칙이다. **타입 힌트 한 글자 실수가 API 계약을 바꾼다.**
클라이언트는 정상인데 422가 나면, 요청보다 **스키마 정의**를 먼저 의심한다.

### 실습 4: `None` 체크 누락 — `'NoneType' object has no attribute`

**바꿀 코드** `app/posts/service.py`

```diff
     def get(self, post_id: int) -> Post:
         post = self.repository.find_by_id(post_id)
-        if post is None:
-            raise PostNotFoundError(post_id)
         return post
```

**재현**

```bash
curl -s -X PATCH localhost:8000/posts/999999 -H 'Content-Type: application/json' -d '{"title":"x"}'
```

**실제 출력:** `Internal Server Error` (500). 서버 로그:

```
Traceback (most recent call last):
  ... (uvicorn, starlette, fastapi 내부 프레임 수십 줄) ...
  File ".../app/posts/router.py", line 54, in update_post
    return service.update(post_id, payload)
  File ".../app/posts/service.py", line 51, in update
    setattr(post, field, value)
AttributeError: 'NoneType' object has no attribute 'title'
```

**읽는 법:** 맨 아래 → `None`에 `.title`을 설정하려 했다. 위로 올라가 첫 `app/` 줄 → `service.py:51`의 `setattr`.
여기서 `post`가 왜 `None`인지 거슬러 올라가면 `self.get()`이 None을 돌려줬다는 걸 알 수 있다.

**원인:** `session.get()`은 없으면 예외 대신 `None`을 돌려준다 (Java의 `findById`가 `Optional`을 돌려주는 것과 같은 상황인데, 타입이 강제하지 않는다).
**AI 코드에서 보이는 모양:** `post = db.get(...)` 다음 줄에서 바로 `post.xxx`를 쓰는 코드. 404여야 할 요청이 500이 된다.

### 실습 5: PATCH에서 `exclude_unset` 누락 — 안 보낸 필드가 null로

**바꿀 코드** `app/posts/service.py`

```diff
-        changes = data.model_dump(exclude_unset=True)
+        changes = data.model_dump()
```

**재현:** `uv run pytest tests/test_posts.py::test_update_post_partially -x`

**실제 출력 (핵심 줄)**

```
app/posts/service.py:54: in update
    self.session.commit()
E   sqlalchemy.exc.IntegrityError: (psycopg.errors.NotNullViolation) null value in column "content"
    of relation "posts" violates not-null constraint
E   DETAIL:  Failing row contains (1, 새 제목, null, 홍길동, ...).
E   [SQL: UPDATE posts SET title=%(title)s::VARCHAR, content=%(content)s::VARCHAR, updated_at=now() WHERE posts.id = %(posts_id)s::INTEGER]
E   [parameters: {'title': '새 제목', 'content': None, 'posts_id': 1}]
```

**읽는 법:** 예외는 `commit()`에서 났지만 **원인은 그 전**이다. `[parameters: ...]`에 `'content': None`이 보인다.
제목만 보냈는데 content가 None으로 들어갔다 → `model_dump()`가 보내지 않은 필드도 기본값(None)으로 꺼냈다.

**원인:** `exclude_unset=True`가 없으면 "안 보냄"과 "null로 보냄"을 구분하지 못한다.
DB 컬럼이 NOT NULL이라 이번에는 에러로 드러났지만, **NULL 허용 컬럼이었다면 에러 없이 데이터가 조용히 지워진다.** 훨씬 위험하다.

---

## 직접 해볼 것

1. 위 실습 5개를 하나씩 직접 재현하고, 각각 `git checkout -- app/`로 되돌린다.
2. 실습 4를 VS Code 디버거로 다시 해 본다. `service.py`의 `update`에 브레이크포인트를 걸고 변수 패널에서 `post`가 `None`인 것을 확인한다.
3. `LOG_LEVEL=DEBUG uv run fastapi dev app/main.py`로 띄우고 로그가 어떻게 달라지는지 본다.
