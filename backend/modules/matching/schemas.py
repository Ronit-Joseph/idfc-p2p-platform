"""
Matching Module — Pydantic Schemas

Request/response shapes for match results and exception handling.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class MatchResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_id: str
    invoice_number: Optional[str] = None
    supplier_name: Optional[str] = None
    match_type: str
    status: str
    variance_pct: Optional[float] = None
    exception_reason: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[str] = None


class MatchingExceptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    match_result_id: str
    invoice_id: str
    invoice_number: Optional[str] = None
    supplier_name: Optional[str] = None
    exception_type: str
    severity: str
    description: Optional[str] = None
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: Optional[str] = None


class RunMatchRequest(BaseModel):
    match_type: str = "3WAY"  # 2WAY or 3WAY


class ResolveExceptionRequest(BaseModel):
    resolution: str  # APPROVED_OVERRIDE / REJECTED / ESCALATED
    resolution_notes: Optional[str] = None


class MatchSummaryResponse(BaseModel):
    total_matches: int
    passed: int
    exceptions: int
    blocked_fraud: int
    pending: int
    open_exceptions: int
