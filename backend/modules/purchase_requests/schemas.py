"""
Purchase Requests Module — Pydantic Schemas

Defines request/response models for the Purchase Requests API.

IMPORTANT: The legacy frontend uses ``pr_number`` (e.g. "PR2024-001") as the
``id`` field in all API calls.  PRResponse therefore exposes an ``id`` field
that maps to the database ``pr_number`` column so that the frontend contract
is never broken — the actual UUID primary key is excluded from responses.

Line-item fields are aliased to the legacy short names:
    description → desc, quantity → qty   (unit_price stays as-is).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Line-item response
# ---------------------------------------------------------------------------

class PRLineItemResponse(BaseModel):
    """Single line item within a PR — uses legacy field names."""

    model_config = ConfigDict(from_attributes=True)

    desc: str = Field(..., description="Line-item description")
    qty: float = Field(..., description="Quantity")
    unit: Optional[str] = None
    unit_price: float = Field(..., description="Unit price")

    @model_validator(mode="before")
    @classmethod
    def _remap_fields(cls, data: Any) -> Any:
        """Map ORM column names → legacy short names expected by the frontend."""
        if hasattr(data, "__dict__"):
            d = {k: v for k, v in data.__dict__.items() if not k.startswith("_")}
        elif isinstance(data, dict):
            d = dict(data)
        else:
            return data
        # description → desc
        if "description" in d and "desc" not in d:
            d["desc"] = d.pop("description")
        # quantity → qty
        if "quantity" in d and "qty" not in d:
            d["qty"] = d.pop("quantity")
        return d


# ---------------------------------------------------------------------------
# PR response (list / create)
# ---------------------------------------------------------------------------

class PRResponse(BaseModel):
    """Purchase Request returned by list / create endpoints.

    ``id`` is always equal to ``pr_number`` (e.g. "PR2024-001") — the
    frontend expects this.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(
        ...,
        description="Same as pr_number — the human-readable PR identifier.",
    )
    title: str
    department: str
    requester: str
    requester_email: Optional[str] = None
    amount: float
    currency: str = "INR"
    gl_account: Optional[str] = None
    cost_center: Optional[str] = None
    category: Optional[str] = None
    supplier_preference: Optional[str] = None
    justification: Optional[str] = None
    status: str
    po_id: Optional[str] = None
    budget_check: Optional[str] = None
    budget_available_at_time: Optional[float] = None
    created_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approver: Optional[str] = None
    rejection_reason: Optional[str] = None
    rejected_at: Optional[datetime] = None
    items: List[PRLineItemResponse] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _set_id_to_pr_number(cls, data: Any) -> Any:
        """Ensure ``id`` in the JSON output equals the ``pr_number`` column."""
        if hasattr(data, "__dict__"):
            d = {k: v for k, v in data.__dict__.items() if not k.startswith("_")}
            d["id"] = d.get("pr_number", d.get("id"))
            return d
        if isinstance(data, dict):
            data["id"] = data.get("pr_number", data.get("id"))
            return data
        return data


# ---------------------------------------------------------------------------
# PR detail response (single-PR endpoint)
# ---------------------------------------------------------------------------

class PRDetailResponse(PRResponse):
    """Extended response that includes budget information for the department."""

    budget: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Create schema
# ---------------------------------------------------------------------------

class PRCreate(BaseModel):
    """Payload accepted when creating a new Purchase Request."""

    title: str = Field(..., min_length=1, max_length=500)
    department: str = Field(..., min_length=1, max_length=10)
    amount: float = Field(..., gt=0)
    gl_account: str = Field(..., min_length=1, max_length=20)
    cost_center: str = Field(..., min_length=1, max_length=20)
    category: str = Field(..., min_length=1, max_length=100)
    justification: str = Field(..., min_length=1)
    requester: str = Field("Demo User", max_length=255)
