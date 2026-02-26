"""
Payments Module — Service Layer

Payment run creation, individual payment tracking, bank file generation stubs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.event_bus import Event, event_bus
from backend.modules.payments.models import Payment, PaymentRun
from backend.modules.invoices.models import Invoice
from backend.modules.suppliers.models import Supplier


# ---------------------------------------------------------------------------
# Counter for run/payment numbers
# ---------------------------------------------------------------------------

async def _next_run_number(db: AsyncSession) -> str:
    result = await db.execute(select(func.count(PaymentRun.id)))
    count = (result.scalar() or 0) + 1
    return f"PAYRUN-{count:04d}"


async def _next_payment_number(db: AsyncSession) -> str:
    result = await db.execute(select(func.count(Payment.id)))
    count = (result.scalar() or 0) + 1
    return f"PAY-{count:06d}"


# ---------------------------------------------------------------------------
# Payment Runs
# ---------------------------------------------------------------------------

async def create_payment_run(
    db: AsyncSession,
    invoice_numbers: List[str],
    payment_method: str = "NEFT",
    initiated_by: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a payment run for a batch of approved invoices."""
    # Validate invoices
    result = await db.execute(
        select(Invoice).where(Invoice.invoice_number.in_(invoice_numbers))
    )
    invoices = list(result.scalars().all())
    if not invoices:
        raise ValueError("No valid invoices found")

    # Only process APPROVED or POSTED_TO_EBS invoices
    payable = [inv for inv in invoices if inv.status in ("APPROVED", "POSTED_TO_EBS")]
    if not payable:
        raise ValueError("No invoices in payable status (APPROVED or POSTED_TO_EBS)")

    run_number = await _next_run_number(db)
    total_amount = sum(inv.net_payable for inv in payable)

    run = PaymentRun(
        run_number=run_number,
        payment_method=payment_method,
        status="DRAFT",
        total_amount=total_amount,
        invoice_count=len(payable),
        initiated_by=initiated_by,
        notes=notes,
    )
    db.add(run)
    await db.flush()

    # Create individual payments
    payments = []
    for inv in payable:
        pay_num = await _next_payment_number(db)
        payment = Payment(
            payment_number=pay_num,
            invoice_id=inv.id,
            supplier_id=inv.supplier_id,
            payment_run_id=run.id,
            amount=inv.total_amount,
            tds_deducted=inv.tds_amount,
            net_amount=inv.net_payable,
            currency="INR",
            payment_method=payment_method,
            status="PENDING",
        )
        db.add(payment)
        payments.append(payment)

    await db.commit()
    await db.refresh(run)
    for p in payments:
        await db.refresh(p)

    await event_bus.publish(Event(
        name="payment.run_created",
        data={"run_number": run_number, "invoice_count": len(payable), "total": total_amount},
        source="payments",
    ))

    return await _run_to_dict(db, run, payments)


async def list_payment_runs(db: AsyncSession) -> List[Dict[str, Any]]:
    """List all payment runs."""
    result = await db.execute(
        select(PaymentRun).order_by(PaymentRun.created_at.desc())
    )
    runs = result.scalars().all()
    out = []
    for run in runs:
        pay_result = await db.execute(
            select(Payment).where(Payment.payment_run_id == run.id)
        )
        payments = list(pay_result.scalars().all())
        out.append(await _run_to_dict(db, run, payments))
    return out


