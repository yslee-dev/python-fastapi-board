"""게시글 API (async 버전). 함수가 async def가 되고 서비스 호출에 await가 붙는다."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import DbSession
from app.posts.models import Post
from app.posts.schemas import PostCreate, PostListResponse, PostResponse, PostUpdate
from app.posts.service import PostService

router = APIRouter(prefix="/posts", tags=["posts"])  # @RequestMapping("/posts")


def get_post_service(db: DbSession) -> PostService:
    # 객체를 만들기만 하고 IO가 없으므로 동기 함수로 둬도 된다
    return PostService(db)


PostServiceDep = Annotated[PostService, Depends(get_post_service)]


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(payload: PostCreate, service: PostServiceDep) -> Post:
    return await service.create(payload)


@router.get("", response_model=PostListResponse)
async def list_posts(
    service: PostServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> PostListResponse:
    posts, total = await service.get_page(page, size)
    return PostListResponse(
        items=[PostResponse.model_validate(post) for post in posts],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, service: PostServiceDep) -> Post:
    return await service.get(post_id)


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(post_id: int, payload: PostUpdate, service: PostServiceDep) -> Post:
    return await service.update(post_id, payload)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, service: PostServiceDep) -> None:
    await service.delete(post_id)
