"""
Matching Module — Service Layer

2-way (Invoice vs PO) and 3-way (Invoice vs PO vs GRN) matching engine.
Creates match results, raises exceptions, and supports manual resolution.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.event_bus import Event, event_bus
from backend.modules.matching.models import MatchResult, MatchingException
from backend.modules.invoices.models import Invoice
from backend.modules.purchase_orders.models import PurchaseOrder, POLineItem, GoodsReceiptNote, GRNLineItem
from backend.modules.suppliers.models import Supplier


# ---------------------------------------------------------------------------
# Run matching
# ---------------------------------------------------------------------------

async def run_match(
    db: AsyncSession,
    invoice_id: str,
    match_type: str = "3WAY",
) -> Dict[str, Any]:
    """Run 2-way or 3-way matching for an invoice.

    2WAY: Invoice total vs PO total — checks price variance.
    3WAY: Invoice vs PO vs GRN — checks price AND quantity.
    """
    # Load invoice by invoice_number
    result = await db.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_id)
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise ValueError(f"Invoice {invoice_id} not found")

    # Check if already matched
    existing = await db.execute(
        select(MatchResult).where(MatchResult.invoice_id == inv.id)
    )
    if existing.scalar_one_or_none():
        raise ValueError(f"Invoice {invoice_id} already has a match result")

    exception_reasons = []
    variance_pct = 0.0
    status = "PASSED"

    # No PO → immediate exception
    if not inv.po_id:
        status = "EXCEPTION"
        exception_reasons.append("No matching PO found")
    else:
        # Load PO
        po_result = await db.execute(
            select(PurchaseOrder).where(PurchaseOrder.id == inv.po_id)
        )
        po = po_result.scalar_one_or_none()

        if po:
            # 2-way: price variance
            if po.amount and po.amount > 0:
                variance_pct = abs(inv.subtotal - po.amount) / po.amount * 100
                if variance_pct > 5.0:  # 5% tolerance
                    status = "EXCEPTION"
                    exception_reasons.append(
                        f"Price variance {variance_pct:.1f}% exceeds 5% tolerance"
                    )

            # 3-way: quantity check
            if match_type == "3WAY" and inv.grn_id:
                grn_result = await db.execute(
                    select(GoodsReceiptNote).where(GoodsReceiptNote.id == inv.grn_id)
                )
                grn = grn_result.scalar_one_or_none()
                if grn and grn.status == "PARTIAL":
                    if status != "EXCEPTION":
                        status = "EXCEPTION"
                    exception_reasons.append(
                        "GRN shows partial delivery — quantity mismatch"
                    )
            elif match_type == "3WAY" and not inv.grn_id:
                if status != "EXCEPTION":
                    status = "EXCEPTION"
                exception_reasons.append("No GRN found for 3-way match")

    # Fraud check
    if inv.fraud_flag:
        status = "BLOCKED_FRAUD"
        exception_reasons.append("Invoice flagged for fraud")

    note = "; ".join(exception_reasons) if exception_reasons else f"{match_type} match passed"

    # Save match result
    mr = MatchResult(
        invoice_id=inv.id,
        match_type=match_type,
        status=status,
        variance_pct=round(variance_pct, 2),
        exception_reason="; ".join(exception_reasons) if exception_reasons else None,
        note=note,
    )
    db.add(mr)
    await db.flush()

    # Create exception entry if needed
    exception_dict = None
    if status in ("EXCEPTION", "BLOCKED_FRAUD"):
        exc_type = "PRICE_VARIANCE" if variance_pct > 5.0 else "NO_PO" if not inv.po_id else "QUANTITY_MISMATCH"
        if inv.fraud_flag:
            exc_type = "FRAUD_BLOCK"
        severity = "CRITICAL" if inv.fraud_flag else "HIGH" if variance_pct > 10 else "MEDIUM"

        me = MatchingException(
            match_result_id=mr.id,
            invoice_id=inv.id,
            exception_type=exc_type,
            severity=severity,
            description="; ".join(exception_reasons),
        )
        db.add(me)
        await db.flush()
        exception_dict = _exception_to_dict(me)

    # Update invoice match fields
    inv.match_status = f"{match_type}_MATCH_{status}"
    inv.match_variance = round(variance_pct, 2)
    inv.match_exception_reason = "; ".join(exception_reasons) if exception_reasons else None
    inv.match_note = note

    await db.commit()

    await event_bus.publish(Event(
        name=f"matching.{status.lower()}",
        data={"invoice_id": invoice_id, "match_type": match_type, "status": status},
        source="matching",
    ))

    return _result_to_dict(mr, inv.invoice_number)


# ---------------------------------------------------------------------------
# List & query
# ---------------------------------------------------------------------------

async def list_match_results(db: AsyncSession) -> List[Dict[str, Any]]:
    """List all match results with invoice numbers."""
    result = await db.execute(
        select(MatchResult, Invoice.invoice_number, Supplier.legal_name)
        .join(Invoice, Invoice.id == MatchResult.invoice_id)
        .outerjoin(Supplier, Supplier.id == Invoice.supplier_id)
        .order_by(MatchResult.created_at.desc())
    )
    return [
        {**_result_to_dict(mr, inv_num), "supplier_name": sup_name}
        for mr, inv_num, sup_name in result.all()
    ]


async def list_exceptions(
    db: AsyncSession,
    open_only: bool = True,
) -> List[Dict[str, Any]]:
    """List matching exceptions, optionally only unresolved ones."""
    q = (
        select(MatchingException, Invoice.invoice_number, Supplier.legal_name)
        .join(Invoice, Invoice.id == MatchingException.invoice_id)
        .outerjoin(Supplier, Supplier.id == Invoice.supplier_id)
    )
    if open_only:
        q = q.where(MatchingException.resolution == None)  # noqa: E711
    q = q.order_by(MatchingException.created_at.desc())

    result = await db.execute(q)
    return [
        {**_exception_to_dict(me), "invoice_number": inv_num, "supplier_name": sup_name}
        for me, inv_num, sup_name in result.all()
    ]


async def get_match_summary(db: AsyncSession) -> Dict[str, Any]:
    """Return summary statistics for matching."""
    total_result = await db.execute(select(func.count(MatchResult.id)))
    total = total_result.scalar() or 0

    passed_result = await db.execute(
        select(func.count(MatchResult.id)).where(MatchResult.status == "PASSED")
    )
    passed = passed_result.scalar() or 0

    exc_result = await db.execute(
        select(func.count(MatchResult.id)).where(MatchResult.status == "EXCEPTION")
    )
    exceptions = exc_result.scalar() or 0

    fraud_result = await db.execute(
        select(func.count(MatchResult.id)).where(MatchResult.status == "BLOCKED_FRAUD")
    )
    blocked_fraud = fraud_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(MatchResult.id)).where(MatchResult.status == "PENDING")
    )
    pending = pending_result.scalar() or 0

    open_exc_result = await db.execute(
        select(func.count(MatchingException.id)).where(MatchingException.resolution == None)  # noqa: E711
    )
    open_exceptions = open_exc_result.scalar() or 0

    return {
        "total_matches": total,
        "passed": passed,
        "exceptions": exceptions,
        "blocked_fraud": blocked_fraud,
        "pending": pending,
        "open_exceptions": open_exceptions,
    }


# ---------------------------------------------------------------------------
# Resolve exception
# ---------------------------------------------------------------------------

async def resolve_exception(
    db: AsyncSession,
    exception_id: str,
    resolution: str,
    resolved_by: str,
    resolution_notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Resolve a matching exception."""
    result = await db.execute(
        select(MatchingException).where(MatchingException.id == exception_id)
    )
    exc = result.scalar_one_or_none()
    if not exc:
        raise ValueError(f"Exception {exception_id} not found")
    if exc.resolution:
        raise ValueError(f"Exception already resolved as {exc.resolution}")

    exc.resolution = resolution
    exc.resolved_by = resolved_by
    exc.resolved_at = datetime.utcnow()
    exc.resolution_notes = resolution_notes

    # If approved override, update invoice match status
    if resolution == "APPROVED_OVERRIDE":
        inv_result = await db.execute(
            select(Invoice).where(Invoice.id == exc.invoice_id)
        )
        inv = inv_result.scalar_one_or_none()
        if inv:
            inv.match_status = "OVERRIDE_APPROVED"
            inv.match_note = f"Exception overridden by {resolved_by}: {resolution_notes or 'N/A'}"

    await db.commit()

    # Fetch invoice number for response
    inv_result = await db.execute(
        select(Invoice.invoice_number, Supplier.legal_name)
        .outerjoin(Supplier, Supplier.id == Invoice.supplier_id)
        .where(Invoice.id == exc.invoice_id)
    )
    row = inv_result.first()
    inv_num = row[0] if row else None
    sup_name = row[1] if row else None

    await event_bus.publish(Event(
        name="matching.exception_resolved",
        data={"exception_id": exception_id, "resolution": resolution},
        source="matching",
    ))

    return {**_exception_to_dict(exc), "invoice_number": inv_num, "supplier_name": sup_name}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _result_to_dict(mr: MatchResult, invoice_number: Optional[str] = None) -> Dict[str, Any]:
    return {
        "id": mr.id,
        "invoice_id": mr.invoice_id,
        "invoice_number": invoice_number,
        "match_type": mr.match_type,
        "status": mr.status,
        "variance_pct": mr.variance_pct,
        "exception_reason": mr.exception_reason,
        "note": mr.note,
        "created_at": mr.created_at.isoformat() if mr.created_at else None,
    }


def _exception_to_dict(me: MatchingException) -> Dict[str, Any]:
    return {
        "id": me.id,
        "match_result_id": me.match_result_id,
        "invoice_id": me.invoice_id,
        "exception_type": me.exception_type,
        "severity": me.severity,
        "description": me.description,
        "resolution": me.resolution,
        "resolved_by": me.resolved_by,
        "resolved_at": me.resolved_at.isoformat() if me.resolved_at else None,
        "resolution_notes": me.resolution_notes,
        "created_at": me.created_at.isoformat() if me.created_at else None,
    }
