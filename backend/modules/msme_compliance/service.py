"""
MSME Compliance Module — Service Layer

Computes Section 43B(h) 45-day payment SLA status from invoice data.

There is no dedicated MSME table.  All MSME compliance columns live on the
Invoice model (is_msme_supplier, msme_category, msme_days_remaining,
msme_due_date, msme_status, msme_penalty_amount).

Public API
----------
- get_msme_compliance(db)  ->  dict   (matches MSMEComplianceResponse shape)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select, case, asc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.invoices.models import Invoice
from backend.modules.suppliers.models import Supplier


# ---------------------------------------------------------------------------
# Internal helpers
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


def _build_msme_invoice_dict(
    inv: Invoice,
    supplier_name: str,
) -> Dict[str, Any]:
    """Build a single MSME invoice dict matching the legacy API shape."""
    return {
        "id": inv.invoice_number,
        "invoice_number": inv.invoice_number,
        "supplier_name": supplier_name,
        "msme_category": inv.msme_category,
        "amount": inv.total_amount,
        "due_date": inv.due_date,
        "msme_due_date": inv.msme_due_date,
        "days_remaining": inv.msme_days_remaining,
        "status": inv.msme_status,
        "penalty_amount": inv.msme_penalty_amount or 0,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_msme_compliance(db: AsyncSession) -> Dict[str, Any]:
    """Query all MSME-flagged invoices and compute the compliance dashboard.

    Returns a dict matching the ``MSMEComplianceResponse`` schema::

        {
            "summary": { ... MSMESummary fields ... },
            "invoices": [ ... MSMEInvoiceResponse dicts ... ]
        }

    Invoices are sorted by ``msme_days_remaining`` ascending (most urgent
    first), with NULL values pushed to the end.
    """
    # Fetch all invoices where is_msme_supplier = True, sorted by
    # msme_days_remaining ascending with NULLs last.
    # SQLAlchemy's ``asc(...).nullslast()`` works on PostgreSQL.
    # For SQLite compatibility we use a CASE expression to sort NULLs last.
    nulls_last_order = case(
        (Invoice.msme_days_remaining.is_(None), 1),
        else_=0,
    )
    result = await db.execute(
        select(Invoice)
        .where(Invoice.is_msme_supplier.is_(True))
        .order_by(nulls_last_order, asc(Invoice.msme_days_remaining))
    )
    msme_invoices: List[Invoice] = list(result.scalars().all())

    # Build per-invoice dicts, resolving supplier name via FK
    invoices_out: List[Dict[str, Any]] = []
    for inv in msme_invoices:
        supplier = await _load_supplier(db, inv.supplier_id)
        supplier_name = supplier.legal_name if supplier else "Unknown Supplier"
        invoices_out.append(_build_msme_invoice_dict(inv, supplier_name))

    # Compute summary statistics
    total = len(invoices_out)
    on_track = sum(1 for i in invoices_out if i["status"] == "ON_TRACK")
    at_risk = sum(1 for i in invoices_out if i["status"] == "AT_RISK")
    breached = sum(1 for i in invoices_out if i["status"] == "BREACHED")
    total_penalty_exposure = sum(i["penalty_amount"] for i in invoices_out)

    days_values = [
        i["days_remaining"]
        for i in invoices_out
        if i["days_remaining"] is not None
    ]
    avg_days_remaining = (
        round(sum(days_values) / len(days_values), 1) if days_values else 0
    )

    return {
        "summary": {
            "total_msme_invoices": total,
            "on_track": on_track,
            "at_risk": at_risk,
            "breached": breached,
            "total_penalty_exposure": total_penalty_exposure,
            "avg_days_remaining": avg_days_remaining,
        },
        "invoices": invoices_out,
    }
