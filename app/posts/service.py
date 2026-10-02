"""게시글 비즈니스 로직. Spring의 @Service에 해당한다.

@Transactional이 없으므로 변경 작업은 여기서 직접 commit 한다.
"""

import logging

from sqlalchemy.orm import Session

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
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = PostRepository(session)

    def create(self, data: PostCreate) -> Post:
        post = self.repository.save(Post(**data.model_dump()))
        self.session.commit()
        self.session.refresh(post)  # DB가 채운 created_at 등을 다시 읽는다
        # f-string 대신 %s 인자를 쓴다 (SLF4J의 {} 플레이스홀더와 같은 이유)
        logger.info("게시글 생성 id=%s", post.id)
        return post

    def get(self, post_id: int) -> Post:
        post = self.repository.find_by_id(post_id)
        if post is None:
            raise PostNotFoundError(post_id)
        return post

    def get_page(self, page: int, size: int) -> tuple[list[Post], int]:
        posts = self.repository.find_page(offset=(page - 1) * size, limit=size)
        return posts, self.repository.count()

    def update(self, post_id: int, data: PostUpdate) -> Post:
        post = self.get(post_id)
        # exclude_unset=True: 클라이언트가 실제로 보낸 필드만 반영한다
        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(post, field, value)
        self.session.commit()
        self.session.refresh(post)
        logger.info("게시글 수정 id=%s fields=%s", post.id, sorted(changes))
        return post

    def delete(self, post_id: int) -> None:
        post = self.get(post_id)
        self.repository.delete(post)
        self.session.commit()
        logger.info("게시글 삭제 id=%s", post_id)
