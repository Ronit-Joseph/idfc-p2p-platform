"""
Purchase Requests Module — FastAPI Routes

Prefix: ``/api/purchase-requests``

All endpoints use the ``pr_number`` (e.g. "PR2024-001") as the path
identifier, matching what the legacy frontend sends.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user, require_role, paginate
from backend.exceptions import NotFoundError
from backend.modules.budgets.models import Budget
from backend.modules.purchase_requests.schemas import (
    PRCreate,
    PRDetailResponse,
    PRResponse,
)
from backend.modules.purchase_requests import service

router = APIRouter(prefix="/api/purchase-requests", tags=["purchase-requests"])


# ---------------------------------------------------------------------------
# GET  /api/purchase-requests
# ---------------------------------------------------------------------------

@router.get("")
async def list_purchase_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
):
    """Return all purchase requests with their line items."""
    prs = await service.list_prs(db)
    return paginate([PRResponse.model_validate(pr) for pr in prs], skip, limit)


# ---------------------------------------------------------------------------
# GET  /api/purchase-requests/{pr_id}
# ---------------------------------------------------------------------------

@router.get("/{pr_id}", response_model=PRDetailResponse)
async def get_purchase_request(
    pr_id: str,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> PRDetailResponse:
    """Return a single PR by its pr_number (e.g. "PR2024-001").

    Includes budget information for the PR's department.
    """
    pr = await service.get_pr_by_number(db, pr_id)
    if pr is None:
        raise NotFoundError(f"Purchase Request {pr_id} not found")

    detail = PRDetailResponse.model_validate(pr)

    # Fetch budget data for the department
    result = await db.execute(
        select(Budget).where(Budget.department_code == pr.department)
    )
    budget_row: Optional[Budget] = result.scalar_one_or_none()

    if budget_row is not None:
        detail.budget = {
            "dept": budget_row.department_code,
            "dept_name": budget_row.department_name,
            "gl_account": budget_row.gl_account,
            "cost_center": budget_row.cost_center,
            "fiscal_year": budget_row.fiscal_year,
            "total": budget_row.total_amount,
            "committed": budget_row.committed_amount,
            "actual": budget_row.actual_amount,
            "available": budget_row.available_amount,
            "currency": budget_row.currency,
        }

    return detail


# ---------------------------------------------------------------------------
# POST /api/purchase-requests
# ---------------------------------------------------------------------------

@router.post("", response_model=PRResponse, status_code=201)
async def create_purchase_request(
    payload: PRCreate,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(require_role("DEPARTMENT_HEAD")),
) -> PRResponse:
    """Create a new purchase request.

    A pr_number (e.g. "PR2024-004") is auto-generated. Budget validation
    is performed against the department's available budget.
    """
    pr = await service.create_pr(db, payload)
    return PRResponse.model_validate(pr)


# ---------------------------------------------------------------------------
# PATCH /api/purchase-requests/{pr_id}/approve
# ---------------------------------------------------------------------------

@router.patch("/{pr_id}/approve", response_model=PRResponse)
async def approve_purchase_request(
    pr_id: str,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role("PROCUREMENT_MANAGER")),
) -> PRResponse:
    """Approve a purchase request that is currently PENDING_APPROVAL.

    Returns 400 (via ValidationError → 422) if the PR is not in the
    correct status or if the approver is the same as the requester
    (maker-checker).
    """
    pr = await service.approve_pr(
        db, pr_id, approved_by=user.get("name", "Unknown"),
    )
    return PRResponse.model_validate(pr)


# ---------------------------------------------------------------------------
# PATCH /api/purchase-requests/{pr_id}/reject
# ---------------------------------------------------------------------------

@router.patch("/{pr_id}/reject", response_model=PRResponse)
async def reject_purchase_request(
    pr_id: str,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(require_role("PROCUREMENT_MANAGER")),
) -> PRResponse:
    """Reject a purchase request."""
    pr = await service.reject_pr(db, pr_id)
    return PRResponse.model_validate(pr)
