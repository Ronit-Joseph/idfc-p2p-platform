"""
Audit Module — SQLAlchemy Models
Table: audit_logs

Append-only audit trail — NO UPDATE or DELETE operations allowed.
RBI requires 7-year retention of all audit records.
"""

import uuid

from sqlalchemy import Column, String, Text, DateTime, JSON, func

from backend.base_model import Base


class AuditLog(Base):
    """Append-only audit log entry.

    Every significant action in the P2P platform generates an audit log:
    - PR/PO/Invoice creation, approval, rejection
    - EBS event posting and acknowledgement
    - AI agent actions (fraud flag, GL coding, SLA alerts)
    - GST cache sync operations
    - Vendor portal event processing
    - User authentication events

    IMPORTANT: This table is append-only. Service layer must never issue
    UPDATE or DELETE statements against this table.
    """

    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    source_module = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=True)  # INVOICE, PR, PO, SUPPLIER, etc.
    entity_id = Column(String(100), nullable=True, index=True)
    actor = Column(String(255), nullable=True)  # User or agent who performed the action
    payload = Column(JSON, nullable=True)  # Full event payload for audit reconstruction
    timestamp = Column(DateTime, nullable=False, server_default=func.now(), index=True)
