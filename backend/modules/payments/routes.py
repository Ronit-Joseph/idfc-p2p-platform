"""
Payments Module — FastAPI Routes

Prefix: ``/api/payments``

Payment runs, individual payments, and bank file management.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user
from backend.modules.payments.schemas import (
    PaymentResponse,
    PaymentRunResponse,
    PaymentSummaryResponse,
    CreatePaymentRunRequest,
)
from backend.modules.payments import service

router = APIRouter(prefix="/api/payments", tags=["payments"])


# ---------------------------------------------------------------------------
# GET  /api/payments
# ---------------------------------------------------------------------------

@router.get("", response_model=List[PaymentResponse])
async def list_payments(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> List[PaymentResponse]:
    """List all individual payments."""
    items = await service.list_payments(db)
    return [PaymentResponse.model_validate(i) for i in items]


# ---------------------------------------------------------------------------
# GET  /api/payments/summary
# ---------------------------------------------------------------------------

@router.get("/summary", response_model=PaymentSummaryResponse)
async def payment_summary(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> PaymentSummaryResponse:
    """Payment summary statistics."""
    summary = await service.get_payment_summary(db)
    return PaymentSummaryResponse(**summary)


# ---------------------------------------------------------------------------
# GET  /api/payments/runs
# ---------------------------------------------------------------------------

@router.get("/runs", response_model=List[PaymentRunResponse])
async def list_runs(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> List[PaymentRunResponse]:
    """List all payment runs."""
    items = await service.list_payment_runs(db)
    return [PaymentRunResponse.model_validate(i) for i in items]


# ---------------------------------------------------------------------------
# POST  /api/payments/runs
# ---------------------------------------------------------------------------

@router.post("/runs", response_model=PaymentRunResponse, status_code=201)
async def create_run(
    body: CreatePaymentRunRequest,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
) -> PaymentRunResponse:
    """Create a new payment run for a batch of invoices."""
    try:
        result = await service.create_payment_run(
            db,
            invoice_numbers=body.invoice_ids,
            payment_method=body.payment_method,
            initiated_by=user.get("name", "Unknown"),
            notes=body.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return PaymentRunResponse.model_validate(result)


# ---------------------------------------------------------------------------
# POST  /api/payments/runs/{run_number}/process
# ---------------------------------------------------------------------------

@router.post("/runs/{run_number}/process", response_model=PaymentRunResponse)
async def process_run(
    run_number: str,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
) -> PaymentRunResponse:
    """Advance a payment run one step (DRAFT→SCHEDULED→PROCESSING→COMPLETED)."""
    try:
        result = await service.process_payment_run(
            db, run_number,
            approved_by=user.get("name", "Unknown"),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return PaymentRunResponse.model_validate(result)
