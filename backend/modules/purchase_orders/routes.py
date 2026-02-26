"""
Purchase Orders Module — FastAPI Routes

Prefix: ``/api/purchase-orders``

All endpoints use the PO ``po_number`` (e.g. "PO2024-001") as the path
identifier, matching what the frontend sends.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user
from backend.exceptions import NotFoundError
from backend.modules.purchase_orders.schemas import (
    PODetailResponse,
    POResponse,
)
from backend.modules.purchase_orders import service

router = APIRouter(prefix="/api/purchase-orders", tags=["purchase-orders"])


# ---------------------------------------------------------------------------
# GET  /api/purchase-orders
# ---------------------------------------------------------------------------

@router.get("", response_model=List[POResponse])
async def list_purchase_orders(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> List[POResponse]:
    """Return all purchase orders with line items and resolved codes."""
    po_dicts = await service.list_pos(db)
    return [POResponse.model_validate(d) for d in po_dicts]


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
