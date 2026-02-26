"""
MSME Compliance Module — Pydantic Schemas

Response models for the Section 43B(h) compliance dashboard endpoint.

The ``MSMEComplianceResponse`` wraps:
  - ``MSMESummary``: aggregate counts and penalty exposure
  - ``List[MSMEInvoiceResponse]``: individual MSME-flagged invoices
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class MSMEInvoiceResponse(BaseModel):
    """Single MSME invoice in the compliance dashboard.

    The ``id`` field is set to the invoice_number (matching the invoice module
    convention where human-readable IDs are used in API responses).
    """

    id: str  # invoice_number (e.g. "INV002")
    invoice_number: str
    supplier_name: str
    msme_category: Optional[str] = None
    amount: float
    due_date: Optional[str] = None
    msme_due_date: Optional[str] = None
    days_remaining: Optional[int] = None
    status: Optional[str] = None
    penalty_amount: Optional[float] = 0


class MSMESummary(BaseModel):
    """Aggregate MSME compliance metrics."""

    total_msme_invoices: int
    on_track: int
    at_risk: int
    breached: int
    total_penalty_exposure: float
    avg_days_remaining: float


class MSMEComplianceResponse(BaseModel):
    """Top-level response for GET /api/msme-compliance."""

    summary: MSMESummary
    invoices: List[MSMEInvoiceResponse]
