from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .config import config

LOG_LEVELS = {
    "error": logging.ERROR,
    "warn": logging.WARN,
    "warning": logging.WARN,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}


def _resolve_level(name: str) -> int:
    return LOG_LEVELS.get(name.lower(), logging.INFO)


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        data = getattr(record, "data", None)
        if data:
            payload["data"] = data
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


class _DevFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        base = f"{timestamp} [{record.levelname}] {record.getMessage()}"
        data = getattr(record, "data", None)
        if data:
            base += f" | {json.dumps(data, default=str)}"
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


logger = logging.getLogger("slack_agent")
logger.setLevel(_resolve_level(config.logging.level))

if not logger.handlers:
    handler = logging.StreamHandler(stream=sys.stdout)
    if config.logging.environment.lower() == "development":
        handler.setFormatter(_DevFormatter())
    else:
        handler.setFormatter(_JsonFormatter())
    logger.addHandler(handler)


def log_info(message: str, data: Optional[Dict[str, Any]] = None) -> None:
    kwargs: Dict[str, Any] = {}
    if data:
        kwargs["extra"] = {"data": data}
    logger.info(message, **kwargs)


def log_error(message: str, error: Optional[BaseException] = None) -> None:
    error_data: Optional[Dict[str, Any]] = None
    if error:
        error_data = {"message": str(error)}
        response = getattr(error, "response", None)
        if response is not None:
            error_data["response"] = str(response)
    kwargs: Dict[str, Any] = {}
    if error_data:
        kwargs["extra"] = {"data": error_data}
    logger.error(message, exc_info=error, **kwargs)


def log_warn(message: str, data: Optional[Dict[str, Any]] = None) -> None:
    kwargs: Dict[str, Any] = {}
    if data:
        kwargs["extra"] = {"data": data}
    logger.warning(message, **kwargs)


def log_debug(message: str, data: Optional[Dict[str, Any]] = None) -> None:
    kwargs: Dict[str, Any] = {}
    if data:
        kwargs["extra"] = {"data": data}
    logger.debug(message, **kwargs)
