"""
Sourcing Module — Business Logic
"""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.sourcing.models import RFQ, RFQResponse


def _next_rfq_number(count: int) -> str:
    return f"RFQ2024-{count + 1:03d}"


async def list_rfqs(db: AsyncSession, status: Optional[str] = None) -> List[RFQ]:
    q = select(RFQ).order_by(RFQ.rfq_number)
    if status:
        q = q.where(RFQ.status == status.upper())
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_rfq(db: AsyncSession, rfq_id: str) -> Optional[RFQ]:
    result = await db.execute(
        select(RFQ).where((RFQ.id == rfq_id) | (RFQ.rfq_number == rfq_id))
    )
    return result.scalars().first()


async def get_rfq_responses(db: AsyncSession, rfq_id: str) -> List[RFQResponse]:
    rfq = await get_rfq(db, rfq_id)
    if not rfq:
        return []
    result = await db.execute(
        select(RFQResponse).where(RFQResponse.rfq_id == rfq.id).order_by(RFQResponse.total_score.desc())
    )
    return list(result.scalars().all())


async def create_rfq(db: AsyncSession, data: dict) -> RFQ:
    count_result = await db.execute(select(RFQ))
    count = len(list(count_result.scalars().all()))
    rfq = RFQ(
        id=str(uuid.uuid4()),
        rfq_number=_next_rfq_number(count),
        **data,
    )
    db.add(rfq)
    await db.commit()
    await db.refresh(rfq)
    return rfq


async def publish_rfq(db: AsyncSession, rfq_id: str) -> Optional[RFQ]:
    rfq = await get_rfq(db, rfq_id)
    if not rfq or rfq.status != "DRAFT":
        return None
    rfq.status = "PUBLISHED"
    await db.commit()
    await db.refresh(rfq)
    return rfq


async def add_response(db: AsyncSession, rfq_id: str, data: dict) -> Optional[RFQResponse]:
    rfq = await get_rfq(db, rfq_id)
    if not rfq:
        return None
    tech = data.get("technical_score") or 0
    comm = data.get("commercial_score") or 0
    total = round(tech * 0.6 + comm * 0.4, 1)  # 60/40 weighting
    resp = RFQResponse(
        id=str(uuid.uuid4()),
        rfq_id=rfq.id,
        total_score=total,
        submitted_at=data.pop("submitted_at", None),
        **data,
    )
    db.add(resp)
    await db.commit()
    await db.refresh(resp)
    return resp


async def award_rfq(db: AsyncSession, rfq_id: str, response_id: str) -> Optional[RFQ]:
    rfq = await get_rfq(db, rfq_id)
    if not rfq:
        return None
    # Mark all responses
    responses = await get_rfq_responses(db, rfq_id)
    for r in responses:
        r.status = "AWARDED" if r.id == response_id else "REJECTED"
    rfq.status = "AWARDED"
    await db.commit()
    await db.refresh(rfq)
    return rfq
