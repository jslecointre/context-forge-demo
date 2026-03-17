import json
import logging
import os
import sys  # noqa: F401
from logging.handlers import RotatingFileHandler

from backend import PROJECT_ROOT


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "name": record.name,
            "funcName": record.funcName,
            "level": record.levelname,
            "message": record.getMessage(),
            "filename": record.filename,
            "line": record.lineno,
        }
        return json.dumps(log_record)


log_dir = "logs"
log_file = os.path.join(PROJECT_ROOT, "logs", "cf_demo_backend_logs.json")

logging.getLogger("absl").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("mcp.client.sse").setLevel(
    logging.ERROR
)  # suppress Unknown SSE event: keepalive
logging.getLogger("root").setLevel(
    logging.ERROR
)  # suppress notifications/initialized validation noise
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


if not logger.handlers:
    os.makedirs(log_dir, exist_ok=True)

    file_handler = RotatingFileHandler(
        filename=log_file, maxBytes=5_000_000, backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)

    # disabling the console logger for now. Enable if required for debugging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(JsonFormatter())
    logger.addHandler(console_handler)
