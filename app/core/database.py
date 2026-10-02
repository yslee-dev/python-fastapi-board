"""DB 연결과 세션 관리. Spring의 DataSource + EntityManager 설정에 해당한다."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# engine = 커넥션 풀 (HikariDataSource)
engine = create_engine(settings.database_url)

# expire_on_commit=False: commit 후에도 객체 속성을 다시 조회하지 않고 그대로 쓴다
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """모든 ORM 모델의 부모. Base.metadata에 테이블 정의가 모인다."""


def get_db() -> Iterator[Session]:
    # 요청 하나당 세션 하나. yield 앞은 요청 전, 뒤는 응답 후에 실행된다
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]
