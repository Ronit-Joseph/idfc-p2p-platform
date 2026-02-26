"""
Workflow Module — SQLAlchemy Models
Tables: approval_matrices, approval_instances, approval_steps

Defines the approval routing rules and tracks live approval requests.
"""

import uuid

from sqlalchemy import Column, String, Boolean, Integer, Float, Text, DateTime, ForeignKey, func

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


class ApprovalInstance(TimestampMixin, Base):
    """A live approval request for an entity (PR, PO, or Invoice).

    Tracks the overall status of the approval flow. Each instance has
    one or more ApprovalStep rows (one per level).

    status: PENDING, APPROVED, REJECTED, ESCALATED, CANCELLED
    """

    __tablename__ = "approval_instances"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    entity_type = Column(String(20), nullable=False, index=True)  # PR / PO / INVOICE
    entity_id = Column(String(100), nullable=False, index=True)  # e.g. "PR2024-001"
    entity_ref = Column(String(36), nullable=True)  # UUID FK to the actual table row
    department = Column(String(10), nullable=True)
    amount = Column(Float, nullable=False, default=0)
    total_levels = Column(Integer, nullable=False, default=1)
    current_level = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="PENDING")
    requested_by = Column(String(255), nullable=True)
    completed_at = Column(DateTime, nullable=True)


class ApprovalStep(Base):
    """One step in a multi-level approval flow.

    status: PENDING, APPROVED, REJECTED, SKIPPED
    """

    __tablename__ = "approval_steps"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    instance_id = Column(String(36), ForeignKey("approval_instances.id"), nullable=False, index=True)
    level = Column(Integer, nullable=False)
    approver_role = Column(String(50), nullable=False)
    approver_name = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")
    comments = Column(Text, nullable=True)
    acted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
