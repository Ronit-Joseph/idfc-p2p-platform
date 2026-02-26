"""
EBS Integration Module — Pydantic Schemas

Defines response models for the Oracle EBS Integration API.

The legacy frontend expects ``event_code`` (e.g. "EBS001") as the ``id``
field in all API responses.  ``EBSEventResponse`` therefore exposes an
``id`` field mapped from the database ``event_code`` column so that the
frontend contract is preserved — the actual UUID primary key is excluded.

``EBSRetryResponse`` is returned by the retry endpoint and includes the
``message`` field expected by the legacy shape.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# EBS event response (list endpoint)
# ---------------------------------------------------------------------------

class EBSEventResponse(BaseModel):
    """Single EBS integration event — uses legacy field names.

    ``id`` is always equal to ``event_code`` (e.g. "EBS001") — the
    frontend expects this.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(
        ...,
        description="Same as event_code — the human-readable event identifier.",
    )
    event_type: str
    entity_id: Optional[str] = None
    entity_ref: Optional[str] = None
    description: Optional[str] = None
    gl_account: Optional[str] = None
    amount: Optional[float] = None
    ebs_module: str
    status: str
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    ebs_ref: Optional[str] = None
    error_message: Optional[str] = None

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


# ---------------------------------------------------------------------------
# EBS retry response
# ---------------------------------------------------------------------------

class EBSRetryResponse(BaseModel):
    """Response returned by the retry endpoint.

    Includes a human-readable ``message`` field alongside the core
    event fields.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(
        ...,
        description="Same as event_code — the human-readable event identifier.",
    )
    status: str
    retry_count: int
    message: str
