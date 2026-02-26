"""
Invoices Module -- FastAPI Routes

Prefix: ``/api/invoices``

All endpoints use the ``invoice_number`` (e.g. "INV001") as the path
identifier, matching what the legacy frontend sends.

Endpoints
---------
GET  /api/invoices              - List all invoices (summary shape)
GET  /api/invoices/{inv_id}     - Invoice detail with PO, GRN, GST data
PATCH /api/invoices/{inv_id}/approve           - Approve an invoice
PATCH /api/invoices/{inv_id}/reject            - Reject an invoice
POST  /api/invoices/{inv_id}/simulate-processing - Advance status one step
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user
from backend.exceptions import NotFoundError
from backend.modules.invoices.schemas import (
    InvoiceDetailResponse,
    InvoiceListItem,
)
from backend.modules.invoices import service

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


# ---------------------------------------------------------------------------
# GET  /api/invoices
# ---------------------------------------------------------------------------

@router.get("", response_model=List[InvoiceListItem])
async def list_invoices(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> List[InvoiceListItem]:
    """Return all invoices with resolved supplier/PO/GRN codes.

    Optionally filter by ``status`` query parameter.
    """
    inv_dicts = await service.list_invoices(db)
    if status:
        inv_dicts = [d for d in inv_dicts if d.get("status") == status]
    return [InvoiceListItem.model_validate(d) for d in inv_dicts]


# ---------------------------------------------------------------------------
# GET  /api/invoices/{inv_id}
# ---------------------------------------------------------------------------

@router.get("/{inv_id}", response_model=InvoiceDetailResponse)
async def get_invoice(
    inv_id: str,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> InvoiceDetailResponse:
    """Return a single invoice by its invoice_number (e.g. "INV001").

    Includes nested PO (with line items), GRN (with line items), and the
    cached GST record for the supplier GSTIN.
    """
    detail = await service.get_invoice_by_id(db, inv_id)
    if detail is None:
        raise NotFoundError(f"Invoice {inv_id} not found")

    return InvoiceDetailResponse.model_validate(detail)


# ---------------------------------------------------------------------------
# PATCH  /api/invoices/{inv_id}/approve
# ---------------------------------------------------------------------------

@router.patch("/{inv_id}/approve", response_model=InvoiceDetailResponse)
async def approve_invoice(
    inv_id: str,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> InvoiceDetailResponse:
    """Approve an invoice that is currently PENDING_APPROVAL or MATCHED.

    Sets status to APPROVED, records approver, and marks EBS AP as PENDING.
    Returns 422 (ValidationError) if the invoice is not in an approvable
    status.
    """
    detail = await service.approve_invoice(db, inv_id)
    return InvoiceDetailResponse.model_validate(detail)


# ---------------------------------------------------------------------------
# PATCH  /api/invoices/{inv_id}/reject
# ---------------------------------------------------------------------------

@router.patch("/{inv_id}/reject", response_model=InvoiceDetailResponse)
async def reject_invoice(
    inv_id: str,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> InvoiceDetailResponse:
    """Reject an invoice.

    Sets status to REJECTED, records rejection reason, and blocks EBS AP.
    Cannot reject invoices that are already POSTED_TO_EBS, PAID, or REJECTED.
    """
    detail = await service.reject_invoice(db, inv_id)
    return InvoiceDetailResponse.model_validate(detail)


# ---------------------------------------------------------------------------
# POST  /api/invoices/{inv_id}/simulate-processing
# ---------------------------------------------------------------------------

@router.post("/{inv_id}/simulate-processing", response_model=InvoiceDetailResponse)
async def simulate_processing(
    inv_id: str,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> InvoiceDetailResponse:
    """Simulate the invoice processing pipeline by advancing status one step.

    Progression: CAPTURED -> EXTRACTED -> VALIDATED -> MATCHED -> PENDING_APPROVAL

    Each step populates simulated metadata (OCR confidence, GST validation,
    matching results, AI coding agent output).  Returns 422 if the invoice
    cannot advance further.
    """
    detail = await service.simulate_processing(db, inv_id)
    return InvoiceDetailResponse.model_validate(detail)
