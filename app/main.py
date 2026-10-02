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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Post {post_id} not found"
        )
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
