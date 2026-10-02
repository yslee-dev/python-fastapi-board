"""게시글 DB 접근 (async 버전).

DB와 통신하는 메서드는 모두 await가 필요하다. session.add()는 메모리 작업이라 동기다.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.posts.models import Post


class PostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, post: Post) -> Post:
        self.session.add(post)
        await self.session.flush()  # INSERT를 지금 보내서 id를 받는다 (commit은 아님)
        return post

    async def find_by_id(self, post_id: int) -> Post | None:
        return await self.session.get(Post, post_id)

    async def find_page(self, offset: int, limit: int) -> list[Post]:
        stmt = (
            select(Post)
            .order_by(Post.created_at.desc(), Post.id.desc())  # 같은 시각이면 id로 결정
            .offset(offset)
            .limit(limit)
        )
        return list(await self.session.scalars(stmt))

    async def count(self) -> int:
        return await self.session.scalar(select(func.count()).select_from(Post)) or 0

    async def delete(self, post: Post) -> None:
        await self.session.delete(post)
