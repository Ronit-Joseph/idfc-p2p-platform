"""
Invoices Module — SQLAlchemy Models
Table: invoices

The most complex entity in the P2P platform (~35+ columns).
Covers: OCR extraction, GST validation, 2/3-way matching, MSME compliance,
        AI coding, fraud detection, cash optimization, and EBS AP posting.

Derived from the 7-record INVOICES list in the prototype.
"""

import uuid

from sqlalchemy import Column, String, Boolean, Integer, Float, Text, DateTime, JSON, ForeignKey, func

from backend.base_model import Base, TimestampMixin


class Invoice(TimestampMixin, Base):
    """Invoice — the central document in the P2P lifecycle.

    Lifecycle:
        CAPTURED -> EXTRACTED -> VALIDATED -> MATCHED -> PENDING_APPROVAL
                 -> APPROVED -> POSTED_TO_EBS -> PAID
                 -> REJECTED (at any stage)

    This model covers every field from the prototype's INVOICES data structure,
    including OCR metadata, GST cache validation, matching results, AI agent
    outputs, MSME Section 43B(h) compliance tracking, and EBS AP posting state.
    """

    __tablename__ = "invoices"

    # ── Identity ──────────────────────────────────────────────
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    invoice_number = Column(String(50), nullable=False, index=True)

    # ── Relationships ─────────────────────────────────────────
    supplier_id = Column(String(36), ForeignKey("suppliers.id"), nullable=False, index=True)
    po_id = Column(String(36), ForeignKey("purchase_orders.id"), nullable=True, index=True)
    grn_id = Column(String(36), ForeignKey("goods_receipt_notes.id"), nullable=True)

    # ── Dates ─────────────────────────────────────────────────
    invoice_date = Column(String(20), nullable=True)  # date string for SQLite compat
    due_date = Column(String(20), nullable=True)

    # ── Financial amounts ─────────────────────────────────────
    subtotal = Column(Float, nullable=False, default=0)
    gst_rate = Column(Float, nullable=True)
    gst_amount = Column(Float, nullable=False, default=0)
    tds_rate = Column(Float, nullable=True)
    tds_amount = Column(Float, nullable=False, default=0)
    total_amount = Column(Float, nullable=False, default=0)
    net_payable = Column(Float, nullable=False, default=0)

    # ── GST identifiers ──────────────────────────────────────
    gstin_supplier = Column(String(15), nullable=True)
    gstin_buyer = Column(String(15), nullable=True)
    hsn_sac = Column(String(10), nullable=True)
    irn = Column(String(128), nullable=True)  # e-Invoice Reference Number

    # ── Status ────────────────────────────────────────────────
    status = Column(String(30), nullable=False, default="CAPTURED")

    # ── OCR extraction metadata ───────────────────────────────
    ocr_confidence = Column(Float, nullable=True)

    # ── GST cache validation ──────────────────────────────────
    gstin_cache_status = Column(String(20), nullable=True)
    gstin_validated_from_cache = Column(Boolean, nullable=False, default=False)
    gstr2b_itc_eligible = Column(Boolean, nullable=True)
    gstin_cache_age_hours = Column(Float, nullable=True)

    # ── Matching engine results ───────────────────────────────
    match_status = Column(String(30), nullable=True)  # 2WAY_MATCH_PASSED, 3WAY_MATCH_PASSED, 3WAY_MATCH_EXCEPTION, BLOCKED_FRAUD, PENDING
    match_variance = Column(Float, nullable=True)
    match_exception_reason = Column(Text, nullable=True)
    match_note = Column(Text, nullable=True)

    # ── AI coding agent output ────────────────────────────────
    coding_agent_gl = Column(String(20), nullable=True)
    coding_agent_confidence = Column(Float, nullable=True)
    coding_agent_category = Column(String(100), nullable=True)

    # ── Fraud detection ───────────────────────────────────────
    fraud_flag = Column(Boolean, nullable=False, default=False)
    fraud_reasons = Column(JSON, nullable=True, default=list)  # list of reason strings

    # ── Cash optimization ─────────────────────────────────────
    cash_opt_suggestion = Column(Text, nullable=True)

    # ── Oracle EBS AP integration ─────────────────────────────
    ebs_ap_status = Column(String(20), nullable=False, default="NOT_STARTED")  # NOT_STARTED / PENDING / POSTED / BLOCKED / FAILED
    ebs_ap_ref = Column(String(50), nullable=True)
    ebs_posted_at = Column(DateTime, nullable=True)

    # ── Approval / rejection ──────────────────────────────────
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_by = Column(String(255), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # ── MSME Section 43B(h) compliance ────────────────────────
    is_msme_supplier = Column(Boolean, nullable=False, default=False)
    msme_category = Column(String(10), nullable=True)  # MICRO / SMALL / MEDIUM
    msme_days_remaining = Column(Integer, nullable=True)
    msme_due_date = Column(String(20), nullable=True)  # date string
    msme_status = Column(String(20), nullable=True)  # ON_TRACK / AT_RISK / BREACHED
    msme_penalty_amount = Column(Float, nullable=True, default=0)

    # ── Upload metadata ───────────────────────────────────────
    uploaded_by = Column(String(255), nullable=True)
