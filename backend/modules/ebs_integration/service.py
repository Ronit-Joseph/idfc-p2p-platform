"""
EBS Integration Module — Service Layer

Async business-logic operations against the ``ebs_events`` table.  All
database access for the EBS-integration domain should go through these
functions so that routes (and future Kafka consumers) share one code-path.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.event_bus import Event, event_bus
from backend.exceptions import NotFoundError, ValidationError
from backend.modules.ebs_integration.models import EBSEvent


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

async def list_ebs_events(db: AsyncSession) -> List[Dict[str, Any]]:
    """Return all EBS integration events as dicts with ``event_code`` mapped to ``id``.

    Results are ordered by ``created_at`` descending so the most recent
    events appear first.
    """
    result = await db.execute(
        select(EBSEvent).order_by(EBSEvent.created_at.desc())
    )
    events = list(result.scalars().all())

    rows: List[Dict[str, Any]] = []
    for ev in events:
        rows.append({
            "id": ev.event_code,
            "event_type": ev.event_type,
            "entity_id": ev.entity_id,
            "entity_ref": ev.entity_ref,
            "description": ev.description,
            "gl_account": ev.gl_account,
            "amount": ev.amount,
            "ebs_module": ev.ebs_module,
            "status": ev.status,
            "sent_at": ev.sent_at,
            "acknowledged_at": ev.acknowledged_at,
            "ebs_ref": ev.ebs_ref,
            "error_message": ev.error_message,
        })

    return rows


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------

async def retry_event(db: AsyncSession, event_code: str) -> Dict[str, Any]:
    """Reset a FAILED EBS event back to PENDING and increment its retry count.

    Business rules:
    - Looks up the event by ``event_code`` (e.g. "EBS007").
    - Only events with status ``FAILED`` may be retried; all other statuses
      raise a ``ValidationError``.
    - Resets ``status`` to ``PENDING``, increments ``retry_count`` by 1,
      and clears ``error_message``.
    - Publishes an ``ebs.event_retried`` domain event on the event bus.

    Returns a dict suitable for serialisation as ``EBSRetryResponse``.

    Raises:
        NotFoundError: if no event matches the given event_code.
        ValidationError: if the event is not in FAILED status.
    """
    result = await db.execute(
        select(EBSEvent).where(EBSEvent.event_code == event_code)
    )
    event = result.scalar_one_or_none()

    if event is None:
        raise NotFoundError(f"EBS event {event_code} not found")

    if event.status != "FAILED":
        raise ValidationError(
            f"Cannot retry event {event_code}: current status is {event.status}, "
            f"expected FAILED"
        )

    event.status = "PENDING"
    event.retry_count = (event.retry_count or 0) + 1
    event.error_message = None

    await db.flush()
    await db.refresh(event)

    # Publish domain event
    await event_bus.publish(Event(
        name="ebs.event_retried",
        data={
            "event_code": event.event_code,
            "event_type": event.event_type,
            "entity_id": event.entity_id,
            "retry_count": event.retry_count,
        },
        source="ebs_integration",
    ))

    return {
        "id": event.event_code,
        "status": event.status,
        "retry_count": event.retry_count,
        "message": f"Event {event_code} queued for retry",
    }
