"""
Purchase Requests Module — Service Layer

Async business-logic operations against the ``purchase_requests`` and
``pr_line_items`` tables.  All database access for the purchase-requests
domain should go through these functions so that routes (and future Kafka
consumers) share one code-path.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.event_bus import Event, event_bus
from backend.exceptions import NotFoundError, ValidationError
from backend.modules.budgets.models import Budget
from backend.modules.purchase_requests.models import PRLineItem, PurchaseRequest
from backend.modules.purchase_requests.schemas import PRCreate


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _load_items(db: AsyncSession, pr_id: str) -> List[PRLineItem]:
    """Load all line items for a given PR, ordered by sort_order."""
    result = await db.execute(
        select(PRLineItem)
        .where(PRLineItem.pr_id == pr_id)
        .order_by(PRLineItem.sort_order)
    )
    return list(result.scalars().all())


async def _attach_items(db: AsyncSession, pr: PurchaseRequest) -> PurchaseRequest:
    """Attach line items as a transient ``items`` attribute on the PR object."""
    items = await _load_items(db, pr.id)
    # Set items as a non-column attribute so the Pydantic schema can read it
    pr.items = items  # type: ignore[attr-defined]
    return pr


async def _attach_items_bulk(
    db: AsyncSession, prs: List[PurchaseRequest]
) -> List[PurchaseRequest]:
    """Attach line items to every PR in the list (batched query)."""
    if not prs:
        return prs

    pr_ids = [pr.id for pr in prs]
    result = await db.execute(
        select(PRLineItem)
        .where(PRLineItem.pr_id.in_(pr_ids))
        .order_by(PRLineItem.sort_order)
    )
    all_items = list(result.scalars().all())

    # Group items by pr_id
    items_by_pr: Dict[str, List[PRLineItem]] = {}
    for item in all_items:
        items_by_pr.setdefault(item.pr_id, []).append(item)

    for pr in prs:
        pr.items = items_by_pr.get(pr.id, [])  # type: ignore[attr-defined]

    return prs


async def _generate_next_pr_number(db: AsyncSession) -> str:
    """Generate the next sequential PR number (e.g. "PR2024-004").

    Finds the current maximum numeric suffix among existing pr_numbers that
    match the ``PR2024-nnn`` pattern and increments by one.
    """
    result = await db.execute(
        select(PurchaseRequest.pr_number)
        .where(PurchaseRequest.pr_number.like("PR2024-%"))
        .order_by(PurchaseRequest.pr_number.desc())
    )
    existing = result.scalars().first()

    if existing is None:
        return "PR2024-001"

    # Extract numeric suffix from e.g. "PR2024-008"
    try:
        suffix = int(existing.split("-")[-1])
    except (ValueError, IndexError):
        suffix = 0

    return f"PR2024-{suffix + 1:03d}"


async def _find_budget_for_department(
    db: AsyncSession, department: str
) -> Optional[Budget]:
    """Find the budget row for a given department code."""
    result = await db.execute(
        select(Budget).where(Budget.department_code == department)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

async def list_prs(db: AsyncSession) -> List[PurchaseRequest]:
    """Return all Purchase Requests with line items, ordered by created_at descending."""
    result = await db.execute(
        select(PurchaseRequest).order_by(PurchaseRequest.created_at.desc())
    )
    prs = list(result.scalars().all())
    return await _attach_items_bulk(db, prs)


async def get_pr_by_number(
    db: AsyncSession, pr_number: str
) -> Optional[PurchaseRequest]:
    """Look up a PR by its human-readable ``pr_number`` (e.g. "PR2024-001").

    Returns the PR with line items attached, or None if not found.
    """
    result = await db.execute(
        select(PurchaseRequest).where(PurchaseRequest.pr_number == pr_number)
    )
    pr = result.scalar_one_or_none()
    if pr is not None:
        await _attach_items(db, pr)
    return pr


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------

async def create_pr(db: AsyncSession, data: PRCreate) -> PurchaseRequest:
    """Create a new Purchase Request with budget validation.

    Business rules:
    - Auto-generates a ``pr_number`` like "PR2024-004".
    - Looks up the department budget; sets ``budget_check`` to "APPROVED"
      if the requested amount fits within ``available_amount``, otherwise "FAILED".
    - Initial status is always "PENDING_APPROVAL".
    """
    pr_number = await _generate_next_pr_number(db)

    # Budget check
    budget = await _find_budget_for_department(db, data.department)
    if budget is not None and data.amount <= budget.available_amount:
        budget_check = "APPROVED"
        budget_available = budget.available_amount
    elif budget is not None:
        budget_check = "FAILED"
        budget_available = budget.available_amount
    else:
        # No budget row found — treat as failed
        budget_check = "FAILED"
        budget_available = None

    pr = PurchaseRequest(
        pr_number=pr_number,
        title=data.title,
        department=data.department,
        requester=data.requester,
        amount=data.amount,
        gl_account=data.gl_account,
        cost_center=data.cost_center,
        category=data.category,
        justification=data.justification,
        status="PENDING_APPROVAL",
        currency="INR",
        budget_check=budget_check,
        budget_available_at_time=budget_available,
    )
    db.add(pr)
    await db.flush()
    await db.refresh(pr)

    # Attach empty items list (newly created PR has no line items yet)
    pr.items = []  # type: ignore[attr-defined]

    # Publish event
    await event_bus.publish(Event(
        name="pr.created",
        data={"pr_number": pr.pr_number, "department": pr.department,
              "amount": pr.amount, "budget_check": budget_check},
        source="purchase_requests",
    ))

    return pr


async def approve_pr(db: AsyncSession, pr_number: str) -> PurchaseRequest:
    """Approve a PR that is currently PENDING_APPROVAL.

    Raises ``ValidationError`` if the PR is not in PENDING_APPROVAL status.
    Raises ``NotFoundError`` if the PR does not exist.
    """
    pr = await get_pr_by_number(db, pr_number)
    if pr is None:
        raise NotFoundError(f"Purchase Request {pr_number} not found")

    if pr.status != "PENDING_APPROVAL":
        raise ValidationError(
            f"Cannot approve PR {pr_number}: current status is {pr.status}, "
            f"expected PENDING_APPROVAL"
        )

    pr.status = "APPROVED"
    pr.approved_at = datetime.utcnow()
    pr.approver = "Demo Approver"

    await db.flush()
    await db.refresh(pr)
    await _attach_items(db, pr)

    # Publish event
    await event_bus.publish(Event(
        name="pr.approved",
        data={"pr_number": pr.pr_number, "department": pr.department, "amount": pr.amount},
        source="purchase_requests",
    ))

    return pr


async def reject_pr(db: AsyncSession, pr_number: str) -> PurchaseRequest:
    """Reject a PR.

    Raises ``NotFoundError`` if the PR does not exist.
    """
    pr = await get_pr_by_number(db, pr_number)
    if pr is None:
        raise NotFoundError(f"Purchase Request {pr_number} not found")

    pr.status = "REJECTED"
    pr.rejected_at = datetime.utcnow()
    pr.rejection_reason = "Rejected via demo"

    await db.flush()
    await db.refresh(pr)
    await _attach_items(db, pr)

    # Publish event
    await event_bus.publish(Event(
        name="pr.rejected",
        data={"pr_number": pr.pr_number, "department": pr.department},
        source="purchase_requests",
    ))

    return pr
