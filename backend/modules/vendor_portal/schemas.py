"""
Vendor Portal Module — Pydantic Schemas

Defines response models for the Vendor Portal Integration API.

The legacy frontend expects ``event_code`` (e.g. "VPE001") as the ``id``
field in all API responses.  ``VendorPortalEventResponse`` therefore exposes
an ``id`` field mapped from the database ``event_code`` column so that the
frontend contract is preserved — the actual UUID primary key is excluded.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Vendor Portal event response (list endpoint)
# ---------------------------------------------------------------------------

class VendorPortalEventResponse(BaseModel):
    """Single Vendor Portal integration event — uses legacy field names.

    ``id`` is always equal to ``event_code`` (e.g. "VPE001") — the
    frontend expects this.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(
        ...,
        description="Same as event_code — the human-readable event identifier.",
    )
    event_type: str
    timestamp: Optional[datetime] = None
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    processed: bool = False
    p2p_action: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _set_id_to_event_code(cls, data: Any) -> Any:
        """Ensure ``id`` in the JSON output equals the ``event_code`` column."""
        if hasattr(data, "__dict__"):
            d = {k: v for k, v in data.__dict__.items() if not k.startswith("_")}
            d["id"] = d.get("event_code", d.get("id"))
            return d
        if isinstance(data, dict):
            data["id"] = data.get("event_code", data.get("id"))
            return data
        return data
