"""
Budgets Module — Service Layer

Async read operations and budget-check logic against the ``budgets`` table.
All database access for the budgets domain should go through these functions
so that routes (and future Kafka consumers) share one code-path.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.budgets.models import Budget


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

async def list_budgets(db: AsyncSession) -> List[Budget]:
    """Return every budget, ordered by department_code ascending."""
    result = await db.execute(
        select(Budget).order_by(Budget.department_code)
    )
    return list(result.scalars().all())


async def get_budget_by_dept(db: AsyncSession, dept_code: str) -> Optional[Budget]:
    """Look up a budget by its ``department_code`` (e.g. "TECH")."""
    result = await db.execute(
        select(Budget).where(Budget.department_code == dept_code)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Budget check
# ---------------------------------------------------------------------------

async def check_budget(db: AsyncSession, dept: str, amount: float) -> Dict[str, Any]:
    """Validate whether ``amount`` can be allocated from the department budget.

    Returns a dict matching the ``BudgetCheckResponse`` shape:
    - status = "APPROVED" when requested amount <= available
    - status = "INSUFFICIENT" when requested amount > available
    - status = "DEPT_NOT_FOUND" when the department does not exist
    """
    budget = await get_budget_by_dept(db, dept)

    if budget is None:
        return {
            "dept": dept,
            "dept_name": "",
            "requested_amount": amount,
            "available_amount": 0,
            "total_budget": 0,
            "committed": 0,
            "actual": 0,
            "status": "DEPT_NOT_FOUND",
            "utilization_after_pct": None,
        }

    available = budget.available_amount or 0.0
    total = budget.total_amount or 0.0
    committed = budget.committed_amount or 0.0
    actual = budget.actual_amount or 0.0

    if amount <= available:
        status = "APPROVED"
    else:
        status = "INSUFFICIENT"

    # Utilization after committing the requested amount:
    # (committed + actual + requested) / total * 100
    if total > 0:
        utilization_after_pct = round(
            (committed + actual + amount) / total * 100, 1
        )
    else:
        utilization_after_pct = None

    return {
        "dept": budget.department_code,
        "dept_name": budget.department_name,
        "requested_amount": amount,
        "available_amount": available,
        "total_budget": total,
        "committed": committed,
        "actual": actual,
        "status": status,
        "utilization_after_pct": utilization_after_pct,
    }
