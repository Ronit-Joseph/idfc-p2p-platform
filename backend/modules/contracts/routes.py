"""
Contracts Module — API Routes

Endpoints: list, detail, create, update, terminate, expiring.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db
from backend.modules.contracts import service
from backend.modules.contracts.schemas import ContractCreate, ContractUpdate

router = APIRouter(prefix="/api/contracts", tags=["contracts"])


@router.get("")
async def list_contracts(
    status: Optional[str] = None,
    contract_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    contracts = await service.list_contracts(db, status=status, contract_type=contract_type)
    items = []
    for c in contracts:
        items.append({
            "id": c.contract_number,
            "contract_number": c.contract_number,
            "title": c.title,
            "supplier_name": c.supplier_name,
            "contract_type": c.contract_type,
            "status": c.status,
            "start_date": c.start_date,
            "end_date": c.end_date,
            "value": c.value,
            "currency": c.currency,
            "auto_renew": c.auto_renew,
            "renewal_notice_days": c.renewal_notice_days,
            "department": c.department,
            "owner": c.owner,
            "terms_summary": c.terms_summary,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    active = len([c for c in contracts if c.status == "ACTIVE"])
    draft = len([c for c in contracts if c.status == "DRAFT"])
    expired = len([c for c in contracts if c.status == "EXPIRED"])

    expiring = await service.get_expiring_contracts(db, days=30)

    return {
        "contracts": items,
        "summary": {
            "total": len(contracts),
            "active": active,
            "draft": draft,
            "expired": expired,
            "expiring_soon": len(expiring),
            "total_value": sum(c.value or 0 for c in contracts if c.status == "ACTIVE"),
        },
    }


@router.get("/expiring")
async def expiring_contracts(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    contracts = await service.get_expiring_contracts(db, days=days)
    return [{
        "id": c.contract_number,
        "contract_number": c.contract_number,
        "title": c.title,
        "supplier_name": c.supplier_name,
        "end_date": c.end_date,
        "value": c.value,
    } for c in contracts]


@router.get("/{contract_id}")
async def get_contract(contract_id: str, db: AsyncSession = Depends(get_db)):
    c = await service.get_contract(db, contract_id)
    if not c:
        raise HTTPException(status_code=404, detail="Contract not found")
    return {
        "id": c.contract_number,
        "contract_number": c.contract_number,
        "title": c.title,
        "supplier_name": c.supplier_name,
        "contract_type": c.contract_type,
        "status": c.status,
        "start_date": c.start_date,
        "end_date": c.end_date,
        "value": c.value,
        "currency": c.currency,
        "auto_renew": c.auto_renew,
        "renewal_notice_days": c.renewal_notice_days,
        "department": c.department,
        "owner": c.owner,
        "terms_summary": c.terms_summary,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@router.post("", status_code=201)
async def create_contract(body: ContractCreate, db: AsyncSession = Depends(get_db)):
    c = await service.create_contract(db, body.model_dump())
    return {"id": c.contract_number, "contract_number": c.contract_number, "status": c.status}


@router.patch("/{contract_id}")
async def update_contract(contract_id: str, body: ContractUpdate, db: AsyncSession = Depends(get_db)):
    c = await service.update_contract(db, contract_id, body.model_dump(exclude_unset=True))
    if not c:
        raise HTTPException(status_code=404, detail="Contract not found")
    return {"id": c.contract_number, "status": c.status}


@router.post("/{contract_id}/terminate")
async def terminate_contract(contract_id: str, db: AsyncSession = Depends(get_db)):
    c = await service.terminate_contract(db, contract_id)
    if not c:
        raise HTTPException(status_code=404, detail="Contract not found")
    return {"id": c.contract_number, "status": "TERMINATED"}
