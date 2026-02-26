"""
Purchase Orders Module — Service Layer

Async read operations against the ``purchase_orders``, ``po_line_items``,
``goods_receipt_notes``, and ``grn_line_items`` tables.

The service builds plain dicts that already contain the human-readable codes
(po_number, pr_number, supplier code, grn_number) instead of UUIDs so that
the Pydantic schemas can serialise them directly without extra translation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.purchase_orders.models import (
    GoodsReceiptNote,
    GRNLineItem,
    POLineItem,
    PurchaseOrder,
)
from backend.modules.purchase_requests.models import PurchaseRequest
from backend.modules.suppliers.models import Supplier
from backend.modules.invoices.models import Invoice


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_po_line_items(line_items: List[POLineItem]) -> List[Dict[str, Any]]:
    """Convert a list of POLineItem ORM objects to legacy-shaped dicts."""
    return [
        {
            "desc": li.description,
            "qty": li.quantity,
            "unit": li.unit,
            "unit_price": li.unit_price,
            "total": li.total,
            "grn_qty": li.grn_quantity,
        }
        for li in sorted(line_items, key=lambda x: x.sort_order)
    ]


def _build_grn_line_items(line_items: List[GRNLineItem]) -> List[Dict[str, Any]]:
    """Convert a list of GRNLineItem ORM objects to legacy-shaped dicts."""
    return [
        {
            "desc": li.description,
            "po_qty": li.po_quantity,
            "received_qty": li.received_quantity,
            "unit": li.unit,
        }
        for li in line_items
    ]


def _build_grn_dict(
    grn: GoodsReceiptNote,
    grn_items: List[GRNLineItem],
    po_number: str,
) -> Dict[str, Any]:
    """Build the legacy GRN response dict."""
    return {
        "id": grn.grn_number,
        "po_id": po_number,
        "grn_number": grn.grn_number,
        "received_date": grn.received_date,
        "received_by": grn.received_by,
        "status": grn.status,
        "notes": grn.notes,
        "items": _build_grn_line_items(grn_items),
    }


async def _load_po_line_items(
    db: AsyncSession,
    po_id: str,
) -> List[POLineItem]:
    """Fetch all line items for a PO, ordered by sort_order."""
    result = await db.execute(
        select(POLineItem)
        .where(POLineItem.po_id == po_id)
        .order_by(POLineItem.sort_order)
    )
    return list(result.scalars().all())


async def _load_grn_for_po(
    db: AsyncSession,
    po_id: str,
) -> Optional[GoodsReceiptNote]:
    """Fetch the first GRN linked to a PO (if any)."""
    result = await db.execute(
        select(GoodsReceiptNote).where(GoodsReceiptNote.po_id == po_id)
    )
    return result.scalar_one_or_none()


async def _load_grn_line_items(
    db: AsyncSession,
    grn_id: str,
) -> List[GRNLineItem]:
    """Fetch all line items for a GRN."""
    result = await db.execute(
        select(GRNLineItem).where(GRNLineItem.grn_id == grn_id)
    )
    return list(result.scalars().all())


async def _load_supplier(
    db: AsyncSession,
    supplier_id: str,
) -> Optional[Supplier]:
    """Fetch a supplier by its UUID primary key."""
    result = await db.execute(
        select(Supplier).where(Supplier.id == supplier_id)
    )
    return result.scalar_one_or_none()


async def _load_pr(
    db: AsyncSession,
    pr_id: str,
) -> Optional[PurchaseRequest]:
    """Fetch a purchase request by its UUID primary key."""
    result = await db.execute(
        select(PurchaseRequest).where(PurchaseRequest.id == pr_id)
    )
    return result.scalar_one_or_none()


async def _load_invoices_for_po(
    db: AsyncSession,
    po_id: str,
) -> List[Invoice]:
    """Fetch all invoices linked to a PO."""
    result = await db.execute(
        select(Invoice).where(Invoice.po_id == po_id)
    )
    return list(result.scalars().all())


async def _build_po_summary(
    db: AsyncSession,
    po: PurchaseOrder,
) -> Dict[str, Any]:
    """Build the flat PO summary dict used by the list endpoint.

    Resolves FK UUIDs to human-readable codes/names:
      - supplier_id → supplier.code
      - pr_id → purchase_request.pr_number
      - grn_id → goods_receipt_note.grn_number
    """
    # Load related entities
    supplier = await _load_supplier(db, po.supplier_id)
    supplier_code = supplier.code if supplier else po.supplier_id
    supplier_name = supplier.legal_name if supplier else "Unknown Supplier"

    pr_number: Optional[str] = None
    if po.pr_id:
        pr = await _load_pr(db, po.pr_id)
        pr_number = pr.pr_number if pr else None

    grn = await _load_grn_for_po(db, po.id)
    grn_number: Optional[str] = grn.grn_number if grn else None

    line_items = await _load_po_line_items(db, po.id)

    return {
        "id": po.po_number,
        "po_number": po.po_number,
        "pr_id": pr_number,
        "supplier_id": supplier_code,
        "supplier_name": supplier_name,
        "amount": po.amount,
        "currency": po.currency,
        "status": po.status,
        "delivery_date": po.delivery_date,
        "dispatch_date": po.dispatch_date,
        "acknowledged_date": po.acknowledged_date,
        "grn_id": grn_number,
        "ebs_commitment_status": po.ebs_commitment_status,
        "ebs_commitment_ref": po.ebs_commitment_ref,
        "items": _build_po_line_items(line_items),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def list_pos(db: AsyncSession) -> List[Dict[str, Any]]:
    """Return all Purchase Orders as legacy-shaped dicts.

    Each PO dict contains resolved human-readable codes for supplier,
    PR, and GRN — plus the nested ``items`` array.
    """
    result = await db.execute(
        select(PurchaseOrder).order_by(PurchaseOrder.po_number)
    )
    pos = list(result.scalars().all())

    summaries: List[Dict[str, Any]] = []
    for po in pos:
        summary = await _build_po_summary(db, po)
        summaries.append(summary)

    return summaries


async def get_po_by_number(
    db: AsyncSession,
    po_number: str,
) -> Optional[Dict[str, Any]]:
    """Return a single PO by its ``po_number`` with full detail.

    Includes the flat PO summary fields PLUS:
      - ``grn``: full GRN dict with line items (or None)
      - ``pr``: PR dict (or None)
      - ``invoices``: list of invoice dicts
    """
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_number == po_number)
    )
    po = result.scalar_one_or_none()
    if po is None:
        return None

    # Build the base summary (resolves codes, loads line items)
    detail = await _build_po_summary(db, po)

    # ── GRN with line items ────────────────────────────────────
    grn = await _load_grn_for_po(db, po.id)
    grn_dict: Optional[Dict[str, Any]] = None
    if grn:
        grn_items = await _load_grn_line_items(db, grn.id)
        grn_dict = _build_grn_dict(grn, grn_items, po.po_number)
    detail["grn"] = grn_dict

    # ── Purchase Request ───────────────────────────────────────
    pr_dict: Optional[Dict[str, Any]] = None
    if po.pr_id:
        pr = await _load_pr(db, po.pr_id)
        if pr:
            pr_dict = {
                k: v for k, v in pr.__dict__.items() if not k.startswith("_")
            }
    detail["pr"] = pr_dict

    # ── Invoices linked to this PO ─────────────────────────────
    invoices = await _load_invoices_for_po(db, po.id)
    detail["invoices"] = [
        {k: v for k, v in inv.__dict__.items() if not k.startswith("_")}
        for inv in invoices
    ]

    return detail
