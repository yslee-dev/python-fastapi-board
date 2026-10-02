"""애플리케이션 진입점. 라우터와 예외 핸들러를 조립한다."""

from fastapi import FastAPI

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.posts.router import router as posts_router

setup_logging(settings.log_level)

app = FastAPI(title="Board API")
register_exception_handlers(app)
app.include_router(posts_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
