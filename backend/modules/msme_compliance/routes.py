"""
MSME Compliance Module — FastAPI Routes

Prefix: ``/api/msme-compliance``

Provides the Section 43B(h) compliance dashboard: a summary of MSME-flagged
invoices with at-risk / breached counts and total penalty exposure.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user
from backend.modules.msme_compliance.schemas import MSMEComplianceResponse
from backend.modules.msme_compliance import service

router = APIRouter(prefix="/api/msme-compliance", tags=["msme-compliance"])


# ---------------------------------------------------------------------------
# GET  /api/msme-compliance
# ---------------------------------------------------------------------------

@router.get("", response_model=MSMEComplianceResponse)
async def get_msme_compliance(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> MSMEComplianceResponse:
    """Return the MSME Section 43B(h) compliance dashboard.

    Response includes:
    - **summary**: aggregate counts (on_track, at_risk, breached) and penalty exposure
    - **invoices**: individual MSME-flagged invoices sorted by days_remaining ascending
    """
    result = await service.get_msme_compliance(db)
    return MSMEComplianceResponse(**result)
