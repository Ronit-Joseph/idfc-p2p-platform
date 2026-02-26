"""
Budgets Module — Pydantic Schemas

Defines response models for the Budgets API.

The legacy frontend expects short field names (``dept``, ``total``, etc.)
while the database uses longer descriptive column names.  The
``@model_validator(mode="before")`` on ``BudgetResponse`` handles the
translation so that ``model_validate(orm_instance)`` works seamlessly.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, model_validator


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class BudgetResponse(BaseModel):
    """Flat budget representation returned by the list endpoint.

    Maps DB column names to the legacy API shape:
        department_code  -> dept
        department_name  -> dept_name
        total_amount     -> total
        committed_amount -> committed
        actual_amount    -> actual
        available_amount -> available
    """

    model_config = ConfigDict(from_attributes=True)

    dept: str
    dept_name: str
    gl_account: Optional[str] = None
    cost_center: Optional[str] = None
    fiscal_year: str
    total: float
    committed: float
    actual: float
    available: float
    currency: str = "INR"

    @model_validator(mode="before")
    @classmethod
    def _translate_db_columns(cls, data: Any) -> Any:
        """Translate long DB column names to short legacy field names.

        Works for both ORM model instances (attribute access) and plain dicts.
        """
        if hasattr(data, "__dict__"):
            # SQLAlchemy model instance — build a flat dict
            d = {k: v for k, v in data.__dict__.items() if not k.startswith("_")}
        elif isinstance(data, dict):
            d = dict(data)
        else:
            return data

        # Map DB columns -> legacy field names (only if the legacy name is absent)
        _mappings = {
            "department_code": "dept",
            "department_name": "dept_name",
            "total_amount": "total",
            "committed_amount": "committed",
            "actual_amount": "actual",
            "available_amount": "available",
        }
        for db_col, legacy_name in _mappings.items():
            if legacy_name not in d and db_col in d:
                d[legacy_name] = d[db_col]

        return d


class BudgetCheckResponse(BaseModel):
    """Response returned by the budget-check endpoint."""

    dept: str
    dept_name: str
    requested_amount: float
    available_amount: float
    total_budget: float
    committed: float
    actual: float
    status: str  # "APPROVED" | "INSUFFICIENT" | "DEPT_NOT_FOUND"
    utilization_after_pct: Optional[float] = None
