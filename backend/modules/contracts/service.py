"""
Contracts Module — Business Logic
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.contracts.models import Contract


def _next_contract_number(existing_count: int) -> str:
    return f"CTR2024-{existing_count + 1:03d}"


async def list_contracts(
    db: AsyncSession,
    status: Optional[str] = None,
    contract_type: Optional[str] = None,
) -> List[Contract]:
    q = select(Contract).order_by(Contract.contract_number)
    if status:
        q = q.where(Contract.status == status.upper())
    if contract_type:
        q = q.where(Contract.contract_type == contract_type.upper())
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_contract(db: AsyncSession, contract_id: str) -> Optional[Contract]:
    result = await db.execute(
        select(Contract).where(
            (Contract.id == contract_id) | (Contract.contract_number == contract_id)
        )
    )
    return result.scalars().first()


async def create_contract(db: AsyncSession, data: dict) -> Contract:
    count_result = await db.execute(select(Contract))
    count = len(list(count_result.scalars().all()))
    contract = Contract(
        id=str(uuid.uuid4()),
        contract_number=_next_contract_number(count),
        **data,
    )
    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    return contract


async def update_contract(db: AsyncSession, contract_id: str, data: dict) -> Optional[Contract]:
    contract = await get_contract(db, contract_id)
    if not contract:
        return None
    for k, v in data.items():
        if v is not None:
            setattr(contract, k, v)
    await db.commit()
    await db.refresh(contract)
    return contract


async def terminate_contract(db: AsyncSession, contract_id: str) -> Optional[Contract]:
    contract = await get_contract(db, contract_id)
    if not contract:
        return None
    contract.status = "TERMINATED"
    await db.commit()
    await db.refresh(contract)
    return contract


async def get_expiring_contracts(db: AsyncSession, days: int = 30) -> List[Contract]:
    """Contracts expiring within N days."""
    result = await db.execute(
        select(Contract).where(Contract.status == "ACTIVE")
    )
    contracts = list(result.scalars().all())
    cutoff = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    return [c for c in contracts if c.end_date and today <= c.end_date <= cutoff]
