import sys
import os
from loguru import logger


def configure_logger(level: str | None = None, log_file: str | None = None):
    level = str(level or os.getenv("LOG_LEVEL", "INFO")).upper()
    log_file = log_file if log_file is not None else os.getenv("LOG_FILE", "")

    # 清理默认 sink，避免重复初始化导致重复输出
    logger.remove()

    logger.add(
        sys.stdout,
        level=level,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> - <level>{level}</level> - <level>{message}</level>",
    )

    if log_file:
        logger.add(
            f"{log_file}.log",
            level=level,
            rotation="1 MB",
            retention=7,
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
        )

    return logger


logger = configure_logger()
