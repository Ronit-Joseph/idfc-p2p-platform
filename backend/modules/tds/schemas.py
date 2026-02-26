"""
TDS Management Module — Pydantic Schemas
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class TDSDeductionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_id: Optional[str] = None
    invoice_number: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    pan: Optional[str] = None
    section: str
    tds_rate: float
    base_amount: float
    tds_amount: float
    surcharge: float
    cess: float
    total_tds: float
    status: str
    fiscal_year: str
    quarter: str
    challan_number: Optional[str] = None
    deposit_date: Optional[str] = None
    bsr_code: Optional[str] = None
    certificate_number: Optional[str] = None
    form16a_generated: str
    form16a_issued_date: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None


class TDSCreateRequest(BaseModel):
    invoice_number: str
    section: str
    tds_rate: Optional[float] = None  # auto-calculate if not provided


class TDSSummaryResponse(BaseModel):
    total_deductions: int
    total_tds_amount: float
    pending_deposit: int
    pending_deposit_amount: float
    deposited: int
    return_filed: int
    form16a_pending: int


class TDSQuarterSummaryResponse(BaseModel):
    fiscal_year: str
    quarter: str
    total_deductions: int
    total_tds: float
    deposited: int
    return_filed: bool
