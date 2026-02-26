"""
AI Agents Module — Pydantic Schemas

Defines response models for the AI Agents API.

The legacy frontend expects ``insight_code`` (e.g. "AI001") as the ``id``
field and ``insight_type`` as the ``type`` field in all API responses.
``AIInsightResponse`` therefore maps these columns so that the frontend
contract is preserved — the actual UUID primary key is excluded.

``AIInsightApplyResponse`` is returned by the apply endpoint and includes
only the fields the frontend needs to confirm the action.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# AI insight response (list endpoint)
# ---------------------------------------------------------------------------

class AIInsightResponse(BaseModel):
    """Single AI insight — uses legacy field names.

    ``id`` is always equal to ``insight_code`` (e.g. "AI001") and ``type``
    is always equal to ``insight_type`` — the frontend expects this.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(
        ...,
        description="Same as insight_code — the human-readable insight identifier.",
    )
    agent: str
    invoice_id: Optional[str] = None
    supplier_id: Optional[str] = None
    type: str = Field(
        ...,
        description="Same as insight_type — e.g. GL_CODING, FRAUD_ALERT.",
    )
    confidence: Optional[float] = None
    recommendation: Optional[str] = None
    reasoning: Optional[str] = None
    applied: bool
    applied_at: Optional[datetime] = None
    status: str

    @model_validator(mode="before")
    @classmethod
    def _remap_legacy_fields(cls, data: Any) -> Any:
        """Map ``insight_code`` -> ``id`` and ``insight_type`` -> ``type``."""
        if hasattr(data, "__dict__"):
            d = {k: v for k, v in data.__dict__.items() if not k.startswith("_")}
            d["id"] = d.get("insight_code", d.get("id"))
            d["type"] = d.get("insight_type", d.get("type"))
            return d
        if isinstance(data, dict):
            data["id"] = data.get("insight_code", data.get("id"))
            data["type"] = data.get("insight_type", data.get("type"))
            return data
        return data


# ---------------------------------------------------------------------------
# AI insight apply response
# ---------------------------------------------------------------------------

class AIInsightApplyResponse(BaseModel):
    """Response returned by the apply endpoint.

    Confirms the insight was applied with the updated status and timestamp.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(
        ...,
        description="Same as insight_code — the human-readable insight identifier.",
    )
    status: str
    applied: bool
    applied_at: Optional[datetime] = None
