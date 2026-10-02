"""DB 연결과 세션 관리 (async 버전)."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# psycopg 3는 같은 URL로 동기/비동기 모두 쓸 수 있다
engine = create_async_engine(settings.database_url)

# async에서는 expire_on_commit=False가 사실상 필수다
# (commit 후 속성 접근 시 암묵적 SELECT를 할 수 없기 때문)
SessionLocal = async_sessionmaker(engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """모든 ORM 모델의 부모. Base.metadata에 테이블 정의가 모인다."""


async def get_db() -> AsyncIterator[AsyncSession]:
    session = SessionLocal()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


DbSession = Annotated[AsyncSession, Depends(get_db)]
