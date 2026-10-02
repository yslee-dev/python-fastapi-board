"""게시글 DB 접근. Spring Data의 Repository에 해당한다.

쿼리만 담당하고 commit은 하지 않는다. 트랜잭션 경계는 서비스가 정한다.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.posts.models import Post


class PostRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, post: Post) -> Post:
        self.session.add(post)
        self.session.flush()  # INSERT를 지금 보내서 id를 받는다 (commit은 아님)
        return post

    def find_by_id(self, post_id: int) -> Post | None:
        return self.session.get(Post, post_id)

    def find_page(self, offset: int, limit: int) -> list[Post]:
        stmt = (
            select(Post)
            .order_by(Post.created_at.desc(), Post.id.desc())  # 같은 시각이면 id로 결정
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def count(self) -> int:
        return self.session.scalar(select(func.count()).select_from(Post)) or 0

    def delete(self, post: Post) -> None:
        self.session.delete(post)
