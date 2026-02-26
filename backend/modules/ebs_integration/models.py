"""
EBS Integration Module — SQLAlchemy Models
Table: ebs_events

Records all integration events sent to/from Oracle EBS via OIC (Oracle
Integration Cloud). Oracle EBS is retained only for AP, AR, GL, and
Fixed Assets — all PR/PO/Invoice UI is handled by the P2P platform.

Derived from the 8-record EBS_EVENTS list in the prototype.
"""

import uuid

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, func

from backend.base_model import Base, TimestampMixin


class EBSEvent(TimestampMixin, Base):
    """Oracle EBS integration event.

    event_type: PO_COMMITMENT, INVOICE_POST, GL_JOURNAL, FA_ADDITION, etc.
    ebs_module: AP, GL, FA (retained modules only).
    status: PENDING -> ACKNOWLEDGED or FAILED.
    """

    __tablename__ = "ebs_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    event_code = Column(String(20), nullable=True, index=True)  # e.g. "EBS001"
    event_type = Column(String(30), nullable=False)
    entity_id = Column(String(50), nullable=True, index=True)
    entity_ref = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    gl_account = Column(String(20), nullable=True)
    amount = Column(Float, nullable=True)
    ebs_module = Column(String(10), nullable=False)  # AP / GL / FA
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING / ACKNOWLEDGED / FAILED
    sent_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    ebs_ref = Column(String(50), nullable=True)  # e.g. "EBS-AP-78234"
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
