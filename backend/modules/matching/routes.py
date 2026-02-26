"""
Matching Module — FastAPI Routes

Prefix: ``/api/matching``

Invoice matching engine: run matches, view results, manage exceptions.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user
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

@router.get("/results", response_model=List[MatchResultResponse])
async def list_results(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> List[MatchResultResponse]:
    """List all match results."""
    items = await service.list_match_results(db)
    return [MatchResultResponse.model_validate(i) for i in items]


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
    _user: Dict[str, Any] = Depends(get_current_user),
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

@router.get("/exceptions", response_model=List[MatchingExceptionResponse])
async def list_exceptions(
    open_only: bool = Query(True, description="Only show unresolved exceptions"),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> List[MatchingExceptionResponse]:
    """List matching exceptions (exception queue)."""
    items = await service.list_exceptions(db, open_only=open_only)
    return [MatchingExceptionResponse.model_validate(i) for i in items]


# ---------------------------------------------------------------------------
# POST  /api/matching/exceptions/{exc_id}/resolve
# ---------------------------------------------------------------------------

@router.post("/exceptions/{exc_id}/resolve", response_model=MatchingExceptionResponse)
async def resolve_exception(
    exc_id: str,
    body: ResolveExceptionRequest,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
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
