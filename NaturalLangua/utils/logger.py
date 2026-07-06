import os
import sys
from loguru import logger
from config import LOG_DIR

logger.remove()

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    colorize=True,
)

logger.add(
    os.path.join(LOG_DIR, "{time:YYYY-MM-DD}.log"),
    level="DEBUG",
    rotation="1 day",
    retention="30 days",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}",
)
