"""Structured (JSON) logging. Never pass tokens, passwords, API keys or medical text to the logger."""
import json
import logging


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            # Exception type only: tracebacks can echo request data into logs.
            payload["exception"] = record.exc_info[0].__name__
        for key in ("user_id", "path", "status_code", "client_ip"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)
