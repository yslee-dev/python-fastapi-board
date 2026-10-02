from sqlalchemy.orm import Session

from app.posts.models import Post
from app.posts.repository import PostRepository


def make_post(title: str) -> Post:
    return Post(title=title, content="내용", author="홍길동")


def test_save_assigns_id(db_session: Session):
    repository = PostRepository(db_session)

    post = repository.save(make_post("제목"))

    assert post.id is not None
    assert repository.find_by_id(post.id) is post  # 같은 세션 = 같은 객체 (1차 캐시)


def test_find_page_orders_newest_first_even_with_same_created_at(db_session: Session):
    repository = PostRepository(db_session)
    for title in ["t0", "t1", "t2"]:
        repository.save(make_post(title))

    posts = repository.find_page(offset=0, limit=10)

    # 한 트랜잭션 안의 now()는 같은 값이므로 id 내림차순이 순서를 결정한다
    assert len({post.created_at for post in posts}) == 1
    assert [post.title for post in posts] == ["t2", "t1", "t0"]
    assert repository.count() == 3


def test_each_test_starts_with_empty_table(db_session: Session):
    # 다른 테스트가 만든 데이터가 롤백되었는지 확인 (실행 순서와 무관하게 0이어야 한다)
    assert PostRepository(db_session).count() == 0
