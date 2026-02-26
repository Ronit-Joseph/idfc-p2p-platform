"""
Budgets Module — FastAPI Routes

Prefix: ``/api/budgets``

Provides read-only budget information and a budget-availability check
endpoint consumed by the PR workflow before approval.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user
from backend.modules.budgets.schemas import BudgetCheckResponse, BudgetResponse
from backend.modules.budgets import service

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


# ---------------------------------------------------------------------------
# GET  /api/budgets
# ---------------------------------------------------------------------------

@router.get("", response_model=List[BudgetResponse])
async def list_budgets(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> List[BudgetResponse]:
    """Return all department budgets."""
    budgets = await service.list_budgets(db)
    return [BudgetResponse.model_validate(b) for b in budgets]


# ---------------------------------------------------------------------------
# POST /api/budgets/check
# ---------------------------------------------------------------------------

@router.post("/check", response_model=BudgetCheckResponse)
async def check_budget(
    dept: str = Query(..., description="Department code (e.g. TECH)"),
    amount: float = Query(..., description="Requested amount to validate"),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> BudgetCheckResponse:
    """Check whether a requested amount is within budget for a department.

    Query parameters:
    - **dept**: department code (e.g. "TECH")
    - **amount**: the amount to check availability against
    """
    result = await service.check_budget(db, dept, amount)
    return BudgetCheckResponse(**result)
