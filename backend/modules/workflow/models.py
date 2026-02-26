"""
Workflow Module — SQLAlchemy Models
Table: approval_matrices

Defines the approval routing rules for PRs, POs, and Invoices
based on entity type, department, category, and amount thresholds.
"""

import uuid

from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, func

from backend.base_model import Base, TimestampMixin


class ApprovalMatrix(TimestampMixin, Base):
    """Approval matrix rule.

    Determines which role must approve a given entity type at a given
    amount level. Multiple rows can exist for multi-level approvals.

    entity_type: PR, PO, INVOICE
    approver_role: DEPARTMENT_HEAD, FINANCE_HEAD, PROCUREMENT_MANAGER, ADMIN
    """

    __tablename__ = "approval_matrices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    entity_type = Column(String(20), nullable=False)  # PR / PO / INVOICE
    department = Column(String(10), nullable=True)  # Optional department filter
    category = Column(String(100), nullable=True)  # Optional category filter
    min_amount = Column(Float, nullable=False, default=0)
    max_amount = Column(Float, nullable=False, default=0)
    approver_role = Column(String(50), nullable=False)
    level = Column(Integer, nullable=False, default=1)  # 1 = first approver, 2 = second, etc.
    is_active = Column(Boolean, nullable=False, default=True)
