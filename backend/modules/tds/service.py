"""
TDS Management Module — Service Layer

TDS deduction computation, deposit tracking, Form 16A management.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.event_bus import Event, event_bus
from backend.modules.tds.models import TDSDeduction
from backend.modules.invoices.models import Invoice
from backend.modules.suppliers.models import Supplier


# ---------------------------------------------------------------------------
# TDS rate lookup (Indian tax sections)
# ---------------------------------------------------------------------------
TDS_RATES = {
    "194C": {"description": "Contractor Payment", "individual": 1.0, "company": 2.0},
    "194J": {"description": "Professional/Technical Fees", "individual": 10.0, "company": 10.0},
    "194H": {"description": "Commission/Brokerage", "individual": 5.0, "company": 5.0},
    "194I": {"description": "Rent", "individual": 10.0, "company": 10.0},
    "194Q": {"description": "Purchase of Goods", "individual": 0.1, "company": 0.1},
    "194A": {"description": "Interest (other than securities)", "individual": 10.0, "company": 10.0},
}


def _get_fiscal_year() -> str:
    now = datetime.utcnow()
    if now.month >= 4:
        return f"FY{now.year}-{str(now.year + 1)[2:]}"
    return f"FY{now.year - 1}-{str(now.year)[2:]}"


def _get_quarter() -> str:
    month = datetime.utcnow().month
    if month in (4, 5, 6):
        return "Q1"
    elif month in (7, 8, 9):
        return "Q2"
    elif month in (10, 11, 12):
        return "Q3"
    return "Q4"


# ---------------------------------------------------------------------------
# Create TDS deduction
# ---------------------------------------------------------------------------

async def create_tds_deduction(
    db: AsyncSession,
    invoice_number: str,
    section: str,
    tds_rate: Optional[float] = None,
) -> Dict[str, Any]:
    """Create a TDS deduction record for an invoice."""
    # Load invoice
    result = await db.execute(
        select(Invoice).where(Invoice.invoice_number == invoice_number)
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise ValueError(f"Invoice {invoice_number} not found")

    # Load supplier for PAN
    sup_result = await db.execute(
        select(Supplier).where(Supplier.id == inv.supplier_id)
    )
    supplier = sup_result.scalar_one_or_none()

    # Determine rate
    if tds_rate is None:
        section_info = TDS_RATES.get(section)
        if section_info:
            tds_rate = section_info["company"]
        else:
            tds_rate = inv.tds_rate or 2.0

    base_amount = inv.subtotal
    tds_amount = base_amount * tds_rate / 100
    surcharge = 0.0
    cess = tds_amount * 0.04  # 4% health & education cess
    total_tds = tds_amount + surcharge + cess

    deduction = TDSDeduction(
        invoice_id=inv.id,
        supplier_id=inv.supplier_id,
        section=section,
        pan=supplier.pan if supplier else None,
        tds_rate=tds_rate,
        base_amount=base_amount,
        tds_amount=tds_amount,
        surcharge=surcharge,
        cess=cess,
        total_tds=total_tds,
        status="PENDING",
        fiscal_year=_get_fiscal_year(),
        quarter=_get_quarter(),
    )
    db.add(deduction)
    await db.commit()
    await db.refresh(deduction)

    await event_bus.publish(Event(
        name="tds.deduction_created",
        data={"invoice": invoice_number, "section": section, "amount": total_tds},
        source="tds",
    ))

    return await _deduction_to_dict(db, deduction)


# ---------------------------------------------------------------------------
# List & query
# ---------------------------------------------------------------------------

async def list_deductions(
    db: AsyncSession,
    fiscal_year: Optional[str] = None,
    quarter: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List TDS deductions with optional filters."""
    q = select(TDSDeduction)
    if fiscal_year:
        q = q.where(TDSDeduction.fiscal_year == fiscal_year)
    if quarter:
        q = q.where(TDSDeduction.quarter == quarter)
    if status:
        q = q.where(TDSDeduction.status == status)
    q = q.order_by(TDSDeduction.created_at.desc())

    result = await db.execute(q)
    out = []
    for d in result.scalars().all():
        out.append(await _deduction_to_dict(db, d))
    return out


