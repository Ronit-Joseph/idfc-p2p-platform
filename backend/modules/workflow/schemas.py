"""
Workflow Module — Pydantic Schemas

Request/response shapes for approval matrices, instances, and steps.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Approval Matrix
# ---------------------------------------------------------------------------

class ApprovalMatrixResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_type: str
    department: Optional[str] = None
    category: Optional[str] = None
    min_amount: float
    max_amount: float
    approver_role: str
    level: int
    is_active: bool


class ApprovalMatrixCreate(BaseModel):
    entity_type: str  # PR / PO / INVOICE
    department: Optional[str] = None
    category: Optional[str] = None
    min_amount: float = 0
    max_amount: float = 0
    approver_role: str
    level: int = 1
    is_active: bool = True


# ---------------------------------------------------------------------------
# Approval Step
# ---------------------------------------------------------------------------

class ApprovalStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    level: int
    approver_role: str
    approver_name: Optional[str] = None
    status: str
    comments: Optional[str] = None
    acted_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Approval Instance
# ---------------------------------------------------------------------------

class ApprovalInstanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_type: str
    entity_id: str
    department: Optional[str] = None
    amount: float
    total_levels: int
    current_level: int
    status: str
    requested_by: Optional[str] = None
    steps: List[ApprovalStepResponse] = []
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class ApprovalRequestCreate(BaseModel):
    entity_type: str  # PR / PO / INVOICE
    entity_id: str    # e.g. "PR2024-001"
    entity_ref: Optional[str] = None  # UUID reference
    department: Optional[str] = None
    amount: float = 0
    requested_by: Optional[str] = None


class ApprovalActionRequest(BaseModel):
    comments: Optional[str] = None
