import logging
from logging.handlers import TimedRotatingFileHandler
import os

from src.database.config import settings


LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_LEVEL = settings.app.log_level


def setup_logger(name: str = "app") -> logging.Logger:
    logger = logging.getLogger(name)

    # защита от дублей при повторных импортах
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | "
            "%(module)s:%(lineno)d | %(funcName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # file handler (daily rotation)
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, "app.log"),
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # не дублировать логи через root logger
    logger.propagate = False

    return logger


logger = setup_logger("my_app")
