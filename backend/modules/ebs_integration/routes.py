"""
EBS Integration Module — FastAPI Routes

Prefix: ``/api/oracle-ebs``

Provides endpoints for listing Oracle EBS integration events and
retrying failed events.  Oracle EBS is retained only as the financial
ledger backend (AP, AR, GL, Fixed Assets) — all PR/PO/Invoice UI is
handled by the P2P platform.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user
from backend.modules.ebs_integration.schemas import EBSEventResponse, EBSRetryResponse
from backend.modules.ebs_integration import service

router = APIRouter(prefix="/api/oracle-ebs", tags=["oracle-ebs"])


# ---------------------------------------------------------------------------
# GET  /api/oracle-ebs/events
# ---------------------------------------------------------------------------

@router.get("/events", response_model=List[EBSEventResponse])
async def list_ebs_events(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> List[EBSEventResponse]:
    """Return all Oracle EBS integration events.

    Each event's ``id`` field corresponds to the ``event_code`` column
    (e.g. "EBS001") to match the legacy API contract.
    """
    events = await service.list_ebs_events(db)
    return [EBSEventResponse.model_validate(e) for e in events]


# ---------------------------------------------------------------------------
# POST /api/oracle-ebs/events/{event_id}/retry
# ---------------------------------------------------------------------------

@router.post("/events/{event_id}/retry", response_model=EBSRetryResponse)
async def retry_ebs_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> EBSRetryResponse:
    """Retry a FAILED EBS integration event.

    Resets the event status to PENDING, increments ``retry_count``, and
    clears any ``error_message``.  Only events with status ``FAILED`` may
    be retried.

    Path parameters:
    - **event_id**: the event code (e.g. "EBS007")
    """
    result = await service.retry_event(db, event_id)
    return EBSRetryResponse.model_validate(result)
