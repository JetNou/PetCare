import logging
import sys
from pathlib import Path


LOG_NAME = "user_api"
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "app.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(LOG_NAME)
logger.setLevel(logging.DEBUG)
logger.propagate = False

if not logger.handlers:
    log_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO) 
    stream_handler.setFormatter(log_format)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

if __name__ == "__main__":
    logger.info("[Logger] Логгер настроен. Можно использовать logger в проекте.")
    logger.debug("[Logger] Debug-сообщение (увидите только в консоли).")
    logger.info("[Logger] Info-сообщение (пишется и в файл, и в консоль).")
    logger.warning("[Logger] Warning-сообщение.")
    logger.error("[Logger] Error-сообщение.")
    logger.critical("[Logger] Critical-сообщение.")