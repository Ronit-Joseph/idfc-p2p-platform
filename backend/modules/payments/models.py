"""
Payments Module — SQLAlchemy Models
Tables: payments, payment_runs

Tracks individual invoice payments and batch payment runs.
Supports NEFT/RTGS/IMPS bank file generation.
"""

import uuid

from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, func

from backend.base_model import Base, TimestampMixin


class PaymentRun(TimestampMixin, Base):
    """Batch payment run — groups invoices for bank file generation.

    status: DRAFT, SCHEDULED, PROCESSING, COMPLETED, FAILED, CANCELLED
    payment_method: NEFT, RTGS, IMPS, CHEQUE
    """

    __tablename__ = "payment_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    run_number = Column(String(50), unique=True, nullable=False, index=True)
    payment_method = Column(String(20), nullable=False, default="NEFT")
    status = Column(String(20), nullable=False, default="DRAFT")
    total_amount = Column(Float, nullable=False, default=0)
    invoice_count = Column(Integer, nullable=False, default=0)
    bank_file_ref = Column(String(100), nullable=True)
    initiated_by = Column(String(255), nullable=True)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)


class Payment(TimestampMixin, Base):
    """Individual invoice payment record.

    status: PENDING, SCHEDULED, PROCESSING, COMPLETED, FAILED, REVERSED
    """

    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    payment_number = Column(String(50), unique=True, nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False, index=True)
    supplier_id = Column(String(36), ForeignKey("suppliers.id"), nullable=False, index=True)
    payment_run_id = Column(String(36), ForeignKey("payment_runs.id"), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    tds_deducted = Column(Float, nullable=False, default=0)
    net_amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    payment_method = Column(String(20), nullable=False, default="NEFT")
    status = Column(String(20), nullable=False, default="PENDING")
    bank_reference = Column(String(100), nullable=True)  # UTR number
    payment_date = Column(DateTime, nullable=True)
    ebs_voucher_ref = Column(String(50), nullable=True)  # EBS AP payment voucher
    remittance_sent = Column(String(10), nullable=False, default="NO")  # YES/NO
    notes = Column(Text, nullable=True)
