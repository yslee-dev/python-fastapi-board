"""게시글 비즈니스 로직 (async 버전).

@Transactional이 없으므로 변경 작업은 여기서 직접 commit 한다.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.posts.models import Post
from app.posts.repository import PostRepository
from app.posts.schemas import PostCreate, PostUpdate

# 로거 이름 = 모듈 경로 "app.posts.service" (SLF4J의 LoggerFactory.getLogger(getClass()))
logger = logging.getLogger(__name__)


class PostNotFoundError(NotFoundError):
    def __init__(self, post_id: int) -> None:
        super().__init__(f"Post {post_id} not found")
        self.post_id = post_id


class PostService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = PostRepository(session)

    async def create(self, data: PostCreate) -> Post:
        post = await self.repository.save(Post(**data.model_dump()))
        await self.session.commit()
        await self.session.refresh(post)  # DB가 채운 created_at 등을 다시 읽는다
        logger.info("게시글 생성 id=%s", post.id)
        return post

    async def get(self, post_id: int) -> Post:
        post = await self.repository.find_by_id(post_id)
        if post is None:
            raise PostNotFoundError(post_id)
        return post

    async def get_page(self, page: int, size: int) -> tuple[list[Post], int]:
        posts = await self.repository.find_page(offset=(page - 1) * size, limit=size)
        return posts, await self.repository.count()

    async def update(self, post_id: int, data: PostUpdate) -> Post:
        post = await self.get(post_id)
        # exclude_unset=True: 클라이언트가 실제로 보낸 필드만 반영한다
        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(post, field, value)  # 메모리 속 객체만 바꾸므로 await 없음
        await self.session.commit()
        await self.session.refresh(post)
        logger.info("게시글 수정 id=%s fields=%s", post.id, sorted(changes))
        return post

    async def delete(self, post_id: int) -> None:
        post = await self.get(post_id)
        await self.repository.delete(post)
        await self.session.commit()
        logger.info("게시글 삭제 id=%s", post_id)
