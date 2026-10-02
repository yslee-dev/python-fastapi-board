"""게시글 ORM 모델. JPA의 @Entity에 해당한다."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Post(Base):
    __tablename__ = "posts"

    # Mapped[int]처럼 Optional이 아니면 NOT NULL 컬럼이 된다
    id: Mapped[int] = mapped_column(primary_key=True)  # @Id @GeneratedValue
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(String(50))
    # server_default: INSERT 시 DB가 now()로 채운다 (@CreationTimestamp)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # onupdate: ORM으로 UPDATE할 때 now()로 바꾼다 (@UpdateTimestamp)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
