"""애플리케이션 설정. Spring의 application.yml + @ConfigurationProperties에 해당한다.

우선순위: 환경 변수 > .env 파일 > 아래 기본값
필드 database_url은 환경 변수 DATABASE_URL과 매칭된다 (대소문자 무시).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://board:board@localhost:5433/board"
    test_database_url: str = "postgresql+psycopg://board:board@localhost:5433/board_test"
    log_level: str = "INFO"


settings = Settings()
