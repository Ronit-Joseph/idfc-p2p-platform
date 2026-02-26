"""
GST Cache Module — SQLAlchemy Models
Tables: gst_records, gst_sync_log

Local cache of GSTIN data fetched from Cygnet GSP in batch mode.
Per the architecture, only IRN generation, IRN cancellation, and e-way bill
require live API calls. All other GST lookups are served from this cache.

Derived from the 15-record GST_CACHE list in the prototype.
"""

import uuid

from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime, func

from backend.base_model import Base, TimestampMixin


class GSTRecord(TimestampMixin, Base):
    """Cached GSTIN record from Cygnet GSP.

    Refreshed via batch sync. Stores GSTR-1 filing status, GSTR-2B
    availability, ITC eligibility, and cache hit metrics.
    """

    __tablename__ = "gst_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    gstin = Column(String(15), unique=True, nullable=False, index=True)
    legal_name = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")  # ACTIVE / SUSPENDED / CANCELLED
    state = Column(String(100), nullable=True)
    registration_type = Column(String(30), nullable=True)  # Regular / Composition
    last_gstr1_filed = Column(String(20), nullable=True)  # e.g. "Aug 2024"
    gstr2b_available = Column(Boolean, nullable=False, default=False)
    gstr2b_period = Column(String(20), nullable=True)
    gstr1_compliance = Column(String(20), nullable=True)  # FILED / PENDING / DELAYED
    itc_eligible = Column(Boolean, nullable=False, default=False)
    last_synced = Column(DateTime, nullable=True)
    sync_source = Column(String(20), nullable=True)  # CYGNET_BATCH / CYGNET_LIVE
    cache_hit_count = Column(Integer, nullable=False, default=0)
    gstr2b_alert = Column(Text, nullable=True)
    itc_note = Column(Text, nullable=True)


class GSTSyncLog(Base):
    """Log entry for each GST cache sync operation."""

    __tablename__ = "gst_sync_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    synced_at = Column(DateTime, nullable=False, server_default=func.now())
    provider = Column(String(50), nullable=False, default="Cygnet GSP")
    records_updated = Column(Integer, nullable=False, default=0)
    total_gstins = Column(Integer, nullable=False, default=0)
    batch_type = Column(String(20), nullable=True)  # INCREMENTAL / FULL
    created_at = Column(DateTime, nullable=False, server_default=func.now())
