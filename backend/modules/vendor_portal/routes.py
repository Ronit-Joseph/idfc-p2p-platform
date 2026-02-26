"""
Vendor Portal Module — FastAPI Routes

Prefix: ``/api/vendor-portal``

Provides endpoints for listing events received from the external Vendor
Management Portal.  The Vendor Portal is a separate independently-built
system — integrated via Kafka events + REST.  This module exposes the
captured events for the P2P frontend.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user
from backend.modules.vendor_portal.schemas import VendorPortalEventResponse
from backend.modules.vendor_portal import service

router = APIRouter(prefix="/api/vendor-portal", tags=["vendor-portal"])


# ---------------------------------------------------------------------------
# GET  /api/vendor-portal/events
# ---------------------------------------------------------------------------

@router.get("/events", response_model=List[VendorPortalEventResponse])
async def list_vendor_events(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> List[VendorPortalEventResponse]:
    """Return all Vendor Portal integration events.

    Each event's ``id`` field corresponds to the ``event_code`` column
    (e.g. "VPE001") to match the legacy API contract.
    """
    events = await service.list_vendor_events(db)
    return [VendorPortalEventResponse.model_validate(e) for e in events]
