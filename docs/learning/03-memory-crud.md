# 03. 메모리 CRUD — 요청이 함수에 도착하기까지

```bash
git diff step-02 step-03 -- app/
uv run pytest tests/test_posts.py -v
```

이번 단계는 일부러 **한 파일**(`app/main.py`)에 모든 것을 넣었다. 레이어 없이
"요청 → 검증 → 처리 → 응답"이 한눈에 보이게 하기 위해서다. 저장소도 DB가 아니라 `dict`다.

## 이번에 바뀐 것

**스키마 4개 (DTO)**

| 클래스 | 용도 |
|---|---|
| `PostCreate` | POST 요청 바디. `title`, `content`, `author` 모두 필수 |
| `PostUpdate` | PATCH 요청 바디. `title`, `content` 둘 다 선택. `author`는 아예 없다 → 보내도 무시된다 |
| `PostResponse` | 응답 한 건 |
| `PostListResponse` | 목록 응답 `{items, total, page, size}` |

**FastAPI가 함수 인자를 어디서 가져오는지 정하는 규칙** — 어노테이션 없이 이름과 타입만으로 결정된다.

| 인자 | 판단 기준 | 출처 |
|---|---|---|
| `post_id: int` | 이름이 경로의 `{post_id}`와 같다 | 경로 |
| `payload: PostCreate` | 타입이 `BaseModel` | 요청 바디(JSON) |
| `page: Annotated[int, Query(ge=1)] = 1` | 그 외 단순 타입 | 쿼리 스트링 |

`Annotated[int, Query(ge=1)]`는 "타입은 int, 추가 정보로 쿼리 파라미터이고 1 이상"이라는 뜻이다.
최근 FastAPI 코드는 거의 이 형태를 쓴다. 예전 코드에서는 `page: int = Query(1, ge=1)`처럼 쓰기도 한다.

**그 밖의 새 문법**

- `HTTPException(status_code=404, detail=...)` — 던지면 FastAPI가 `{"detail": ...}` 응답으로 바꿔 준다.
- `payload.model_dump(exclude_unset=True)` — 클라이언트가 **실제로 보낸** 필드만 dict로 꺼낸다. PATCH의 핵심이다.
- `post.model_copy(update={...})` — 일부 필드만 바꾼 새 객체를 만든다 (원본은 그대로).
- `global _next_id` — 함수 안에서 모듈 변수에 **재할당**하려면 필요하다.
- `@field_validator` — 필드 하나에 커스텀 검증을 붙인다. 여기서는 PATCH에 `null`을 직접 보낸 경우를 막는다.
- `ConfigDict(str_strip_whitespace=True)` — 문자열 앞뒤 공백을 제거한다. `"   "`는 `""`가 되어 `min_length=1`에 걸린다.

## Spring이라면?

| FastAPI | Spring |
|---|---|
| `class PostCreate(BaseModel)` | DTO 클래스 + Bean Validation |
| `Field(min_length=1, max_length=100)` | `@Size(min = 1, max = 100)` / `@NotBlank` |
| `payload: PostCreate` | `@RequestBody @Valid PostCreate payload` |
| `post_id: int` | `@PathVariable Long postId` |
| `page: Annotated[int, Query(ge=1)] = 1` | `@RequestParam(defaultValue = "1") @Min(1) int page` |
| 422 Unprocessable Entity | 400 Bad Request (`MethodArgumentNotValidException`) — **FastAPI는 검증 실패에 422를 쓴다** |
| `HTTPException(404, ...)` | `ResponseStatusException(HttpStatus.NOT_FOUND, ...)` |
| 반환 타입 힌트 `-> PostResponse` | `ResponseEntity<PostResponse>` (응답 스키마와 문서가 이걸로 정해진다) |
| `status_code=status.HTTP_201_CREATED` | `@ResponseStatus(HttpStatus.CREATED)` |

## 디버깅 포인트 — 422 응답 해부

검증에 실패하면 **엔드포인트 함수는 아예 실행되지 않는다.** 그래서 함수에 브레이크포인트를 걸어도 멈추지 않는다.
원인은 응답 본문에 있다. 아래는 `content`를 빈 문자열로 보냈을 때의 실제 응답이다.

```bash
curl -s -X POST localhost:8000/posts -H 'Content-Type: application/json' \
  -d '{"title":"a","content":"","author":"홍길동"}'
```

```jsonc
{
  "detail": [                         // 에러 목록. 여러 필드가 틀리면 여러 개가 온다
    {
      "type": "string_too_short",     // 왜: 에러 종류 (검색 키워드로 쓰기 좋다)
      "loc": ["body", "content"],     // 어디: 바디의 content 필드
      "msg": "String should have at least 1 character",  // 사람이 읽는 설명
      "input": "",                    // 실제로 들어온 값
      "ctx": { "min_length": 1 }      // 걸린 제약 조건
    }
  ]
}
```

**`loc`의 첫 번째 값으로 출처를 구분한다**

| `loc` 예시 | 의미 |
|---|---|
| `["body", "title"]` | 요청 바디의 title |
| `["path", "post_id"]` | 경로 변수 (`/posts/abc` → 정수가 아님) |
| `["query", "size"]` | 쿼리 스트링 (`?size=0`) |

**자주 보는 `type`**

| `type` | 원인 |
|---|---|
| `missing` | 필수 필드를 안 보냄 |
| `string_too_short` / `string_too_long` | 길이 제약 위반 |
| `int_parsing` | 정수 자리에 정수가 아닌 값 |
| `greater_than_equal` | `ge=1` 같은 범위 제약 위반 |
| `value_error` | 우리가 만든 `field_validator`에서 `ValueError`를 던짐 |
| `json_invalid` | JSON 문법 오류 |

## 직접 해볼 것

1. `update_post`에서 `exclude_unset=True`를 지우고 `uv run pytest tests/test_posts.py -q`를 실행한다.
   어떤 테스트가 왜 깨지는지 설명해 본다. (힌트: 보내지 않은 `content`가 `None`이 된다)
2. `create_post`의 `global _next_id` 줄을 지우고 POST를 보내 본다. 서버 로그의 `UnboundLocalError` 트레이스백을 끝까지 읽는다.
3. `uv run fastapi dev app/main.py`로 서버를 띄우고 `/docs`에서 글을 만들고, 목록·수정·삭제를 순서대로 호출해 본다.
4. 끝나면 `git checkout -- app/`로 되돌린다.
