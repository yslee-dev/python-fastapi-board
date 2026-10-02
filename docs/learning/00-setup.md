# 00. 프로젝트 셋업

```bash
git show step-00 --stat
```

## 이번에 바뀐 것

| 파일 | 역할 |
|---|---|
| `pyproject.toml` | 프로젝트 이름, Python 버전, 의존성, 도구(ruff, pytest) 설정을 한 파일에 모은다 |
| `.python-version` | 이 프로젝트가 쓸 Python 버전(3.12). `uv python pin 3.12`가 만든다 |
| `uv.lock` | 실제로 설치된 모든 패키지의 정확한 버전. 커밋해서 팀원 모두가 같은 버전을 쓴다 |
| `.venv/` | 프로젝트 전용 가상환경. 이 프로젝트의 Python과 패키지가 여기에만 설치된다 (커밋하지 않음) |
| `.vscode/` | 인터프리터 경로, 저장 시 ruff 포맷, pytest 사용 설정 |

**uv**는 Python 버전 설치, 가상환경 생성, 패키지 설치, 명령 실행을 한 도구로 처리한다.
예전 방식(`pyenv` + `venv` + `pip` + `requirements.txt`)을 대체하는 최근 실무 표준이다.

## Spring이라면?

| Python (uv) | Java (Gradle) |
|---|---|
| `pyproject.toml` | `build.gradle` |
| `uv.lock` | `gradle.lockfile` |
| `.python-version` | `java { toolchain { languageVersion = 21 } }` |
| `.venv/` | 프로젝트 전용 JDK + `~/.gradle/caches`의 jar들 (단, 프로젝트마다 따로 있음) |
| `uv sync` | `./gradlew dependencies` (의존성 내려받기) |
| `uv run pytest` | `./gradlew test` |
| `uv add fastapi` | `implementation("...")` 한 줄 추가 + 다운로드 |
| `uv add --dev pytest` (`[dependency-groups] dev`) | `testImplementation("...")` |

가장 큰 차이: Java는 클래스패스를 빌드 도구가 매번 구성하지만, Python은 **어떤 python 실행 파일로 실행했느냐**가
곧 어떤 패키지를 쓸 수 있느냐를 결정한다. 그래서 `uv run`(= `.venv`의 python으로 실행)이 중요하다.

## 디버깅 포인트

- `ModuleNotFoundError: No module named 'fastapi'`가 나면 십중팔구 **가상환경 밖의 python**으로 실행한 것이다.
  - 터미널: `python ...` 대신 `uv run python ...`으로 실행했는지 확인
  - VS Code: 우측 하단 인터프리터가 `.venv`인지 확인 (`Cmd+Shift+P` → `Python: Select Interpreter`)
- 지금 어떤 python이 실행되는지 비교해 보기:

  ```bash
  which python3              # 시스템 python (예: 3.10)
  uv run which python        # 프로젝트 .venv의 python (3.12)
  ```

## 직접 해볼 것

1. `uv run python -c "import sys; print(sys.executable)"`를 실행해서 경로가 `.venv` 안인지 확인한다.
2. `uv add httpx`를 실행하고 `git diff pyproject.toml`로 무엇이 바뀌었는지 본 뒤, `uv remove httpx`로 되돌린다.
