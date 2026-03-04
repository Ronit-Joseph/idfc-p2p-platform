"""
Purchase Orders Module — FastAPI Routes

Prefix: ``/api/purchase-orders``

All endpoints use the PO ``po_number`` (e.g. "PO2024-001") as the path
identifier, matching what the frontend sends.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user, require_role, paginate
from backend.exceptions import NotFoundError
from backend.modules.purchase_orders.schemas import (
    GRNCreate,
    GRNResponse,
    PODetailResponse,
    POResponse,
)
from backend.modules.purchase_orders import service

router = APIRouter(prefix="/api/purchase-orders", tags=["purchase-orders"])


# ---------------------------------------------------------------------------
# GET  /api/purchase-orders
# ---------------------------------------------------------------------------

@router.get("")
async def list_purchase_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
):
    """Return all purchase orders with line items and resolved codes."""
    po_dicts = await service.list_pos(db)
    return paginate([POResponse.model_validate(d) for d in po_dicts], skip, limit)


# ---------------------------------------------------------------------------
# GET  /api/purchase-orders/{po_id}
# ---------------------------------------------------------------------------

@router.get("/{po_id}", response_model=PODetailResponse)
async def get_purchase_order(
    po_id: str,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> PODetailResponse:
    """Return a single purchase order by its po_number (e.g. "PO2024-001").

    Includes the full GRN (with line items), the originating PR, and any
    linked invoices.
    """
    detail = await service.get_po_by_number(db, po_id)
    if detail is None:
        raise NotFoundError(f"Purchase order {po_id} not found")

    return PODetailResponse.model_validate(detail)


# ---------------------------------------------------------------------------
# POST /api/purchase-orders/{po_id}/grn
# ---------------------------------------------------------------------------

@router.post("/{po_id}/grn", response_model=GRNResponse, status_code=201)
async def create_grn(
    po_id: str,
    body: GRNCreate,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role("PROCUREMENT_MANAGER")),
) -> GRNResponse:
    """Create a Goods Receipt Note for a purchase order.

    If no line items are provided, a full receipt of all PO items is assumed.
    """
    from fastapi import HTTPException
    try:
        result = await service.create_grn(
            db, po_id,
            data=body.model_dump(),
            received_by=user.get("name", "Unknown"),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return GRNResponse.model_validate(result)
