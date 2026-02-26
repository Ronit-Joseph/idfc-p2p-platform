"""
GST Cache Module — Pydantic Schemas

Defines response models for the GST Cache API.

The legacy frontend expects the exact field names stored in the ``gst_records``
table, so no column-name translation is needed (unlike the Budgets module).
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Record-level response
# ---------------------------------------------------------------------------

class GSTRecordResponse(BaseModel):
    """Single cached GSTIN record returned by the list endpoint.

    Field names map 1-to-1 with the ``gst_records`` table columns that
    the legacy frontend consumes.
    """

    model_config = ConfigDict(from_attributes=True)

    gstin: str
    legal_name: str
    status: str
    state: Optional[str] = None
    registration_type: Optional[str] = None
    last_gstr1_filed: Optional[str] = None
    gstr2b_available: bool
    gstr2b_period: Optional[str] = None
    gstr1_compliance: Optional[str] = None
    itc_eligible: bool
    last_synced: Optional[str] = None
    sync_source: Optional[str] = None
    cache_hit_count: int
    gstr2b_alert: Optional[str] = None
    itc_note: Optional[str] = None


# ---------------------------------------------------------------------------
# Summary / aggregate
# ---------------------------------------------------------------------------

class GSTCacheSummary(BaseModel):
    """Aggregate counts returned alongside the record list."""

    total_gstins: int
    active: int
    issues: int
    last_full_sync: Optional[str] = None
    sync_source: str = "Cygnet GSP"


# ---------------------------------------------------------------------------
# Composite list response
# ---------------------------------------------------------------------------

class GSTCacheListResponse(BaseModel):
    """Envelope wrapping records + summary for ``GET /api/gst-cache``."""

    records: List[GSTRecordResponse]
    summary: GSTCacheSummary


# ---------------------------------------------------------------------------
# Sync response
# ---------------------------------------------------------------------------

class GSTSyncResponse(BaseModel):
    """Result returned by ``POST /api/gst-cache/sync``."""

    status: str
    records_updated: int
    timestamp: str
