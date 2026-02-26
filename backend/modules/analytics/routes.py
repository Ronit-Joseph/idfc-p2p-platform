"""
Analytics Module — FastAPI Routes

Prefix: ``/api/analytics``

Provides endpoints for spend analytics.  The analytics module has no
dedicated database table — it aggregates data from other modules' tables
(primarily invoices) combined with hardcoded prototype data for category
breakdowns and trends.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user
from backend.modules.analytics.schemas import SpendAnalyticsResponse
from backend.modules.analytics import service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# ---------------------------------------------------------------------------
# GET  /api/analytics/spend
# ---------------------------------------------------------------------------

@router.get("/spend", response_model=SpendAnalyticsResponse)
async def get_spend_analytics(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> SpendAnalyticsResponse:
    """Return spend analytics including summary KPIs, category breakdown,
    monthly trends, and top suppliers.

    Summary KPIs (``total_spend_mtd``, ``total_invoices``,
    ``auto_approval_rate``, ``three_way_match_rate``) are computed from
    the Invoice table in real time.  Category breakdown, monthly trends,
    and top suppliers use hardcoded prototype data.
    """
    data = await service.get_spend_analytics(db)
    return SpendAnalyticsResponse.model_validate(data)
