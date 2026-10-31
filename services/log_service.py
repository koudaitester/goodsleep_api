# services/log_service.py
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from utils.sse_log_helper import push_log

LOG_DIR = "log"
os.makedirs(LOG_DIR, exist_ok=True)


class SseLogHandler(logging.Handler):
    """自定义日志Handler，日志消息自动推送到SSE缓冲区"""
    def emit(self, record):
        try:
            line = self.format(record)
            push_log(line)
        except Exception:
            pass


logger = logging.getLogger("goodsleep_api")
logger.setLevel(logging.INFO)
logger.propagate = False

log_format = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y%m%d')}.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8"
)
file_handler.setFormatter(log_format)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)

sse_handler = SseLogHandler()
sse_handler.setFormatter(log_format)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.addHandler(sse_handler)
