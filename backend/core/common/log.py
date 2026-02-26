import sys
from loguru import logger

from core.common.config import cfg


def _build_logger():
    level = str(cfg.get("log.level", "INFO")).upper()
    log_file = cfg.get("log.file", "")

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


logger = _build_logger()
