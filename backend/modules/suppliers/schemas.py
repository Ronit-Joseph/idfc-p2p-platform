"""
Suppliers Module — Pydantic Schemas

Defines request/response models for the Suppliers API.

IMPORTANT: The frontend uses the supplier `code` (e.g. "SUP001") as the
identifier in all API calls.  SupplierResponse therefore exposes an `id`
field that maps to the database `code` column so that the frontend contract
is never broken — the actual UUID primary key is excluded from responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class SupplierResponse(BaseModel):
    """Flat supplier representation returned by list / detail endpoints.

    ``id`` is always equal to ``code`` (e.g. "SUP001") — the frontend
    expects this.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(
        ...,
        description="Same as code — the human-readable supplier identifier (e.g. SUP001).",
    )
    code: str
    legal_name: str
    gstin: str
    pan: Optional[str] = None
    state: Optional[str] = None
    category: Optional[str] = None
    is_msme: bool = False
    msme_category: Optional[str] = None
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None
    ifsc: Optional[str] = None
    payment_terms: Optional[int] = 30
    risk_score: Optional[float] = None
    status: str = "ACTIVE"
    vendor_portal_status: Optional[str] = None
    contact_email: Optional[str] = None
    onboarded_date: Optional[str] = None
    last_synced_from_portal: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def _set_id_to_code(cls, data: Any) -> Any:
        """Ensure ``id`` in the JSON output equals the ``code`` column.

        Works for both ORM model instances (attribute access) and plain dicts.
        """
        if hasattr(data, "__dict__"):
            # SQLAlchemy model instance — copy code → id via a dict
            d = {k: v for k, v in data.__dict__.items() if not k.startswith("_")}
            d["id"] = d.get("code", d.get("id"))
            return d
        if isinstance(data, dict):
            data["id"] = data.get("code", data.get("id"))
            return data
        return data


class SupplierDetailResponse(SupplierResponse):
    """Extended response that includes cross-module data.

    ``gst_data`` and ``recent_invoices`` will be populated once
    the GST-cache and invoices modules are wired in.
    """

    gst_data: Optional[dict[str, Any]] = None
    recent_invoices: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Create / Update schemas
# ---------------------------------------------------------------------------

class SupplierCreate(BaseModel):
    """Payload accepted when creating a new supplier.

    Only ``legal_name`` and ``gstin`` are required — every other field is
    optional and can be filled in later (or synced from the Vendor Portal).
    """

    legal_name: str = Field(..., min_length=1, max_length=500)
    gstin: str = Field(..., min_length=15, max_length=15)
    pan: Optional[str] = Field(None, max_length=10)
    state: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    is_msme: bool = False
    msme_category: Optional[str] = Field(None, max_length=10)
    bank_account: Optional[str] = Field(None, max_length=50)
    bank_name: Optional[str] = Field(None, max_length=100)
    ifsc: Optional[str] = Field(None, max_length=11)
    payment_terms: Optional[int] = 30
    risk_score: Optional[float] = None
    status: str = Field("ACTIVE", max_length=20)
    vendor_portal_status: Optional[str] = Field(None, max_length=30)
    contact_email: Optional[str] = Field(None, max_length=255)
    onboarded_date: Optional[str] = Field(None, max_length=20)


class SupplierUpdate(BaseModel):
    """Partial-update payload — every field is optional."""

    legal_name: Optional[str] = Field(None, min_length=1, max_length=500)
    gstin: Optional[str] = Field(None, min_length=15, max_length=15)
    pan: Optional[str] = Field(None, max_length=10)
    state: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    is_msme: Optional[bool] = None
    msme_category: Optional[str] = Field(None, max_length=10)
    bank_account: Optional[str] = Field(None, max_length=50)
    bank_name: Optional[str] = Field(None, max_length=100)
    ifsc: Optional[str] = Field(None, max_length=11)
    payment_terms: Optional[int] = None
    risk_score: Optional[float] = None
    status: Optional[str] = Field(None, max_length=20)
    vendor_portal_status: Optional[str] = Field(None, max_length=30)
    contact_email: Optional[str] = Field(None, max_length=255)
    onboarded_date: Optional[str] = Field(None, max_length=20)