async def process_payment_run(
    db: AsyncSession,
    run_number: str,
    approved_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Advance a payment run from DRAFT → SCHEDULED → PROCESSING → COMPLETED."""
    result = await db.execute(
        select(PaymentRun).where(PaymentRun.run_number == run_number)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise ValueError(f"Payment run {run_number} not found")

    transitions = {
        "DRAFT": "SCHEDULED",
        "SCHEDULED": "PROCESSING",
        "PROCESSING": "COMPLETED",
    }
    next_status = transitions.get(run.status)
    if not next_status:
        raise ValueError(f"Cannot advance run from {run.status}")

    run.status = next_status
    if next_status == "SCHEDULED":
        run.approved_by = approved_by
        run.approved_at = datetime.utcnow()
    elif next_status == "COMPLETED":
        run.completed_at = datetime.utcnow()
        run.bank_file_ref = f"NEFT-{run.run_number}-{datetime.utcnow().strftime('%Y%m%d')}"
        # Mark all payments as completed
        pay_result = await db.execute(
            select(Payment).where(Payment.payment_run_id == run.id)
        )
        for pay in pay_result.scalars().all():
            pay.status = "COMPLETED"
            pay.payment_date = datetime.utcnow()
            pay.bank_reference = f"UTR{run.run_number[-4:]}{pay.payment_number[-6:]}"

    await db.commit()
    await db.refresh(run)

    pay_result = await db.execute(
        select(Payment).where(Payment.payment_run_id == run.id)
    )
    payments = list(pay_result.scalars().all())

    await event_bus.publish(Event(
        name=f"payment.run_{next_status.lower()}",
        data={"run_number": run.run_number, "status": next_status},
        source="payments",
    ))

    return await _run_to_dict(db, run, payments)


# ---------------------------------------------------------------------------
# Individual Payments
# ---------------------------------------------------------------------------

async def list_payments(db: AsyncSession) -> List[Dict[str, Any]]:
    """List all payments with invoice/supplier details."""
    result = await db.execute(
        select(Payment, Invoice.invoice_number, Supplier.legal_name)
        .join(Invoice, Invoice.id == Payment.invoice_id)
        .outerjoin(Supplier, Supplier.id == Payment.supplier_id)
        .order_by(Payment.created_at.desc())
    )
    return [
        {**_payment_to_dict(p), "invoice_number": inv_num, "supplier_name": sup_name}
        for p, inv_num, sup_name in result.all()
    ]


async def get_payment_summary(db: AsyncSession) -> Dict[str, Any]:
    """Payment summary statistics."""
    total_result = await db.execute(select(func.count(Payment.id)))
    total = total_result.scalar() or 0

    amount_result = await db.execute(select(func.sum(Payment.net_amount)))
    total_amount = amount_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(Payment.id)).where(Payment.status == "PENDING")
    )
    pending = pending_result.scalar() or 0

    completed_result = await db.execute(
        select(func.count(Payment.id)).where(Payment.status == "COMPLETED")
    )
    completed = completed_result.scalar() or 0

    failed_result = await db.execute(
        select(func.count(Payment.id)).where(Payment.status == "FAILED")
    )
    failed = failed_result.scalar() or 0

    runs_result = await db.execute(select(func.count(PaymentRun.id)))
    total_runs = runs_result.scalar() or 0

    return {
        "total_payments": total,
        "total_amount": total_amount,
        "pending": pending,
        "completed": completed,
        "failed": failed,
        "total_runs": total_runs,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _payment_to_dict(p: Payment) -> Dict[str, Any]:
    return {
        "id": p.id,
        "payment_number": p.payment_number,
        "invoice_id": p.invoice_id,
        "supplier_id": p.supplier_id,
        "amount": p.amount,
        "tds_deducted": p.tds_deducted,
        "net_amount": p.net_amount,
        "currency": p.currency,
        "payment_method": p.payment_method,
        "status": p.status,
        "bank_reference": p.bank_reference,
        "payment_date": p.payment_date.isoformat() if p.payment_date else None,
        "ebs_voucher_ref": p.ebs_voucher_ref,
        "remittance_sent": p.remittance_sent,
        "notes": p.notes,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


async def _run_to_dict(
    db: AsyncSession, run: PaymentRun, payments: List[Payment],
) -> Dict[str, Any]:
    # Resolve invoice numbers and supplier names
    pay_dicts = []
    for p in payments:
        inv_result = await db.execute(
            select(Invoice.invoice_number).where(Invoice.id == p.invoice_id)
        )
        inv_num = inv_result.scalar()
        sup_result = await db.execute(
            select(Supplier.legal_name).where(Supplier.id == p.supplier_id)
        )
        sup_name = sup_result.scalar()
        pay_dicts.append({
            **_payment_to_dict(p),
            "invoice_number": inv_num,
            "supplier_name": sup_name,
        })

    return {
        "id": run.id,
        "run_number": run.run_number,
        "payment_method": run.payment_method,
        "status": run.status,
        "total_amount": run.total_amount,
        "invoice_count": run.invoice_count,
        "bank_file_ref": run.bank_file_ref,
        "initiated_by": run.initiated_by,
        "approved_by": run.approved_by,
        "approved_at": run.approved_at.isoformat() if run.approved_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "notes": run.notes,
        "payments": pay_dicts,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }
