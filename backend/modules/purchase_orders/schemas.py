"""
Purchase Orders Module — Pydantic Schemas

Defines response models for the Purchase Orders API.

IMPORTANT: The frontend uses ``po_number`` (e.g. "PO2024-001") as the
identifier in all API calls.  POResponse therefore exposes an ``id``
field that maps to ``po_number`` so the frontend contract is never
broken — the actual UUID primary key is excluded from responses.

Field renames in line-item responses:
  - description → desc
  - quantity → qty
  - grn_quantity → grn_qty
  - po_quantity → po_qty
  - received_quantity → received_qty
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Line-item response schemas
# ---------------------------------------------------------------------------

class POLineItemResponse(BaseModel):
    """Single PO line item — field names match the legacy API contract."""

    model_config = ConfigDict(from_attributes=True)

    desc: str = Field(..., description="Line item description")
    qty: float = Field(..., description="Ordered quantity")
    unit: Optional[str] = None
    unit_price: float = 0
    total: float = 0
    grn_qty: float = Field(0, description="Quantity received via GRN")

    @model_validator(mode="before")
    @classmethod
    def _rename_fields(cls, data: Any) -> Any:
        """Map ORM/dict field names to the legacy API short names."""
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
        # grn_quantity → grn_qty
        if "grn_quantity" in d and "grn_qty" not in d:
            d["grn_qty"] = d.pop("grn_quantity")

        return d


class GRNLineItemResponse(BaseModel):
    """Single GRN line item — field names match the legacy API contract."""

    model_config = ConfigDict(from_attributes=True)

    desc: str = Field(..., description="Line item description")
    po_qty: float = Field(0, description="Original PO quantity")
    received_qty: float = Field(0, description="Quantity actually received")
    unit: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _rename_fields(cls, data: Any) -> Any:
        """Map ORM/dict field names to the legacy API short names."""
        if hasattr(data, "__dict__"):
            d = {k: v for k, v in data.__dict__.items() if not k.startswith("_")}
        elif isinstance(data, dict):
            d = dict(data)
        else:
            return data

        if "description" in d and "desc" not in d:
            d["desc"] = d.pop("description")
        if "po_quantity" in d and "po_qty" not in d:
            d["po_qty"] = d.pop("po_quantity")
        if "received_quantity" in d and "received_qty" not in d:
            d["received_qty"] = d.pop("received_quantity")

        return d


# ---------------------------------------------------------------------------
# GRN response schema
# ---------------------------------------------------------------------------

class GRNResponse(BaseModel):
    """Goods Receipt Note — ``id`` is the human-readable ``grn_number``."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="grn_number (e.g. GRN2024-001)")
    po_id: str = Field(..., description="po_number of the parent PO")
    grn_number: str
    received_date: Optional[str] = None
    received_by: Optional[str] = None
    status: str = "PARTIAL"
    notes: Optional[str] = None
    items: List[GRNLineItemResponse] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _translate_ids(cls, data: Any) -> Any:
        """Ensure ``id`` equals ``grn_number`` and ``po_id`` is the po_number."""
        if hasattr(data, "__dict__"):
            d = {k: v for k, v in data.__dict__.items() if not k.startswith("_")}
        elif isinstance(data, dict):
            d = dict(data)
        else:
            return data

        # id → grn_number
        if "grn_number" in d:
            d["id"] = d["grn_number"]

        return d


# ---------------------------------------------------------------------------
# PO response schemas
# ---------------------------------------------------------------------------

class POResponse(BaseModel):
    """Purchase Order summary — used in list endpoint.

    ``id`` is always equal to ``po_number`` (e.g. "PO2024-001").
    ``pr_id`` is the PR's ``pr_number``, ``supplier_id`` is the supplier ``code``,
    and ``grn_id`` is the GRN's ``grn_number``.

    The service layer is responsible for building a dict with these
    human-readable codes already in place.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Same as po_number (e.g. PO2024-001)")
    po_number: str
    pr_id: Optional[str] = Field(None, description="PR number (e.g. PR2024-001)")
    supplier_id: str = Field(..., description="Supplier code (e.g. SUP001)")
    supplier_name: str = Field(..., description="Supplier legal name")
    amount: float
    currency: str = "INR"
    status: str = "DRAFT"
    delivery_date: Optional[str] = None
    dispatch_date: Optional[datetime] = None
    acknowledged_date: Optional[datetime] = None
    grn_id: Optional[str] = Field(None, description="GRN number (e.g. GRN2024-001)")
    ebs_commitment_status: Optional[str] = None
    ebs_commitment_ref: Optional[str] = None
    items: List[POLineItemResponse] = Field(default_factory=list)


class PODetailResponse(POResponse):
    """Extended PO response — includes full GRN, PR, and invoices data.

    Used by the single-PO detail endpoint.
    """

    grn: Optional[GRNResponse] = None
    pr: Optional[Dict[str, Any]] = None
    invoices: List[Dict[str, Any]] = Field(default_factory=list)
