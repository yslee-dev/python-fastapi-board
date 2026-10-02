"""pytest 공용 픽스처. 같은 폴더의 테스트 파일들이 import 없이 자동으로 쓴다.

격리 전략 (Spring 테스트의 @Transactional 롤백과 같은 효과):
1. 테스트 세션 전체에서 테이블은 한 번만 만든다.
2. 테스트마다 커넥션에서 바깥 트랜잭션을 열고, 끝나면 롤백한다.
3. 서비스가 commit()을 불러도 SAVEPOINT만 확정되므로 바깥 트랜잭션은 롤백할 수 있다.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.posts import models  # noqa: F401  Base.metadata에 posts 테이블 등록


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    engine = create_engine(settings.test_database_url)
    Base.metadata.drop_all(engine)  # 이전 실행이 비정상 종료됐을 때를 대비
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Iterator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        autoflush=False,
        expire_on_commit=False,
    )
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()  # 테스트가 만든 데이터를 전부 되돌린다
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
