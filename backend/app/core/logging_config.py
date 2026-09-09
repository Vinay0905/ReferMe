import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Base directory for ReferMe logs
LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
APP_LOG_PATH = LOGS_DIR / "app.log"
ERRORS_LOG_PATH = LOGS_DIR / "errors.log"

# Max 10 MB per file, keeps 5 backup files
MAX_LOG_BYTES = 10 * 1024 * 1024
BACKUP_COUNT = 5

LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_central_logging(log_level: int = logging.INFO) -> None:
    """Configures centralized logging: console stdout + rotating app.log + rotating errors.log."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates during reload
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 1. Console Stream Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. General App Log Handler (all events INFO and above)
    app_file_handler = RotatingFileHandler(
        filename=APP_LOG_PATH,
        maxBytes=MAX_LOG_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    app_file_handler.setLevel(log_level)
    app_file_handler.setFormatter(formatter)
    root_logger.addHandler(app_file_handler)

    # 3. Dedicated Error Log Handler (only WARNING, ERROR, CRITICAL)
    error_file_handler = RotatingFileHandler(
        filename=ERRORS_LOG_PATH,
        maxBytes=MAX_LOG_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    error_file_handler.setLevel(logging.WARNING)
    error_file_handler.setFormatter(formatter)
    root_logger.addHandler(error_file_handler)

    # Lower noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)

    root_logger.info("Centralized logging initialized (console + app.log + errors.log)")
