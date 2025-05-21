import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# Path to the logs folder.
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Logger configuration.
def setup_logging():
    logger = logging.getLogger("app_logger")
    logger.setLevel(logging.DEBUG)  # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL.).

    # Log format.
    formatter = logging.Formatter(
        "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
    )

    # Console handler.
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Time-based file rotation handler.
    file_handler = TimedRotatingFileHandler(
        LOG_DIR / "app.log", when="midnight", interval=1, backupCount=7, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Attach handlers to the logger.
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# Global logger.
logger = setup_logging()