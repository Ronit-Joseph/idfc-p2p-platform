"""
Purchase Orders Module — SQLAlchemy Models
Tables: purchase_orders, po_line_items, goods_receipt_notes, grn_line_items

Derived from the 3-record PURCHASE_ORDERS and 3-record GRNS lists in the prototype.
"""

import uuid

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, func

from backend.base_model import Base, TimestampMixin


class PurchaseOrder(TimestampMixin, Base):
    """Purchase Order (PO) — replaces Oracle EBS PO UI.

    Lifecycle: DRAFT -> ISSUED -> ACKNOWLEDGED -> PARTIALLY_RECEIVED -> RECEIVED -> CLOSED
    """

    __tablename__ = "purchase_orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    po_number = Column(String(20), unique=True, nullable=False, index=True)  # e.g. PO2024-001
    pr_id = Column(String(36), ForeignKey("purchase_requests.id"), nullable=True, index=True)
    supplier_id = Column(String(36), ForeignKey("suppliers.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    status = Column(String(30), nullable=False, default="DRAFT")
    delivery_date = Column(String(20), nullable=True)  # date string for SQLite compat
    dispatch_date = Column(DateTime, nullable=True)
    acknowledged_date = Column(DateTime, nullable=True)
    ebs_commitment_status = Column(String(20), nullable=True)  # POSTED / PENDING / FAILED
    ebs_commitment_ref = Column(String(50), nullable=True)


class POLineItem(Base):
    """Individual line item within a Purchase Order."""

    __tablename__ = "po_line_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    po_id = Column(String(36), ForeignKey("purchase_orders.id"), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Float, nullable=False, default=1)
    unit = Column(String(20), nullable=True)
    unit_price = Column(Float, nullable=False, default=0)
    total = Column(Float, nullable=False, default=0)
    grn_quantity = Column(Float, nullable=False, default=0)
    sort_order = Column(Integer, nullable=False, default=0)


class GoodsReceiptNote(TimestampMixin, Base):
    """Goods Receipt Note (GRN) — records what was physically received against a PO."""

    __tablename__ = "goods_receipt_notes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    grn_number = Column(String(20), unique=True, nullable=False, index=True)  # e.g. GRN2024-001
    po_id = Column(String(36), ForeignKey("purchase_orders.id"), nullable=False, index=True)
    received_date = Column(String(20), nullable=True)  # date string for SQLite compat
    received_by = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="PARTIAL")  # PARTIAL / COMPLETE
    notes = Column(Text, nullable=True)


class GRNLineItem(Base):
    """Individual line item within a GRN."""

    __tablename__ = "grn_line_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    grn_id = Column(String(36), ForeignKey("goods_receipt_notes.id"), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    po_quantity = Column(Float, nullable=False, default=0)
    received_quantity = Column(Float, nullable=False, default=0)
    unit = Column(String(20), nullable=True)
