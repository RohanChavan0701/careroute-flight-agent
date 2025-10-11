from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AuditEvent:
    t: datetime
    actor: str
    action: str
    target: str
    details: Dict[str, Any]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def write_audit(actor: str, action: str, target: str, details: Optional[Dict[str, Any]] = None) -> AuditEvent:
    event = AuditEvent(t=utc_now(), actor=actor, action=action, target=target, details=details or {})
    # For MVP, persist to logs; in production, write to durable store
    logger.info(
        "audit event",  # message kept constant for log parsing
        extra={
            "audit": True,
            "t": event.t.isoformat(),
            "actor": event.actor,
            "action": event.action,
            "target": event.target,
            "details": event.details,
        },
    )
    return event


