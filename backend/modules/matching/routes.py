"""
Matching Module — FastAPI Routes

Prefix: ``/api/matching``

Invoice matching engine: run matches, view results, manage exceptions.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user, require_role, paginate
from backend.modules.matching.schemas import (
    MatchResultResponse,
    MatchingExceptionResponse,
    MatchSummaryResponse,
    RunMatchRequest,
    ResolveExceptionRequest,
)
from backend.modules.matching import service

router = APIRouter(prefix="/api/matching", tags=["matching"])


# ---------------------------------------------------------------------------
# GET  /api/matching/results
# ---------------------------------------------------------------------------

@router.get("/results")
async def list_results(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """List all match results."""
    items = await service.list_match_results(db)
    results = [MatchResultResponse.model_validate(i) for i in items]
    return paginate(results, skip, limit)


# ---------------------------------------------------------------------------
# GET  /api/matching/summary
# ---------------------------------------------------------------------------

@router.get("/summary", response_model=MatchSummaryResponse)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> MatchSummaryResponse:
    """Return matching summary statistics."""
    summary = await service.get_match_summary(db)
    return MatchSummaryResponse(**summary)


# ---------------------------------------------------------------------------
# POST  /api/matching/run/{invoice_id}
# ---------------------------------------------------------------------------

@router.post("/run/{invoice_id}", response_model=MatchResultResponse)
async def run_match(
    invoice_id: str,
    body: RunMatchRequest,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(require_role("PROCUREMENT_MANAGER")),
) -> MatchResultResponse:
    """Run 2-way or 3-way matching for an invoice."""
    try:
        result = await service.run_match(db, invoice_id, match_type=body.match_type)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return MatchResultResponse.model_validate(result)


# ---------------------------------------------------------------------------
# GET  /api/matching/exceptions
# ---------------------------------------------------------------------------

@router.get("/exceptions")
async def list_exceptions(
    open_only: bool = Query(True, description="Only show unresolved exceptions"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """List matching exceptions (exception queue)."""
    items = await service.list_exceptions(db, open_only=open_only)
    results = [MatchingExceptionResponse.model_validate(i) for i in items]
    return paginate(results, skip, limit)


# ---------------------------------------------------------------------------
# POST  /api/matching/exceptions/{exc_id}/resolve
# ---------------------------------------------------------------------------

@router.post("/exceptions/{exc_id}/resolve", response_model=MatchingExceptionResponse)
async def resolve_exception(
    exc_id: str,
    body: ResolveExceptionRequest,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role("FINANCE_HEAD")),
) -> MatchingExceptionResponse:
    """Resolve a matching exception."""
    try:
        result = await service.resolve_exception(
            db, exc_id,
            resolution=body.resolution,
            resolved_by=user.get("name", "Unknown"),
            resolution_notes=body.resolution_notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return MatchingExceptionResponse.model_validate(result)
