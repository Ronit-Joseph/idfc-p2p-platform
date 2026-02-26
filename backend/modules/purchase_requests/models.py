"""
Purchase Requests Module — SQLAlchemy Models
Tables: purchase_requests, pr_line_items

Derived from the 8-record PURCHASE_REQUESTS list in the prototype.
"""

import uuid

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, func

from backend.base_model import Base, TimestampMixin


class PurchaseRequest(TimestampMixin, Base):
    """Purchase Request (PR) — replaces Oracle EBS PR UI.

    Lifecycle: DRAFT -> PENDING_APPROVAL -> APPROVED -> PO_CREATED
                                         -> REJECTED
    """

    __tablename__ = "purchase_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    pr_number = Column(String(20), unique=True, nullable=False, index=True)  # e.g. PR2024-001
    title = Column(String(500), nullable=False)
    department = Column(String(10), nullable=False)
    requester = Column(String(255), nullable=False)
    requester_email = Column(String(255), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    gl_account = Column(String(20), nullable=True)
    cost_center = Column(String(20), nullable=True)
    category = Column(String(100), nullable=True)
    supplier_preference = Column(String(20), nullable=True)  # Preferred supplier code
    justification = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="DRAFT")
    po_id = Column(String(36), nullable=True)  # FK to purchase_orders.id once PO created
    budget_check = Column(String(20), nullable=True)  # APPROVED / FAILED
    budget_available_at_time = Column(Float, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approver = Column(String(255), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    rejected_at = Column(DateTime, nullable=True)


class PRLineItem(Base):
    """Individual line item within a Purchase Request."""

    __tablename__ = "pr_line_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    pr_id = Column(String(36), ForeignKey("purchase_requests.id"), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Float, nullable=False, default=1)
    unit = Column(String(20), nullable=True)  # LS, REAM, BOX, PCS, PACK, KG, YEAR, MONTH, QUARTER
    unit_price = Column(Float, nullable=False, default=0)
    sort_order = Column(Integer, nullable=False, default=0)
