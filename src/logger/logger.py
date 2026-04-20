import logging
import os
from logging.handlers import TimedRotatingFileHandler

from src.database.config import settings

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_LEVEL = settings.app.log_level


def setup_logger(name: str = "app") -> logging.Logger:
    """
    Configures and returns a structured application logger.

    This logger supports:
        - Console output (INFO level)
        - File logging with daily rotation (DEBUG level)
        - Automatic log file rotation with retention

    Args:
        name (str): Name of the logger instance.

    Returns:
        logging.Logger: Configured logger instance.

    Notes:
        - Prevents duplicate handlers on re-import.
        - Logs are stored in the `logs/` directory.
        - Rotated logs are kept for 7 days.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | "
        "%(module)s:%(lineno)d | %(funcName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, "app.log"),
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.propagate = False

    return logger


logger = setup_logger("my_app")
