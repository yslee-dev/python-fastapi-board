"""애플리케이션 진입점. Spring의 @SpringBootApplication 클래스에 해당한다."""

from fastapi import FastAPI

app = FastAPI(title="Board API")


@app.get("/health")
def health() -> dict[str, str]:
    # 반환한 dict는 FastAPI가 JSON으로 직렬화한다 (@RestController + Jackson)
    return {"status": "ok"}
