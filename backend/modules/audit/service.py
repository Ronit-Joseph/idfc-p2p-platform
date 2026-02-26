"""
Audit Module — Service Layer

Append-only audit log. Events flow in via the event bus subscriber;
read-only queries exposed to the API layer.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.audit.models import AuditLog


# ---------------------------------------------------------------------------
# Write (internal only — called from event bus handler)
# ---------------------------------------------------------------------------

async def log_event(
    db: AsyncSession,
    event_type: str,
    source_module: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    actor: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    """Append a new audit log entry. NEVER update or delete existing entries."""
    entry = AuditLog(
        event_type=event_type,
        source_module=source_module,
        entity_type=entity_type,
        entity_id=entity_id,
        actor=actor,
        payload=payload,
    )
    db.add(entry)
    await db.commit()


# ---------------------------------------------------------------------------
# Read (exposed via routes)
# ---------------------------------------------------------------------------

async def list_audit_logs(
    db: AsyncSession,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    event_type: Optional[str] = None,
    source_module: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Query audit logs with optional filters."""
    q = select(AuditLog)
    if entity_type:
        q = q.where(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.where(AuditLog.entity_id == entity_id)
    if event_type:
        q = q.where(AuditLog.event_type == event_type)
    if source_module:
        q = q.where(AuditLog.source_module == source_module)
    q = q.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)

    result = await db.execute(q)
    return [_log_to_dict(row) for row in result.scalars().all()]


async def get_audit_summary(db: AsyncSession) -> Dict[str, Any]:
    """Return summary statistics for the audit log."""
    # Total events
    total_result = await db.execute(select(func.count(AuditLog.id)))
    total = total_result.scalar() or 0

    # By module
    mod_result = await db.execute(
        select(AuditLog.source_module, func.count(AuditLog.id))
        .group_by(AuditLog.source_module)
    )
    by_module = {row[0]: row[1] for row in mod_result.all()}

    # By event type
    type_result = await db.execute(
        select(AuditLog.event_type, func.count(AuditLog.id))
        .group_by(AuditLog.event_type)
    )
    by_event_type = {row[0]: row[1] for row in type_result.all()}

    # Recent (last 24h)
    cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_result = await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.timestamp >= cutoff)
    )
    recent = recent_result.scalar() or 0

    return {
        "total_events": total,
        "by_module": by_module,
        "by_event_type": by_event_type,
        "recent_events": recent,
    }


async def get_entity_history(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
) -> List[Dict[str, Any]]:
    """Get complete audit trail for a specific entity."""
    result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id,
        )
        .order_by(AuditLog.timestamp.asc())
    )
    return [_log_to_dict(row) for row in result.scalars().all()]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log_to_dict(log: AuditLog) -> Dict[str, Any]:
    return {
        "id": log.id,
        "event_type": log.event_type,
        "source_module": log.source_module,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "actor": log.actor,
        "payload": log.payload,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
    }
