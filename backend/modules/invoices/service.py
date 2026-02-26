"""
Invoices Module -- Service Layer

Async read/write operations against the ``invoices`` table and related
entities (suppliers, purchase_orders, goods_receipt_notes, gst_records).

The service builds plain dicts that already contain the human-readable codes
(invoice_number, supplier code, po_number, grn_number) instead of UUIDs so
that the Pydantic schemas can serialise them directly without extra
translation.

Public API
----------
- list_invoices(db)                   -> List[dict]
- get_invoice_by_id(db, inv_id)       -> Optional[dict]
- approve_invoice(db, inv_id)         -> dict
- reject_invoice(db, inv_id)          -> dict
- simulate_processing(db, inv_id)     -> dict
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.event_bus import Event, event_bus
from backend.exceptions import NotFoundError, ValidationError
from backend.modules.gst_cache.models import GSTRecord
from backend.modules.invoices.models import Invoice
from backend.modules.purchase_orders.models import (
    GoodsReceiptNote,
    GRNLineItem,
    POLineItem,
    PurchaseOrder,
)
from backend.modules.suppliers.models import Supplier


# ---------------------------------------------------------------------------
# Internal helpers — entity loaders
# ---------------------------------------------------------------------------

async def _load_supplier(
    db: AsyncSession,
    supplier_id: str,
) -> Optional[Supplier]:
    """Fetch a supplier by its UUID primary key."""
    result = await db.execute(
        select(Supplier).where(Supplier.id == supplier_id)
    )
    return result.scalar_one_or_none()


async def _load_po(
    db: AsyncSession,
    po_id: str,
) -> Optional[PurchaseOrder]:
    """Fetch a purchase order by its UUID primary key."""
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == po_id)
    )
    return result.scalar_one_or_none()


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


async def _load_grn(
    db: AsyncSession,
    grn_id: str,
) -> Optional[GoodsReceiptNote]:
    """Fetch a GRN by its UUID primary key."""
    result = await db.execute(
        select(GoodsReceiptNote).where(GoodsReceiptNote.id == grn_id)
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


async def _load_gst_record(
    db: AsyncSession,
    gstin: str,
) -> Optional[GSTRecord]:
    """Fetch a GST cache record by GSTIN."""
    result = await db.execute(
        select(GSTRecord).where(GSTRecord.gstin == gstin)
    )
    return result.scalar_one_or_none()


async def _load_invoice_by_number(
    db: AsyncSession,
    invoice_number: str,
) -> Optional[Invoice]:
    """Look up an invoice by its ``invoice_number`` (e.g. "INV001")."""
    result = await db.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_number)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Internal helpers — dict builders
# ---------------------------------------------------------------------------

def _dt_to_str(dt: Optional[datetime]) -> Optional[str]:
    """Convert a datetime to ISO string, or return None."""
    if dt is None:
        return None
    return dt.isoformat()


def _build_po_line_items(line_items: List[POLineItem]) -> List[Dict[str, Any]]:
    """Convert PO line items to legacy-shaped dicts."""
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
    """Convert GRN line items to legacy-shaped dicts."""
    return [
        {
            "desc": li.description,
            "po_qty": li.po_quantity,
            "received_qty": li.received_quantity,
            "unit": li.unit,
        }
        for li in line_items
    ]


def _build_gst_dict(gst: GSTRecord) -> Dict[str, Any]:
    """Build a dict from a GSTRecord for embedding in the invoice detail."""
    return {
        "gstin": gst.gstin,
        "legal_name": gst.legal_name,
        "status": gst.status,
        "state": gst.state,
        "registration_type": gst.registration_type,
        "last_gstr1_filed": gst.last_gstr1_filed,
        "gstr2b_available": gst.gstr2b_available,
        "gstr2b_period": gst.gstr2b_period,
        "gstr1_compliance": gst.gstr1_compliance,
        "itc_eligible": gst.itc_eligible,
        "last_synced": _dt_to_str(gst.last_synced),
        "sync_source": gst.sync_source,
        "cache_hit_count": gst.cache_hit_count,
        "gstr2b_alert": gst.gstr2b_alert,
        "itc_note": gst.itc_note,
    }


async def _build_invoice_summary(
    db: AsyncSession,
    inv: Invoice,
) -> Dict[str, Any]:
    """Build the flat invoice summary dict used by the list endpoint.

    Resolves FK UUIDs to human-readable codes/names:
      - supplier_id -> supplier.code  (+ supplier.legal_name)
      - po_id       -> purchase_order.po_number
      - grn_id      -> goods_receipt_note.grn_number
    """
    # Resolve supplier
    supplier = await _load_supplier(db, inv.supplier_id)
    supplier_code = supplier.code if supplier else inv.supplier_id
    supplier_name = supplier.legal_name if supplier else "Unknown Supplier"

    # Resolve PO number
    po_number: Optional[str] = None
    if inv.po_id:
        po = await _load_po(db, inv.po_id)
        po_number = po.po_number if po else None

    # Resolve GRN number
    grn_number: Optional[str] = None
    if inv.grn_id:
        grn = await _load_grn(db, inv.grn_id)
        grn_number = grn.grn_number if grn else None

    return {
        "id": inv.invoice_number,
        "invoice_number": inv.invoice_number,
        "supplier_id": supplier_code,
        "supplier_name": supplier_name,
        "po_id": po_number,
        "grn_id": grn_number,
        "invoice_date": inv.invoice_date,
        "due_date": inv.due_date,
        "subtotal": inv.subtotal,
        "gst_rate": inv.gst_rate,
        "gst_amount": inv.gst_amount,
        "tds_rate": inv.tds_rate,
        "tds_amount": inv.tds_amount,
        "total_amount": inv.total_amount,
        "net_payable": inv.net_payable,
        "status": inv.status,
        "match_status": inv.match_status,
        "is_msme_supplier": inv.is_msme_supplier,
        "msme_status": inv.msme_status,
        "fraud_flag": inv.fraud_flag,
        "ebs_ap_status": inv.ebs_ap_status,
        "created_at": _dt_to_str(inv.created_at) if inv.created_at else None,
        "uploaded_by": inv.uploaded_by,
    }


async def _build_invoice_detail(
    db: AsyncSession,
    inv: Invoice,
) -> Dict[str, Any]:
    """Build the full invoice detail dict with nested PO, GRN, and GST data.

    Extends the summary with every column from the model plus nested dicts.
    """
    # Resolve supplier
    supplier = await _load_supplier(db, inv.supplier_id)
    supplier_code = supplier.code if supplier else inv.supplier_id
    supplier_name = supplier.legal_name if supplier else "Unknown Supplier"

    # Resolve PO
    po_number: Optional[str] = None
    po_dict: Optional[Dict[str, Any]] = None
    if inv.po_id:
        po = await _load_po(db, inv.po_id)
        if po:
            po_number = po.po_number
            po_items = await _load_po_line_items(db, po.id)
            po_dict = {
                "id": po.po_number,
                "po_number": po.po_number,
                "amount": po.amount,
                "currency": po.currency,
                "status": po.status,
                "delivery_date": po.delivery_date,
                "items": _build_po_line_items(po_items),
            }

    # Resolve GRN
    grn_number: Optional[str] = None
    grn_dict: Optional[Dict[str, Any]] = None
    if inv.grn_id:
        grn = await _load_grn(db, inv.grn_id)
        if grn:
            grn_number = grn.grn_number
            grn_items = await _load_grn_line_items(db, grn.id)
            grn_dict = {
                "id": grn.grn_number,
                "grn_number": grn.grn_number,
                "po_id": po_number,
                "received_date": grn.received_date,
                "received_by": grn.received_by,
                "status": grn.status,
                "notes": grn.notes,
                "items": _build_grn_line_items(grn_items),
            }

    # Resolve GST record from cache
    gst_dict: Optional[Dict[str, Any]] = None
    if inv.gstin_supplier:
        gst = await _load_gst_record(db, inv.gstin_supplier)
        if gst:
            gst_dict = _build_gst_dict(gst)

    return {
        # Identity
        "id": inv.invoice_number,
        "invoice_number": inv.invoice_number,
        "supplier_id": supplier_code,
        "supplier_name": supplier_name,
        "po_id": po_number,
        "grn_id": grn_number,
        # Dates
        "invoice_date": inv.invoice_date,
        "due_date": inv.due_date,
        # Financial
        "subtotal": inv.subtotal,
        "gst_rate": inv.gst_rate,
        "gst_amount": inv.gst_amount,
        "tds_rate": inv.tds_rate,
        "tds_amount": inv.tds_amount,
        "total_amount": inv.total_amount,
        "net_payable": inv.net_payable,
        # GST identifiers
        "gstin_supplier": inv.gstin_supplier,
        "gstin_buyer": inv.gstin_buyer,
        "hsn_sac": inv.hsn_sac,
        "irn": inv.irn,
        # Status
        "status": inv.status,
        # OCR
        "ocr_confidence": inv.ocr_confidence,
        # GST cache validation
        "gstin_cache_status": inv.gstin_cache_status,
        "gstin_validated_from_cache": inv.gstin_validated_from_cache,
        "gstr2b_itc_eligible": inv.gstr2b_itc_eligible,
        "gstin_cache_age_hours": inv.gstin_cache_age_hours,
        # Matching
        "match_status": inv.match_status,
        "match_variance": inv.match_variance,
        "match_exception_reason": inv.match_exception_reason,
        "match_note": inv.match_note,
        # AI coding agent
        "coding_agent_gl": inv.coding_agent_gl,
        "coding_agent_confidence": inv.coding_agent_confidence,
        "coding_agent_category": inv.coding_agent_category,
        # Fraud
        "fraud_flag": inv.fraud_flag,
        "fraud_reasons": inv.fraud_reasons or [],
        # Cash optimisation
        "cash_opt_suggestion": inv.cash_opt_suggestion,
        # EBS AP
        "ebs_ap_status": inv.ebs_ap_status,
        "ebs_ap_ref": inv.ebs_ap_ref,
        "ebs_posted_at": inv.ebs_posted_at,
        # Approval / rejection
        "approved_by": inv.approved_by,
        "approved_at": inv.approved_at,
        "rejected_by": inv.rejected_by,
        "rejected_at": inv.rejected_at,
        "rejection_reason": inv.rejection_reason,
        # MSME
        "is_msme_supplier": inv.is_msme_supplier,
        "msme_category": inv.msme_category,
        "msme_days_remaining": inv.msme_days_remaining,
        "msme_due_date": inv.msme_due_date,
        "msme_status": inv.msme_status,
        "msme_penalty_amount": inv.msme_penalty_amount,
        # Upload
        "uploaded_by": inv.uploaded_by,
        "created_at": _dt_to_str(inv.created_at) if inv.created_at else None,
        "updated_at": _dt_to_str(inv.updated_at) if inv.updated_at else None,
        # Nested related objects
        "po": po_dict,
        "grn": grn_dict,
        "gst_record": gst_dict,
    }


# ---------------------------------------------------------------------------
# Public API — Read
# ---------------------------------------------------------------------------

async def list_invoices(db: AsyncSession) -> List[Dict[str, Any]]:
    """Return all invoices as legacy-shaped dicts with resolved FK codes.

    Each dict contains human-readable supplier code, PO number, and GRN
    number instead of UUIDs.
    """
    result = await db.execute(
        select(Invoice).order_by(Invoice.invoice_number)
    )
    invoices = list(result.scalars().all())

    summaries: List[Dict[str, Any]] = []
    for inv in invoices:
        summary = await _build_invoice_summary(db, inv)
        summaries.append(summary)

    return summaries


async def get_invoice_by_id(
    db: AsyncSession,
    inv_id: str,
) -> Optional[Dict[str, Any]]:
    """Return a single invoice by its ``invoice_number`` with full detail.

    Includes the full invoice fields PLUS:
      - ``po``: PO dict with line items (or None)
      - ``grn``: GRN dict with line items (or None)
      - ``gst_record``: cached GST record for the supplier GSTIN (or None)
    """
    inv = await _load_invoice_by_number(db, inv_id)
    if inv is None:
        return None

    return await _build_invoice_detail(db, inv)


# ---------------------------------------------------------------------------
# Public API — Write (state transitions)
# ---------------------------------------------------------------------------

async def approve_invoice(
    db: AsyncSession,
    inv_id: str,
) -> Dict[str, Any]:
    """Approve an invoice that is currently in PENDING_APPROVAL or MATCHED status.

    Updates:
      - status -> APPROVED
      - approved_by, approved_at set
      - ebs_ap_status -> PENDING (ready for EBS posting)

    Publishes ``invoice.approved`` event.

    Raises ``NotFoundError`` if the invoice does not exist.
    Raises ``ValidationError`` if the invoice is not in an approvable status.
    """
    inv = await _load_invoice_by_number(db, inv_id)
    if inv is None:
        raise NotFoundError(f"Invoice {inv_id} not found")

    approvable_statuses = {"PENDING_APPROVAL", "MATCHED"}
    if inv.status not in approvable_statuses:
        raise ValidationError(
            f"Cannot approve invoice {inv_id}: current status is {inv.status}, "
            f"expected one of {', '.join(sorted(approvable_statuses))}"
        )

    now = datetime.now(timezone.utc)
    inv.status = "APPROVED"
    inv.approved_by = "Demo Approver"
    inv.approved_at = now
    inv.ebs_ap_status = "PENDING"

    await db.flush()
    await db.refresh(inv)

    # Publish event
    await event_bus.publish(Event(
        name="invoice.approved",
        data={
            "invoice_number": inv.invoice_number,
            "supplier_id": inv.supplier_id,
            "total_amount": inv.total_amount,
            "net_payable": inv.net_payable,
        },
        source="invoices",
    ))

    return await _build_invoice_detail(db, inv)


async def reject_invoice(
    db: AsyncSession,
    inv_id: str,
) -> Dict[str, Any]:
    """Reject an invoice.

    Updates:
      - status -> REJECTED
      - rejected_by, rejected_at, rejection_reason set
      - ebs_ap_status -> BLOCKED

    Publishes ``invoice.rejected`` event.

    Raises ``NotFoundError`` if the invoice does not exist.
    """
    inv = await _load_invoice_by_number(db, inv_id)
    if inv is None:
        raise NotFoundError(f"Invoice {inv_id} not found")

    non_rejectable = {"POSTED_TO_EBS", "PAID", "REJECTED"}
    if inv.status in non_rejectable:
        raise ValidationError(
            f"Cannot reject invoice {inv_id}: current status is {inv.status}"
        )

    now = datetime.now(timezone.utc)
    inv.status = "REJECTED"
    inv.rejected_by = "Demo Approver"
    inv.rejected_at = now
    inv.rejection_reason = "Rejected via demo"
    inv.ebs_ap_status = "BLOCKED"

    await db.flush()
    await db.refresh(inv)

    # Publish event
    await event_bus.publish(Event(
        name="invoice.rejected",
        data={
            "invoice_number": inv.invoice_number,
            "supplier_id": inv.supplier_id,
            "total_amount": inv.total_amount,
            "reason": inv.rejection_reason,
        },
        source="invoices",
    ))

    return await _build_invoice_detail(db, inv)


async def simulate_processing(
    db: AsyncSession,
    inv_id: str,
) -> Dict[str, Any]:
    """Simulate the invoice processing pipeline by advancing status one step.

    Status progression:
        CAPTURED -> EXTRACTED -> VALIDATED -> MATCHED -> PENDING_APPROVAL

    At each step, simulated metadata is populated:
      - CAPTURED -> EXTRACTED: OCR confidence set
      - EXTRACTED -> VALIDATED: GST cache fields set
      - VALIDATED -> MATCHED: match engine fields set
      - MATCHED -> PENDING_APPROVAL: AI coding agent fields set

    Publishes a status-specific event at each step.

    Raises ``NotFoundError`` if the invoice does not exist.
    Raises ``ValidationError`` if the invoice cannot advance further.
    """
    inv = await _load_invoice_by_number(db, inv_id)
    if inv is None:
        raise NotFoundError(f"Invoice {inv_id} not found")

    progression = {
        "CAPTURED": "EXTRACTED",
        "EXTRACTED": "VALIDATED",
        "VALIDATED": "MATCHED",
        "MATCHED": "PENDING_APPROVAL",
    }

    next_status = progression.get(inv.status)
    if next_status is None:
        raise ValidationError(
            f"Invoice {inv_id} cannot advance further: current status is {inv.status}"
        )

    old_status = inv.status
    inv.status = next_status

    # Populate simulated metadata based on the transition
    if old_status == "CAPTURED":
        # Simulate OCR extraction
        inv.ocr_confidence = 95.2

    elif old_status == "EXTRACTED":
        # Simulate GST validation from cache
        inv.gstin_cache_status = "VALID"
        inv.gstin_validated_from_cache = True
        inv.gstr2b_itc_eligible = True
        inv.gstin_cache_age_hours = 1.5

    elif old_status == "VALIDATED":
        # Simulate matching engine
        if inv.po_id and inv.grn_id:
            inv.match_status = "3WAY_MATCH_PASSED"
            inv.match_variance = 0.0
            inv.match_note = (
                "PO amount matches invoice. GRN confirms delivery. "
                "3-way match passed."
            )
        elif inv.po_id:
            inv.match_status = "2WAY_MATCH_PASSED"
            inv.match_variance = 0.0
            inv.match_note = "PO amount matches invoice. 2-way match passed."
        else:
            inv.match_status = "3WAY_MATCH_EXCEPTION"
            inv.match_variance = 0.0
            inv.match_exception_reason = (
                "No matching PO found. Invoice submitted without "
                "purchase order reference."
            )
            inv.match_note = (
                "Non-PO invoice. Requires manual approval per policy."
            )

    elif old_status == "MATCHED":
        # Simulate AI coding agent
        inv.coding_agent_gl = "6100"
        inv.coding_agent_confidence = 0.92
        inv.coding_agent_category = "General Services"

    await db.flush()
    await db.refresh(inv)

    # Publish event
    event_name = f"invoice.{next_status.lower().replace('_', '-')}"
    await event_bus.publish(Event(
        name=event_name,
        data={
            "invoice_number": inv.invoice_number,
            "old_status": old_status,
            "new_status": next_status,
        },
        source="invoices",
    ))

    return await _build_invoice_detail(db, inv)
