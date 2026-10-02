"""게시글 요청/응답 DTO."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PostCreate(BaseModel):
    # str_strip_whitespace: 앞뒤 공백 제거 → "   "는 ""가 되어 min_length에서 걸린다
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=50)


class PostUpdate(BaseModel):
    # author는 수정 불가라 필드가 없다. 정의되지 않은 필드는 조용히 무시된다
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
    # from_attributes: ORM 객체의 속성(post.title)에서 값을 읽을 수 있게 한다
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
