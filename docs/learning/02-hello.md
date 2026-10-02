# 02. FastAPI Hello — 첫 엔드포인트

```bash
git diff step-01 step-02
uv run fastapi dev app/main.py     # → http://localhost:8000/docs
```

## 이번에 바뀐 것

- `app = FastAPI(title="Board API")` — 애플리케이션 객체. 라우트, 미들웨어, 예외 핸들러가 모두 여기에 등록된다.
- `@app.get("/health")` — `GET /health` 요청을 아래 함수에 연결한다.
- 반환한 `dict`는 FastAPI가 자동으로 JSON 응답으로 만든다. 반환 타입 힌트(`-> dict[str, str]`)는 OpenAPI 문서에도 반영된다.
- **Uvicorn** — FastAPI 앱을 실제로 실행하는 ASGI 서버. `fastapi dev`는 내부적으로 Uvicorn을 **자동 리로드** 모드로 띄운다 (코드 저장 → 서버 재시작).
- `/docs` (Swagger UI), `/openapi.json` (OpenAPI 스펙) — 코드만 작성하면 자동으로 생긴다.
- `fastapi[standard]` — FastAPI 본체 + Uvicorn + httpx(테스트 클라이언트용) + fastapi CLI를 한 번에 설치하는 묶음.

## Spring이라면?

| FastAPI | Spring Boot |
|---|---|
| `app = FastAPI()` | `SpringApplication.run(...)`으로 뜨는 애플리케이션 컨텍스트 |
| `@app.get("/health")` | `@GetMapping("/health")` |
| 함수가 `dict` 반환 | `@RestController` 메서드가 객체 반환 → Jackson 직렬화 |
| Uvicorn | 내장 Tomcat |
| `fastapi dev` | `./gradlew bootRun` + DevTools |
| `/docs` | springdoc-openapi의 `/swagger-ui.html` |
| `TestClient(app)` | `MockMvc` (실제 포트를 열지 않고 앱을 직접 호출) |

`@app.get`은 01단계의 `basics/decorators.py`에 있는 `MiniRouter.get`과 **같은 원리**다.
경로와 함수를 `app` 안의 라우트 목록에 등록하고, 함수 자체는 그대로 돌려준다.
그래서 테스트나 다른 코드에서 `health()`를 그냥 호출할 수도 있다.

## 디버깅 포인트

**서버 로그 한 줄 읽기**

```
INFO:     127.0.0.1:52344 - "GET /health HTTP/1.1" 200 OK
          ^ 클라이언트       ^ 메서드와 경로              ^ 상태 코드
```

**자주 보는 응답**

| 응답 | 의미 | 확인할 것 |
|---|---|---|
| `404 {"detail":"Not Found"}` | 경로와 맞는 라우트가 없다 | 경로 오타, 라우터 등록 누락 (05단계) |
| `405 {"detail":"Method Not Allowed"}` | 경로는 있지만 메서드가 다르다 | GET/POST 혼동 |
| `[Errno 48] Address already in use` | 8000 포트를 다른 프로세스가 쓰고 있다 | `lsof -i :8000`으로 찾아서 종료 |

**`uv run pytest`에서 import가 되는 이유:** `pyproject.toml`의 `[tool.pytest.ini_options] pythonpath = ["."]` 덕분에
프로젝트 루트가 import 경로에 들어가서 `from app.main import app`이 동작한다.

## 직접 해볼 것

1. `app/main.py`에 아래 엔드포인트를 추가하고, 서버가 자동으로 재시작되는지 로그로 확인한 뒤 `/docs`에서 호출해 본다.

   ```python
   @app.get("/hello/{name}")
   def hello(name: str) -> dict[str, str]:
       return {"message": f"Hello, {name}!"}
   ```

2. `curl -i localhost:8000/hello/철수`, `curl -i -X POST localhost:8000/health`를 실행하고 상태 코드를 비교한다.
3. 끝나면 `git checkout -- app/`로 되돌린다.