async def get_tds_summary(db: AsyncSession) -> Dict[str, Any]:
    """Summary statistics for TDS."""
    total_result = await db.execute(select(func.count(TDSDeduction.id)))
    total = total_result.scalar() or 0

    amount_result = await db.execute(select(func.sum(TDSDeduction.total_tds)))
    total_amount = amount_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(TDSDeduction.id)).where(TDSDeduction.status == "PENDING")
    )
    pending = pending_result.scalar() or 0

    pending_amount_result = await db.execute(
        select(func.sum(TDSDeduction.total_tds)).where(TDSDeduction.status == "PENDING")
    )
    pending_amount = pending_amount_result.scalar() or 0

    deposited_result = await db.execute(
        select(func.count(TDSDeduction.id)).where(TDSDeduction.status == "DEPOSITED")
    )
    deposited = deposited_result.scalar() or 0

    filed_result = await db.execute(
        select(func.count(TDSDeduction.id)).where(TDSDeduction.status == "RETURN_FILED")
    )
    return_filed = filed_result.scalar() or 0

    form16a_result = await db.execute(
        select(func.count(TDSDeduction.id)).where(TDSDeduction.form16a_generated == "NO")
    )
    form16a_pending = form16a_result.scalar() or 0

    return {
        "total_deductions": total,
        "total_tds_amount": total_amount,
        "pending_deposit": pending,
        "pending_deposit_amount": pending_amount,
        "deposited": deposited,
        "return_filed": return_filed,
        "form16a_pending": form16a_pending,
    }


async def deposit_tds(
    db: AsyncSession,
    deduction_id: str,
    challan_number: str,
    bsr_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Record TDS deposit against a government challan."""
    result = await db.execute(
        select(TDSDeduction).where(TDSDeduction.id == deduction_id)
    )
    ded = result.scalar_one_or_none()
    if not ded:
        raise ValueError(f"TDS deduction {deduction_id} not found")
    if ded.status != "PENDING":
        raise ValueError(f"Deduction is {ded.status}, not PENDING")

    ded.status = "DEPOSITED"
    ded.challan_number = challan_number
    ded.bsr_code = bsr_code
    ded.deposit_date = datetime.utcnow()
    await db.commit()
    await db.refresh(ded)

    await event_bus.publish(Event(
        name="tds.deposited",
        data={"deduction_id": deduction_id, "challan": challan_number},
        source="tds",
    ))

    return await _deduction_to_dict(db, ded)


async def generate_form16a(
    db: AsyncSession,
    deduction_id: str,
) -> Dict[str, Any]:
    """Generate Form 16A certificate for a deposited TDS deduction."""
    result = await db.execute(
        select(TDSDeduction).where(TDSDeduction.id == deduction_id)
    )
    ded = result.scalar_one_or_none()
    if not ded:
        raise ValueError(f"TDS deduction {deduction_id} not found")
    if ded.status not in ("DEPOSITED", "RETURN_FILED"):
        raise ValueError(f"TDS must be DEPOSITED before Form 16A generation")

    ded.form16a_generated = "YES"
    ded.form16a_issued_date = datetime.utcnow()
    ded.certificate_number = f"F16A-{ded.fiscal_year}-{ded.quarter}-{ded.id[:8]}"
    await db.commit()
    await db.refresh(ded)

    return await _deduction_to_dict(db, ded)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _deduction_to_dict(db: AsyncSession, d: TDSDeduction) -> Dict[str, Any]:
    # Resolve invoice number and supplier name
    inv_result = await db.execute(
        select(Invoice.invoice_number).where(Invoice.id == d.invoice_id)
    )
    inv_num = inv_result.scalar()

    sup_result = await db.execute(
        select(Supplier.legal_name).where(Supplier.id == d.supplier_id)
    )
    sup_name = sup_result.scalar()

    return {
        "id": d.id,
        "invoice_id": d.invoice_id,
        "invoice_number": inv_num,
        "supplier_id": d.supplier_id,
        "supplier_name": sup_name,
        "pan": d.pan,
        "section": d.section,
        "tds_rate": d.tds_rate,
        "base_amount": d.base_amount,
        "tds_amount": d.tds_amount,
        "surcharge": d.surcharge,
        "cess": d.cess,
        "total_tds": d.total_tds,
        "status": d.status,
        "fiscal_year": d.fiscal_year,
        "quarter": d.quarter,
        "challan_number": d.challan_number,
        "deposit_date": d.deposit_date.isoformat() if d.deposit_date else None,
        "bsr_code": d.bsr_code,
        "certificate_number": d.certificate_number,
        "form16a_generated": d.form16a_generated,
        "form16a_issued_date": d.form16a_issued_date.isoformat() if d.form16a_issued_date else None,
        "notes": d.notes,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }
