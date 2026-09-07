import contextvars
import json
import logging
from datetime import UTC, datetime
from typing import Any


request_id_context: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="system"
)


class JsonFormatter(logging.Formatter):
    """Minimal structured logs with an allowlist of safe operational fields."""

    safe_fields = (
        "operation",
        "method",
        "path",
        "status_code",
        "duration_ms",
        "dependency",
        "document_id",
        "review_id",
        "error_type",
    )

    def format(self, record: logging.LogRecord) -> str:
        event: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_context.get(),
        }
        for field in self.safe_fields:
            value = getattr(record, field, None)
            if value is not None:
                event[field] = value
        if record.exc_info:
            event["exception_type"] = record.exc_info[0].__name__
        return json.dumps(event, ensure_ascii=True)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
