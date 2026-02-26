"""
Vendor Portal Module — Service Layer

Async business-logic operations against the ``vendor_portal_events`` table.
All database access for the vendor-portal domain should go through these
functions so that routes (and future Kafka consumers) share one code-path.

The Vendor Management Portal is a separate independently-built system;
events are received via Kafka and stored in this table for P2P processing.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.vendor_portal.models import VendorPortalEvent


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

async def list_vendor_events(db: AsyncSession) -> List[Dict[str, Any]]:
    """Return all Vendor Portal events as dicts with ``event_code`` mapped to ``id``.

    Results are ordered by ``created_at`` descending so the most recent
    events appear first.
    """
    result = await db.execute(
        select(VendorPortalEvent).order_by(VendorPortalEvent.created_at.desc())
    )
    events = list(result.scalars().all())

    rows: List[Dict[str, Any]] = []
    for ev in events:
        rows.append({
            "id": ev.event_code,
            "event_type": ev.event_type,
            "timestamp": ev.timestamp,
            "supplier_id": ev.supplier_id,
            "supplier_name": ev.supplier_name,
            "payload": ev.payload,
            "processed": ev.processed,
            "p2p_action": ev.p2p_action,
        })

    return rows
