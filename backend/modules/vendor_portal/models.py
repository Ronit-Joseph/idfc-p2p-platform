"""
Vendor Portal Module — SQLAlchemy Models
Table: vendor_portal_events

Records events received from the external Vendor Management Portal
via Kafka event stream. The Vendor Portal is a separate independently-built
system; this table captures its events for P2P processing.

Derived from the 6-record VENDOR_PORTAL_EVENTS list in the prototype.
"""

import uuid

from sqlalchemy import Column, String, Boolean, Text, DateTime, JSON, func

from backend.base_model import Base


class VendorPortalEvent(Base):
    """Inbound event from the Vendor Management Portal.

    event_type: vendor.onboarded, vendor.bank_verified,
                vendor.gstin_updated, vendor.document_expired, etc.
    processed: whether the P2P platform has acted on this event.
    p2p_action: description of what the P2P platform did in response.
    """

    __tablename__ = "vendor_portal_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    event_code = Column(String(20), nullable=True, index=True)  # e.g. "VPE001"
    event_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=True)
    supplier_id = Column(String(20), nullable=True, index=True)  # Vendor portal supplier code
    supplier_name = Column(String(500), nullable=True)
    payload = Column(JSON, nullable=True)  # Full event payload
    processed = Column(Boolean, nullable=False, default=False)
    p2p_action = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
