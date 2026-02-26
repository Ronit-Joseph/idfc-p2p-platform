"""
TDS Management Module — FastAPI Routes

Prefix: ``/api/tds``

TDS deduction tracking, deposit recording, and Form 16A management.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user
from backend.modules.tds.schemas import (
    TDSDeductionResponse,
    TDSCreateRequest,
    TDSSummaryResponse,
)
from backend.modules.tds import service

router = APIRouter(prefix="/api/tds", tags=["tds"])


# ---------------------------------------------------------------------------
# GET  /api/tds
# ---------------------------------------------------------------------------

@router.get("", response_model=List[TDSDeductionResponse])
async def list_deductions(
    fiscal_year: Optional[str] = Query(None),
    quarter: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> List[TDSDeductionResponse]:
    """List TDS deductions with optional filters."""
    items = await service.list_deductions(db, fiscal_year=fiscal_year, quarter=quarter, status=status)
    return [TDSDeductionResponse.model_validate(i) for i in items]


# ---------------------------------------------------------------------------
# GET  /api/tds/summary
# ---------------------------------------------------------------------------

@router.get("/summary", response_model=TDSSummaryResponse)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> TDSSummaryResponse:
    """TDS summary statistics."""
    summary = await service.get_tds_summary(db)
    return TDSSummaryResponse(**summary)


# ---------------------------------------------------------------------------
# POST  /api/tds
# ---------------------------------------------------------------------------

@router.post("", response_model=TDSDeductionResponse, status_code=201)
async def create_deduction(
    body: TDSCreateRequest,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> TDSDeductionResponse:
    """Create a TDS deduction for an invoice."""
    try:
        result = await service.create_tds_deduction(
            db, body.invoice_number, body.section, body.tds_rate,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return TDSDeductionResponse.model_validate(result)


# ---------------------------------------------------------------------------
# POST  /api/tds/{deduction_id}/deposit
# ---------------------------------------------------------------------------

@router.post("/{deduction_id}/deposit", response_model=TDSDeductionResponse)
async def deposit(
    deduction_id: str,
    challan_number: str = Query(..., description="Government challan number"),
    bsr_code: Optional[str] = Query(None, description="BSR code"),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> TDSDeductionResponse:
    """Record TDS deposit against a challan."""
    try:
        result = await service.deposit_tds(db, deduction_id, challan_number, bsr_code)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return TDSDeductionResponse.model_validate(result)


# ---------------------------------------------------------------------------
# POST  /api/tds/{deduction_id}/form16a
# ---------------------------------------------------------------------------

@router.post("/{deduction_id}/form16a", response_model=TDSDeductionResponse)
async def generate_form16a(
    deduction_id: str,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> TDSDeductionResponse:
    """Generate Form 16A certificate for a deposited TDS deduction."""
    try:
        result = await service.generate_form16a(db, deduction_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return TDSDeductionResponse.model_validate(result)


# ---------------------------------------------------------------------------
# GET  /api/tds/rates
# ---------------------------------------------------------------------------

@router.get("/rates")
async def tds_rates(
    _user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return TDS rate reference table by section."""
    return {"rates": service.TDS_RATES}
