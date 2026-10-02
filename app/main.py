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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Post {post_id} not found"
        )
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
