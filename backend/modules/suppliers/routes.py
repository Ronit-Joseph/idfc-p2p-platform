"""
Suppliers Module — FastAPI Routes

Prefix: ``/api/suppliers``

All endpoints use the supplier ``code`` (e.g. "SUP001") as the path
identifier, matching what the frontend sends.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user
from backend.exceptions import NotFoundError
from backend.modules.suppliers.schemas import (
    SupplierCreate,
    SupplierDetailResponse,
    SupplierResponse,
    SupplierUpdate,
)
from backend.modules.suppliers import service

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


# ---------------------------------------------------------------------------
# GET  /api/suppliers
# ---------------------------------------------------------------------------

@router.get("", response_model=List[SupplierResponse])
async def list_suppliers(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> List[SupplierResponse]:
    """Return all suppliers."""
    suppliers = await service.list_suppliers(db)
    return [SupplierResponse.model_validate(s) for s in suppliers]


# ---------------------------------------------------------------------------
# GET  /api/suppliers/{sid}
# ---------------------------------------------------------------------------

@router.get("/{sid}", response_model=SupplierDetailResponse)
async def get_supplier(
    sid: str,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> SupplierDetailResponse:
    """Return a single supplier by its code (e.g. "SUP001").

    ``gst_data`` and ``recent_invoices`` are placeholders that will be
    populated once the GST-cache and invoices modules are wired in.
    """
    supplier = await service.get_supplier_by_code(db, sid)
    if supplier is None:
        raise NotFoundError(f"Supplier {sid} not found")

    # Build the detail response.  Cross-module data (GST cache, invoices)
    # will be joined here once those modules exist.
    gst_data: dict | None = None
    recent_invoices: list[dict] = []

    detail = SupplierDetailResponse.model_validate(supplier)
    detail.gst_data = gst_data
    detail.recent_invoices = recent_invoices
    return detail


# ---------------------------------------------------------------------------
# POST /api/suppliers
# ---------------------------------------------------------------------------

@router.post("", response_model=SupplierResponse, status_code=201)
async def create_supplier(
    payload: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> SupplierResponse:
    """Create a new supplier.  A code (e.g. "SUP016") is auto-generated."""
    supplier = await service.create_supplier(db, payload)
    return SupplierResponse.model_validate(supplier)


# ---------------------------------------------------------------------------
# PATCH /api/suppliers/{sid}
# ---------------------------------------------------------------------------

@router.patch("/{sid}", response_model=SupplierResponse)
async def update_supplier(
    sid: str,
    payload: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> SupplierResponse:
    """Partially update a supplier identified by its code."""
    supplier = await service.update_supplier(db, sid, payload)
    return SupplierResponse.model_validate(supplier)
