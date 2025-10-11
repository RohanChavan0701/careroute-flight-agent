import logging
from typing import Any, Dict

REDACTED = "[REDACTED]"


class SensitiveHeaderFilter(logging.Filter):
    """Redacts sensitive headers or fields in structured logs.

    This is a light-weight safeguard; do not log request bodies that could contain PHI.
    """

    SENSITIVE_KEYS = {"authorization", "x-api-key", "cookie", "set-cookie"}

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.args, dict):
                record.args = self._redact_dict(record.args)
        except Exception:
            # Never fail logging
            pass
        return True

    def _redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        redacted: Dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(key, str) and key.lower() in self.SENSITIVE_KEYS:
                redacted[key] = REDACTED
            else:
                redacted[key] = value
        return redacted


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(SensitiveHeaderFilter())


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Inherit root config
        logger.addFilter(SensitiveHeaderFilter())
    return logger


