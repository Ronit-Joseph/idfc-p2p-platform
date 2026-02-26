"""
Audit Module — Pydantic Schemas

Response shapes for audit log entries. Append-only — no create/update schemas
exposed to API consumers (audit logs are created internally by the event bus).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    source_module: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    actor: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None


class AuditSummaryResponse(BaseModel):
    total_events: int
    by_module: Dict[str, int]
    by_event_type: Dict[str, int]
    recent_events: int  # last 24h
