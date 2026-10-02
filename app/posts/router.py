"""게시글 API. Spring의 @RestController에 해당한다.

HTTP 입출력만 담당하고 로직은 서비스에 맡긴다.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import DbSession
from app.posts.models import Post
from app.posts.schemas import PostCreate, PostListResponse, PostResponse, PostUpdate
from app.posts.service import PostService

router = APIRouter(prefix="/posts", tags=["posts"])  # @RequestMapping("/posts")


def get_post_service(db: DbSession) -> PostService:
    # 의존성 체인: 엔드포인트 → get_post_service → get_db
    # Spring이 생성자 주입으로 해주던 일을 함수로 명시한다
    return PostService(db)


PostServiceDep = Annotated[PostService, Depends(get_post_service)]


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, service: PostServiceDep) -> Post:
    return service.create(payload)


@router.get("", response_model=PostListResponse)
def list_posts(
    service: PostServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> PostListResponse:
    posts, total = service.get_page(page, size)
    return PostListResponse(
        items=[PostResponse.model_validate(post) for post in posts],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int, service: PostServiceDep) -> Post:
    return service.get(post_id)


@router.patch("/{post_id}", response_model=PostResponse)
def update_post(post_id: int, payload: PostUpdate, service: PostServiceDep) -> Post:
    return service.update(post_id, payload)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, service: PostServiceDep) -> None:
    service.delete(post_id)
