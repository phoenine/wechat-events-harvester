import sys
import os
from loguru import logger


def configure_logger(level: str | None = None, log_file: str | None = None):
    level = str(level or "INFO").upper()
    log_file = str(log_file).strip() if log_file is not None else ""

    logger.remove()

    logger.add(
        sys.stdout,
        level=level,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> - <level>{level}</level> - <level>{message}</level>",
    )

    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        logger.add(
            log_file,
            level=level,
            rotation="1 MB",
            retention=7,
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
        )

    return logger


logger = configure_logger()
