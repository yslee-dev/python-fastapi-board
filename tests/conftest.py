"""pytest 공용 픽스처 (async 버전).

격리 전략은 06단계와 같다. 테이블 생성/삭제는 동기 엔진으로 한 번만 하고,
테스트마다 async 커넥션에서 바깥 트랜잭션을 열고 롤백한다.
"""

from collections.abc import AsyncIterator, Iterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.posts import models  # noqa: F401  Base.metadata에 posts 테이블 등록


@pytest.fixture(scope="session")
def create_tables() -> Iterator[None]:
    engine = create_engine(settings.test_database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
async def db_session(create_tables: None) -> AsyncIterator[AsyncSession]:
    # 테스트마다 이벤트 루프가 새로 만들어지므로 엔진도 테스트마다 만든다
    engine = create_async_engine(settings.test_database_url, poolclass=NullPool)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            autoflush=False,
            expire_on_commit=False,
        )
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    # TestClient 대신 같은 이벤트 루프에서 도는 AsyncClient를 쓴다
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()
