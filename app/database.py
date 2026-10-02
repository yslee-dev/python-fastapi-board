"""DB 연결과 세션 관리. Spring의 DataSource + EntityManager 설정에 해당한다."""

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# 05단계에서 pydantic-settings로 옮긴다
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://board:board@localhost:5433/board")

# engine = 커넥션 풀 (HikariDataSource)
engine = create_engine(DATABASE_URL)

# SessionLocal() 호출마다 새 세션(= 영속성 컨텍스트, EntityManager)을 만든다
# expire_on_commit=False: commit 후에도 객체 속성을 다시 조회하지 않고 그대로 쓴다
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """모든 ORM 모델의 부모. Base.metadata에 테이블 정의가 모인다."""


def get_db() -> Iterator[Session]:
    # 요청 하나당 세션 하나. FastAPI가 yield 앞을 요청 전에, 뒤를 응답 후에 실행한다
    # (01단계 basics/generators.py의 get_session_like와 같은 구조)
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
