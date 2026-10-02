"""게시글 비즈니스 로직. Spring의 @Service에 해당한다.

@Transactional이 없으므로 변경 작업은 여기서 직접 commit 한다.
"""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.posts.models import Post
from app.posts.repository import PostRepository
from app.posts.schemas import PostCreate, PostUpdate


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
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(post, field, value)
        self.session.commit()
        self.session.refresh(post)
        return post

    def delete(self, post_id: int) -> None:
        post = self.get(post_id)
        self.repository.delete(post)
        self.session.commit()
