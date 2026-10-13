"""Scrubbed JSON logs for API and worker operational events."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime


_SAFE_FIELDS = ("method", "path", "status_code", "duration_ms", "run_id", "attempt", "error_code")


class JsonLogFormatter(logging.Formatter):
    """Emit a small allowlisted event envelope; never serialize arbitrary extras."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname.lower(),
            "event": getattr(record, "event", record.getMessage()),
            "logger": record.name,
        }
        for key in _SAFE_FIELDS:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def configure_logging() -> logging.Logger:
    """Configure the application logger once without changing host logging."""
    logger = logging.getLogger("octodig")
    if not any(getattr(handler, "_octodig_json", False) for handler in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(JsonLogFormatter())
        handler._octodig_json = True  # type: ignore[attr-defined]
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
