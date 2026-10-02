"""전역 예외 처리. Spring의 @RestControllerAdvice + @ExceptionHandler에 해당한다."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class NotFoundError(Exception):
    """'대상이 없음' 계열 도메인 예외의 부모. 핸들러가 404로 바꾼다."""


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    def handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        # 서비스는 HTTP를 모르고 도메인 예외만 던진다. HTTP 변환은 여기서 한다
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})
