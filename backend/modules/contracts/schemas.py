"""
Contracts Module — Pydantic Schemas
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ContractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    contract_number: str
    title: str
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    contract_type: str
    status: str = "DRAFT"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    value: Optional[float] = 0
    currency: str = "INR"
    auto_renew: bool = False
    renewal_notice_days: Optional[int] = 30
    department: Optional[str] = None
    owner: Optional[str] = None
    terms_summary: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ContractCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    supplier_name: Optional[str] = None
    contract_type: str = Field(..., pattern="^(MSA|SOW|NDA|SLA|AMENDMENT)$")
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    value: Optional[float] = 0
    currency: str = "INR"
    auto_renew: bool = False
    renewal_notice_days: Optional[int] = 30
    department: Optional[str] = None
    owner: Optional[str] = None
    terms_summary: Optional[str] = None


class ContractUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    end_date: Optional[str] = None
    value: Optional[float] = None
    auto_renew: Optional[bool] = None
    renewal_notice_days: Optional[int] = None
    owner: Optional[str] = None
    terms_summary: Optional[str] = None
