"""
TDS Management Module — SQLAlchemy Models
Table: tds_deductions

Tracks TDS deduction records per invoice/supplier.
Supports Form 16A generation and quarterly return filing.
"""

import uuid

from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, func

from backend.base_model import Base, TimestampMixin


class TDSDeduction(TimestampMixin, Base):
    """TDS deduction record for an invoice payment.

    section: 194C (Contractor), 194J (Professional), 194H (Commission),
             194I (Rent), 194Q (Purchase), etc.
    status: PENDING, DEDUCTED, DEPOSITED, RETURN_FILED
    quarter: Q1 (Apr-Jun), Q2 (Jul-Sep), Q3 (Oct-Dec), Q4 (Jan-Mar)
    """

    __tablename__ = "tds_deductions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False, index=True)
    supplier_id = Column(String(36), ForeignKey("suppliers.id"), nullable=False, index=True)
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=True, index=True)

    # TDS details
    section = Column(String(10), nullable=False)  # 194C, 194J, etc.
    pan = Column(String(10), nullable=True)
    tds_rate = Column(Float, nullable=False)
    base_amount = Column(Float, nullable=False)  # Amount before TDS
    tds_amount = Column(Float, nullable=False)
    surcharge = Column(Float, nullable=False, default=0)
    cess = Column(Float, nullable=False, default=0)
    total_tds = Column(Float, nullable=False)

    # Status tracking
    status = Column(String(20), nullable=False, default="PENDING")
    fiscal_year = Column(String(10), nullable=False)  # e.g. "FY2024-25"
    quarter = Column(String(5), nullable=False)  # Q1, Q2, Q3, Q4

    # Deposit info
    challan_number = Column(String(50), nullable=True)
    deposit_date = Column(DateTime, nullable=True)
    bsr_code = Column(String(20), nullable=True)

    # Form 16A
    certificate_number = Column(String(50), nullable=True)
    form16a_generated = Column(String(3), nullable=False, default="NO")  # YES/NO
    form16a_issued_date = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)
