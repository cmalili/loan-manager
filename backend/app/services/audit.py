"""Audit logging service."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def _serialize_value(value):
    """Convert ORM column values into JSON-safe primitives."""

    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def snapshot_model(instance) -> dict[str, object] | None:
    """Capture the current column-state snapshot for an ORM instance."""

    if instance is None:
        return None

    mapper = sa_inspect(instance.__class__)
    return {
        column.key: _serialize_value(getattr(instance, column.key))
        for column in mapper.columns
    }


def record_audit_log(
    db: Session,
    *,
    user_id: UUID | None,
    entity_type: str,
    entity_id: UUID,
    action_type: str,
    before_state: dict[str, object] | None = None,
    after_state: dict[str, object] | None = None,
) -> AuditLog:
    """Persist one audit log entry within the current transaction."""

    audit_log = AuditLog(
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action_type=action_type,
        before_state_json=before_state,
        after_state_json=after_state,
    )
    db.add(audit_log)
    return audit_log
