"""
GST Cache Module — Service Layer

Async read operations and sync logic against the ``gst_records`` and
``gst_sync_log`` tables.  All database access for the GST Cache domain
should go through these functions so that routes (and future Kafka
consumers) share one code-path.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.gst_cache.models import GSTRecord, GSTSyncLog


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

async def list_gst_records(db: AsyncSession) -> Dict[str, Any]:
    """Return all cached GSTIN records with an aggregate summary.

    The dict matches the ``GSTCacheListResponse`` shape:
    ``{"records": [...], "summary": {...}}``.
    """

    # Fetch all records ordered by legal_name
    result = await db.execute(
        select(GSTRecord).order_by(GSTRecord.legal_name)
    )
    records = list(result.scalars().all())

    # Build summary counts
    total_gstins = len(records)
    active = sum(1 for r in records if r.status == "ACTIVE")
    issues = total_gstins - active

    # Determine last full sync timestamp from the sync log
    last_full_sync_result = await db.execute(
        select(GSTSyncLog.synced_at)
        .where(GSTSyncLog.batch_type == "FULL")
        .order_by(GSTSyncLog.synced_at.desc())
        .limit(1)
    )
    last_full_sync_row = last_full_sync_result.scalar_one_or_none()
    last_full_sync: Optional[str] = None
    if last_full_sync_row is not None:
        last_full_sync = last_full_sync_row.isoformat()

    return {
        "records": records,
        "summary": {
            "total_gstins": total_gstins,
            "active": active,
            "issues": issues,
            "last_full_sync": last_full_sync,
            "sync_source": "Cygnet GSP",
        },
    }


async def get_gst_by_gstin(db: AsyncSession, gstin: str) -> Optional[GSTRecord]:
    """Look up a single GST record by its GSTIN (used by invoice detail)."""

    result = await db.execute(
        select(GSTRecord).where(GSTRecord.gstin == gstin)
    )
    record = result.scalar_one_or_none()

    # Bump cache hit counter when a record is found
    if record is not None:
        record.cache_hit_count = (record.cache_hit_count or 0) + 1
        await db.flush()

    return record


# ---------------------------------------------------------------------------
# Sync operation
# ---------------------------------------------------------------------------

async def sync_gst_cache(db: AsyncSession) -> Dict[str, Any]:
    """Simulate a batch sync of GSTIN data from Cygnet GSP.

    In production this would call the Cygnet batch API.  For now it
    updates ``last_synced`` on every record and writes a sync-log entry.

    Returns a dict matching the ``GSTSyncResponse`` shape.
    """

    now = datetime.now(timezone.utc)

    # Count records before update (needed for response)
    count_result = await db.execute(select(func.count(GSTRecord.id)))
    total_records: int = count_result.scalar_one()

    # Touch last_synced + sync_source on all records
    await db.execute(
        update(GSTRecord).values(
            last_synced=now,
            sync_source="CYGNET_BATCH",
        )
    )

    # Write sync-log entry
    log_entry = GSTSyncLog(
        synced_at=now,
        provider="Cygnet GSP",
        records_updated=total_records,
        total_gstins=total_records,
        batch_type="FULL",
    )
    db.add(log_entry)

    await db.commit()

    return {
        "status": "completed",
        "records_updated": total_records,
        "timestamp": now.isoformat(),
    }
