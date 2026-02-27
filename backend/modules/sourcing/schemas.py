"""
Sourcing Module — Pydantic Schemas
"""

from __future__ import annotations

from typing import Optional, List, Any
from pydantic import BaseModel, Field


class RFQCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = None
    department: Optional[str] = None
    budget_estimate: Optional[float] = 0
    submission_deadline: Optional[str] = None
    evaluation_criteria: Optional[List[Any]] = None
    created_by: Optional[str] = None


class RFQResponseCreate(BaseModel):
    supplier_name: str
    quoted_amount: Optional[float] = 0
    delivery_timeline: Optional[str] = None
    technical_score: Optional[float] = None
    commercial_score: Optional[float] = None
    notes: Optional[str] = None
