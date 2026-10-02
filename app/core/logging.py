"""로깅 설정. Spring의 logback 설정 + logging.level에 해당한다."""

import logging


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        # 어느 파일 몇 번째 줄에서 찍힌 로그인지 보이게 한다 (디버깅에 가장 유용)
        format="%(asctime)s %(levelname)-5s [%(name)s] %(filename)s:%(lineno)d - %(message)s",
    )
