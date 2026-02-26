"""
Matching Module — SQLAlchemy Models
Tables: match_results, matching_exceptions

Stores the outcome of 2-way and 3-way matching between invoices, POs, and GRNs,
plus exception queue for manual resolution.
"""

import uuid

from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, func

from backend.base_model import Base


class MatchResult(Base):
    """Result of the invoice matching engine.

    match_type: 2WAY (invoice vs PO) or 3WAY (invoice vs PO vs GRN).
    status: PASSED, EXCEPTION, BLOCKED_FRAUD, PENDING.
    """

    __tablename__ = "match_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False, index=True)
    match_type = Column(String(20), nullable=False)  # 2WAY / 3WAY
    status = Column(String(30), nullable=False, default="PENDING")  # PASSED / EXCEPTION / BLOCKED_FRAUD / PENDING
    variance_pct = Column(Float, nullable=True)
    exception_reason = Column(Text, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class MatchingException(Base):
    """Exception queue entry — invoice that failed matching and needs manual resolution.

    resolution: APPROVED_OVERRIDE, REJECTED, ESCALATED, AUTO_RESOLVED
    """

    __tablename__ = "matching_exceptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    match_result_id = Column(String(36), ForeignKey("match_results.id"), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False, index=True)
    exception_type = Column(String(50), nullable=False)  # PRICE_VARIANCE, QUANTITY_MISMATCH, NO_PO, DUPLICATE, OTHER
    severity = Column(String(20), nullable=False, default="MEDIUM")  # LOW / MEDIUM / HIGH / CRITICAL
    description = Column(Text, nullable=True)
    resolution = Column(String(30), nullable=True)  # APPROVED_OVERRIDE / REJECTED / ESCALATED / AUTO_RESOLVED
    resolved_by = Column(String(255), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
