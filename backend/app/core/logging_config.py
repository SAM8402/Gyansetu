import logging
from pathlib import Path

import structlog

from .config import settings

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"


def setup_logging() -> structlog.stdlib.BoundLogger:
    file_handler = logging.FileHandler(str(LOG_FILE), encoding="utf-8")
    file_handler.setLevel(settings.LOG_LEVEL)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.KeyValueRenderer(
                key_order=["timestamp", "level", "event"],
            ),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    root_logger.addHandler(file_handler)

    logger = structlog.get_logger()
    logger.info("log_file", path=str(LOG_FILE))
    return logger


logger = setup_logging()
