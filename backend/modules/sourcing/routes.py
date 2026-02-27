"""
Sourcing Module — API Routes

Endpoints: list RFQs, detail, create, publish, add response, award, comparison.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db
from backend.modules.sourcing import service
from backend.modules.sourcing.schemas import RFQCreate, RFQResponseCreate

router = APIRouter(prefix="/api/sourcing", tags=["sourcing"])


def _rfq_dict(r):
    return {
        "id": r.rfq_number,
        "rfq_number": r.rfq_number,
        "title": r.title,
        "status": r.status,
        "category": r.category,
        "department": r.department,
        "budget_estimate": r.budget_estimate,
        "submission_deadline": r.submission_deadline,
        "evaluation_criteria": r.evaluation_criteria,
        "created_by": r.created_by,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _resp_dict(r):
    return {
        "id": r.id,
        "supplier_name": r.supplier_name,
        "quoted_amount": r.quoted_amount,
        "delivery_timeline": r.delivery_timeline,
        "technical_score": r.technical_score,
        "commercial_score": r.commercial_score,
        "total_score": r.total_score,
        "status": r.status,
        "notes": r.notes,
        "submitted_at": r.submitted_at,
    }


@router.get("/rfqs")
async def list_rfqs(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    rfqs = await service.list_rfqs(db, status=status)
    items = [_rfq_dict(r) for r in rfqs]

    # Get response counts per RFQ
    for item in items:
        rfq = await service.get_rfq(db, item["rfq_number"])
        responses = await service.get_rfq_responses(db, item["rfq_number"])
        item["response_count"] = len(responses)

    return {
        "rfqs": items,
        "summary": {
            "total": len(rfqs),
            "draft": len([r for r in rfqs if r.status == "DRAFT"]),
            "published": len([r for r in rfqs if r.status == "PUBLISHED"]),
            "evaluation": len([r for r in rfqs if r.status == "EVALUATION"]),
            "awarded": len([r for r in rfqs if r.status == "AWARDED"]),
        },
    }


@router.get("/rfqs/{rfq_id}")
async def get_rfq(rfq_id: str, db: AsyncSession = Depends(get_db)):
    rfq = await service.get_rfq(db, rfq_id)
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    responses = await service.get_rfq_responses(db, rfq_id)
    result = _rfq_dict(rfq)
    result["responses"] = [_resp_dict(r) for r in responses]
    return result


@router.post("/rfqs", status_code=201)
async def create_rfq(body: RFQCreate, db: AsyncSession = Depends(get_db)):
    rfq = await service.create_rfq(db, body.model_dump())
    return {"id": rfq.rfq_number, "rfq_number": rfq.rfq_number, "status": rfq.status}


@router.post("/rfqs/{rfq_id}/publish")
async def publish_rfq(rfq_id: str, db: AsyncSession = Depends(get_db)):
    rfq = await service.publish_rfq(db, rfq_id)
    if not rfq:
        raise HTTPException(status_code=400, detail="Cannot publish (not in DRAFT status or not found)")
    return {"id": rfq.rfq_number, "status": "PUBLISHED"}


@router.post("/rfqs/{rfq_id}/responses")
async def add_response(rfq_id: str, body: RFQResponseCreate, db: AsyncSession = Depends(get_db)):
    resp = await service.add_response(db, rfq_id, body.model_dump())
    if not resp:
        raise HTTPException(status_code=404, detail="RFQ not found")
    return _resp_dict(resp)


@router.post("/rfqs/{rfq_id}/award")
async def award_rfq(rfq_id: str, response_id: str, db: AsyncSession = Depends(get_db)):
    rfq = await service.award_rfq(db, rfq_id, response_id)
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    return {"id": rfq.rfq_number, "status": "AWARDED"}


@router.get("/rfqs/{rfq_id}/comparison")
async def bid_comparison(rfq_id: str, db: AsyncSession = Depends(get_db)):
    rfq = await service.get_rfq(db, rfq_id)
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    responses = await service.get_rfq_responses(db, rfq_id)
    return {
        "rfq": _rfq_dict(rfq),
        "bids": [_resp_dict(r) for r in responses],
        "criteria": rfq.evaluation_criteria or [],
    }
