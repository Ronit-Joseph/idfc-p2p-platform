"""
Matching Module — SQLAlchemy Models
Table: match_results

Stores the outcome of 2-way and 3-way matching between invoices, POs, and GRNs.
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
