"""
Payments Module — Pydantic Schemas
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    payment_number: str
    invoice_id: Optional[str] = None
    invoice_number: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    amount: float
    tds_deducted: float
    net_amount: float
    currency: str
    payment_method: str
    status: str
    bank_reference: Optional[str] = None
    payment_date: Optional[str] = None
    ebs_voucher_ref: Optional[str] = None
    remittance_sent: str
    notes: Optional[str] = None
    created_at: Optional[str] = None


class PaymentRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_number: str
    payment_method: str
    status: str
    total_amount: float
    invoice_count: int
    bank_file_ref: Optional[str] = None
    initiated_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    completed_at: Optional[str] = None
    notes: Optional[str] = None
    payments: List[PaymentResponse] = []
    created_at: Optional[str] = None


class CreatePaymentRunRequest(BaseModel):
    payment_method: str = "NEFT"
    invoice_ids: List[str]  # invoice numbers
    notes: Optional[str] = None


class PaymentSummaryResponse(BaseModel):
    total_payments: int
    total_amount: float
    pending: int
    completed: int
    failed: int
    total_runs: int
