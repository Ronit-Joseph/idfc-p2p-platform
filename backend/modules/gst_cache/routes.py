"""
GST Cache Module — FastAPI Routes

Prefix: ``/api/gst-cache``

Provides cached GSTIN data served from a local copy of Cygnet GSP batch
exports, and a sync endpoint to refresh the cache.  Per the architecture,
only IRN generation, IRN cancellation, and e-way bill require live API
calls — all other GST lookups are served from this cache.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user
from backend.modules.gst_cache.schemas import (
    GSTCacheListResponse,
    GSTCacheSummary,
    GSTRecordResponse,
    GSTSyncResponse,
)
from backend.modules.gst_cache import service

router = APIRouter(prefix="/api/gst-cache", tags=["gst-cache"])


# ---------------------------------------------------------------------------
# GET  /api/gst-cache
# ---------------------------------------------------------------------------

@router.get("", response_model=GSTCacheListResponse)
async def list_gst_cache(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> GSTCacheListResponse:
    """Return all cached GSTIN records with an aggregate summary."""
    data = await service.list_gst_records(db)
    return GSTCacheListResponse(
        records=[GSTRecordResponse.model_validate(r) for r in data["records"]],
        summary=GSTCacheSummary(**data["summary"]),
    )


# ---------------------------------------------------------------------------
# POST /api/gst-cache/sync
# ---------------------------------------------------------------------------

@router.post("/sync", response_model=GSTSyncResponse)
async def sync_gst_cache(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> GSTSyncResponse:
    """Trigger a batch sync of GSTIN data from Cygnet GSP.

    In production this calls the Cygnet batch API.  Currently simulates
    the sync by updating ``last_synced`` on all records and logging the
    operation.
    """
    result = await service.sync_gst_cache(db)
    return GSTSyncResponse(**result)
