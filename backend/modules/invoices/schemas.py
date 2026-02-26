"""
Invoices Module -- Pydantic Schemas

Defines response models for the Invoices API.

IMPORTANT: The legacy frontend uses ``invoice_number`` (e.g. "INV001") as the
``id`` field in all API calls.  InvoiceListItem therefore exposes an ``id``
field that maps to the database ``invoice_number`` column so that the frontend
contract is never broken -- the actual UUID primary key is excluded from
responses.

FK resolution performed by the service layer:
    - supplier_id  UUID -> supplier.code  (response field: supplier_id)
    - po_id        UUID -> po_number      (response field: po_id)
    - grn_id       UUID -> grn_number     (response field: grn_id)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Invoice list item
# ---------------------------------------------------------------------------

class InvoiceListItem(BaseModel):
    """Shape for GET /api/invoices list endpoint.

    ``id`` is always equal to ``invoice_number`` (e.g. "INV001") -- the
    frontend expects this.  The service layer resolves FK UUIDs to
    human-readable codes before validation.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Same as invoice_number (e.g. INV001)")
    invoice_number: str
    supplier_id: str = Field(..., description="Supplier code (e.g. SUP001)")
    supplier_name: str = Field(..., description="Supplier legal name")
    po_id: Optional[str] = Field(None, description="PO number (e.g. PO2024-001)")
    grn_id: Optional[str] = Field(None, description="GRN number (e.g. GRN2024-001)")
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    subtotal: float = 0
    gst_rate: Optional[float] = None
    gst_amount: float = 0
    tds_rate: Optional[float] = None
    tds_amount: float = 0
    total_amount: float = 0
    net_payable: float = 0
    status: str = "CAPTURED"
    match_status: Optional[str] = None
    is_msme_supplier: bool = False
    msme_status: Optional[str] = None
    fraud_flag: bool = False
    ebs_ap_status: str = "NOT_STARTED"
    created_at: Optional[str] = None
    uploaded_by: Optional[str] = None


# ---------------------------------------------------------------------------
# Invoice detail response
# ---------------------------------------------------------------------------

class InvoiceDetailResponse(BaseModel):
    """Full invoice detail with resolved FKs and nested subsystem data.

    Returned by the single-invoice GET endpoint.  Includes every column from
    the Invoice model plus nested dicts for the related PO, GRN, GST record,
    and supplier name.

    ``id`` is always ``invoice_number``.
    """

    model_config = ConfigDict(from_attributes=True)

    # -- Identity --
    id: str = Field(..., description="Same as invoice_number")
    invoice_number: str
    supplier_id: str = Field(..., description="Supplier code (e.g. SUP001)")
    supplier_name: str = Field(..., description="Supplier legal name")
    po_id: Optional[str] = Field(None, description="PO number (e.g. PO2024-001)")
    grn_id: Optional[str] = Field(None, description="GRN number (e.g. GRN2024-001)")

    # -- Dates --
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None

    # -- Financial --
    subtotal: float = 0
    gst_rate: Optional[float] = None
    gst_amount: float = 0
    tds_rate: Optional[float] = None
    tds_amount: float = 0
    total_amount: float = 0
    net_payable: float = 0

    # -- GST identifiers --
    gstin_supplier: Optional[str] = None
    gstin_buyer: Optional[str] = None
    hsn_sac: Optional[str] = None
    irn: Optional[str] = None

    # -- Status --
    status: str = "CAPTURED"

    # -- OCR --
    ocr_confidence: Optional[float] = None

    # -- GST cache validation --
    gstin_cache_status: Optional[str] = None
    gstin_validated_from_cache: bool = False
    gstr2b_itc_eligible: Optional[bool] = None
    gstin_cache_age_hours: Optional[float] = None

    # -- Matching --
    match_status: Optional[str] = None
    match_variance: Optional[float] = None
    match_exception_reason: Optional[str] = None
    match_note: Optional[str] = None

    # -- AI coding agent --
    coding_agent_gl: Optional[str] = None
    coding_agent_confidence: Optional[float] = None
    coding_agent_category: Optional[str] = None

    # -- Fraud --
    fraud_flag: bool = False
    fraud_reasons: Optional[List[str]] = Field(default_factory=list)

    # -- Cash optimisation --
    cash_opt_suggestion: Optional[str] = None

    # -- EBS AP --
    ebs_ap_status: str = "NOT_STARTED"
    ebs_ap_ref: Optional[str] = None
    ebs_posted_at: Optional[datetime] = None

    # -- Approval / rejection --
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # -- MSME --
    is_msme_supplier: bool = False
    msme_category: Optional[str] = None
    msme_days_remaining: Optional[int] = None
    msme_due_date: Optional[str] = None
    msme_status: Optional[str] = None
    msme_penalty_amount: Optional[float] = 0

    # -- Upload --
    uploaded_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # -- Nested related objects (populated by detail endpoint) --
    po: Optional[Dict[str, Any]] = None
    grn: Optional[Dict[str, Any]] = None
    gst_record: Optional[Dict[str, Any]] = None
