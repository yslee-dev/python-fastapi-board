# FastAPI 게시판 학습 프로젝트

Spring 개발자가 FastAPI 코드를 읽고 디버깅하는 눈을 기르기 위한 단계별 학습 저장소입니다.

## 학습 방법

단계마다 커밋과 태그(`step-00` ~ `step-08`)가 있습니다.

```bash
git tag                          # 단계 목록
git diff step-02 step-03         # 단계 사이의 변화 보기
git checkout step-03             # 특정 단계로 이동 (돌아올 땐 git checkout main)
```

단계별 학습 노트는 `docs/learning/`에 있습니다.

## 준비물

- [uv](https://docs.astral.sh/uv/)
- Docker
- VS Code (추천 확장은 `.vscode/extensions.json` 참고)

## 자주 쓰는 명령

```bash
uv sync                  # 의존성 설치 (= ./gradlew dependencies)
uv run pytest            # 테스트 (= ./gradlew test)
uv run ruff check .      # 린트
uv run ruff format .     # 포맷
uv run fastapi dev app/main.py   # 개발 서버 (자동 재시작) → http://localhost:8000/docs
```
