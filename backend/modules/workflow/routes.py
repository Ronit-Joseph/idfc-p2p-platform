"""
Workflow Module — FastAPI Routes

Prefix: ``/api/workflow``

Approval matrix management and approval instance lifecycle.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user
from backend.modules.workflow.schemas import (
    ApprovalMatrixResponse,
    ApprovalMatrixCreate,
    ApprovalInstanceResponse,
    ApprovalRequestCreate,
    ApprovalActionRequest,
)
from backend.modules.workflow import service

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


# ---------------------------------------------------------------------------
# GET  /api/workflow/matrices
# ---------------------------------------------------------------------------

@router.get("/matrices", response_model=List[ApprovalMatrixResponse])
async def list_matrices(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> List[ApprovalMatrixResponse]:
    """Return all approval matrix rules."""
    matrices = await service.list_matrices(db)
    return [ApprovalMatrixResponse.model_validate(m) for m in matrices]


# ---------------------------------------------------------------------------
# POST  /api/workflow/matrices
# ---------------------------------------------------------------------------

@router.post("/matrices", response_model=ApprovalMatrixResponse, status_code=201)
async def create_matrix(
    body: ApprovalMatrixCreate,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> ApprovalMatrixResponse:
    """Create a new approval matrix rule."""
    result = await service.create_matrix(db, body.model_dump())
    return ApprovalMatrixResponse.model_validate(result)


# ---------------------------------------------------------------------------
# GET  /api/workflow/pending
# ---------------------------------------------------------------------------

@router.get("/pending", response_model=List[ApprovalInstanceResponse])
async def list_pending(
    role: Optional[str] = Query(None, description="Filter by approver role"),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> List[ApprovalInstanceResponse]:
    """List all pending approval requests, optionally by role."""
    items = await service.list_pending_approvals(db, approver_role=role)
    return [ApprovalInstanceResponse.model_validate(i) for i in items]


# ---------------------------------------------------------------------------
# POST  /api/workflow/request
# ---------------------------------------------------------------------------

@router.post("/request", response_model=ApprovalInstanceResponse, status_code=201)
async def create_approval_request(
    body: ApprovalRequestCreate,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
) -> ApprovalInstanceResponse:
    """Submit an entity for approval."""
    result = await service.create_approval_request(
        db,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        department=body.department,
        amount=body.amount,
        requested_by=body.requested_by or user.get("name", "Unknown"),
        entity_ref=body.entity_ref,
    )
    return ApprovalInstanceResponse.model_validate(result)


# ---------------------------------------------------------------------------
# GET  /api/workflow/instances/{instance_id}
# ---------------------------------------------------------------------------

@router.get("/instances/{instance_id}", response_model=ApprovalInstanceResponse)
async def get_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> ApprovalInstanceResponse:
    """Get a specific approval instance with its steps."""
    result = await service.get_approval_instance(db, instance_id)
    if not result:
        raise HTTPException(status_code=404, detail="Approval instance not found")
    return ApprovalInstanceResponse.model_validate(result)


# ---------------------------------------------------------------------------
# GET  /api/workflow/entity/{entity_type}/{entity_id}
# ---------------------------------------------------------------------------

@router.get("/entity/{entity_type}/{entity_id}", response_model=ApprovalInstanceResponse)
async def get_by_entity(
    entity_type: str,
    entity_id: str,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> ApprovalInstanceResponse:
    """Get the latest approval instance for an entity."""
    result = await service.get_approval_by_entity(db, entity_type, entity_id)
    if not result:
        raise HTTPException(status_code=404, detail="No approval found for this entity")
    return ApprovalInstanceResponse.model_validate(result)


# ---------------------------------------------------------------------------
# POST  /api/workflow/instances/{instance_id}/approve
# ---------------------------------------------------------------------------

@router.post("/instances/{instance_id}/approve", response_model=ApprovalInstanceResponse)
async def approve(
    instance_id: str,
    body: ApprovalActionRequest,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
) -> ApprovalInstanceResponse:
    """Approve the current step of an approval instance."""
    try:
        result = await service.approve_step(
            db, instance_id,
            approver_name=user.get("name", "Unknown"),
            comments=body.comments,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return ApprovalInstanceResponse.model_validate(result)


# ---------------------------------------------------------------------------
# POST  /api/workflow/instances/{instance_id}/reject
# ---------------------------------------------------------------------------

@router.post("/instances/{instance_id}/reject", response_model=ApprovalInstanceResponse)
async def reject(
    instance_id: str,
    body: ApprovalActionRequest,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
) -> ApprovalInstanceResponse:
    """Reject the current step — entire approval is rejected."""
    try:
        result = await service.reject_step(
            db, instance_id,
            approver_name=user.get("name", "Unknown"),
            comments=body.comments,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return ApprovalInstanceResponse.model_validate(result)
