"""
Reports Module — CSV Export Routes

Endpoints for exporting invoices, payments, suppliers, and audit logs as CSV.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db
from backend.modules.invoices.models import Invoice
from backend.modules.payments.models import Payment
from backend.modules.suppliers.models import Supplier
from backend.modules.audit.models import AuditLog

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _csv_response(output: io.StringIO, filename: str) -> StreamingResponse:
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/invoices/csv")
async def export_invoices_csv(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).order_by(Invoice.invoice_number))
    invoices = list(result.scalars().all())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Invoice Number", "Supplier GSTIN", "Invoice Date", "Due Date",
        "Subtotal", "GST Amount", "TDS Amount", "Total Amount", "Net Payable",
        "Status", "Match Status", "MSME Status", "EBS AP Status", "Created At",
    ])
    for inv in invoices:
        writer.writerow([
            inv.invoice_number, inv.gstin_supplier, inv.invoice_date, inv.due_date,
            inv.subtotal, inv.gst_amount, inv.tds_amount, inv.total_amount, inv.net_payable,
            inv.status, inv.match_status, inv.msme_status, inv.ebs_ap_status,
            inv.created_at.isoformat() if inv.created_at else "",
        ])

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _csv_response(output, f"invoices_export_{ts}.csv")


@router.get("/payments/csv")
async def export_payments_csv(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Payment).order_by(Payment.payment_ref))
    payments = list(result.scalars().all())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Payment Ref", "Invoice Number", "Supplier Name", "Amount",
        "Payment Method", "Status", "Paid At", "Created At",
    ])
    for p in payments:
        writer.writerow([
            p.payment_ref, p.invoice_number, p.supplier_name, p.amount,
            p.payment_method, p.status,
            p.paid_at.isoformat() if p.paid_at else "",
            p.created_at.isoformat() if p.created_at else "",
        ])

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _csv_response(output, f"payments_export_{ts}.csv")


@router.get("/suppliers/csv")
async def export_suppliers_csv(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Supplier).order_by(Supplier.code))
    suppliers = list(result.scalars().all())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Code", "Legal Name", "GSTIN", "PAN", "State", "Category",
        "MSME Category", "Status", "Risk Score", "Created At",
    ])
    for s in suppliers:
        writer.writerow([
            s.code, s.legal_name, s.gstin, s.pan, s.state, s.category,
            s.msme_category, s.status, s.risk_score,
            s.created_at.isoformat() if s.created_at else "",
        ])

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _csv_response(output, f"suppliers_export_{ts}.csv")


@router.get("/audit/csv")
async def export_audit_csv(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(1000))
    logs = list(result.scalars().all())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Event Type", "Source Module", "Entity Type", "Entity ID",
        "Actor", "Timestamp",
    ])
    for log in logs:
        writer.writerow([
            log.event_type, log.source_module, log.entity_type, log.entity_id,
            log.actor,
            log.created_at.isoformat() if log.created_at else "",
        ])

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _csv_response(output, f"audit_export_{ts}.csv")
