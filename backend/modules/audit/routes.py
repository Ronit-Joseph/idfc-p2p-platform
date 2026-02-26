"""
Audit Module — FastAPI Routes

Prefix: ``/api/audit``

Read-only access to the immutable audit trail.
Audit logs are created internally via the event bus — never by API consumers.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user
from backend.modules.audit.schemas import AuditLogResponse, AuditSummaryResponse
from backend.modules.audit import service

router = APIRouter(prefix="/api/audit", tags=["audit"])


# ---------------------------------------------------------------------------
# GET  /api/audit
# ---------------------------------------------------------------------------

@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (INVOICE, PR, PO, etc.)"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    source_module: Optional[str] = Query(None, description="Filter by source module"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> List[AuditLogResponse]:
    """Query audit logs with optional filters. RBI 7-year retention."""
    logs = await service.list_audit_logs(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        source_module=source_module,
        limit=limit,
        offset=offset,
    )
    return [AuditLogResponse.model_validate(log) for log in logs]


# ---------------------------------------------------------------------------
# GET  /api/audit/summary
# ---------------------------------------------------------------------------

@router.get("/summary", response_model=AuditSummaryResponse)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> AuditSummaryResponse:
    """Return summary statistics of the audit trail."""
    summary = await service.get_audit_summary(db)
    return AuditSummaryResponse(**summary)


# ---------------------------------------------------------------------------
# GET  /api/audit/entity/{entity_type}/{entity_id}
# ---------------------------------------------------------------------------

@router.get("/entity/{entity_type}/{entity_id}", response_model=List[AuditLogResponse])
async def entity_history(
    entity_type: str,
    entity_id: str,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> List[AuditLogResponse]:
    """Get full audit trail for a specific entity (e.g. all events for INV001)."""
    logs = await service.get_entity_history(db, entity_type, entity_id)
    return [AuditLogResponse.model_validate(log) for log in logs]
