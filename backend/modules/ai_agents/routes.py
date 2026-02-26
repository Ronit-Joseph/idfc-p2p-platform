"""
AI Agents Module — FastAPI Routes

Prefix: ``/api/ai-agents``

Provides endpoints for listing AI agent insights and applying
recommended actions.  The five AI agents (InvoiceCodingAgent,
FraudDetectionAgent, SLAPredictionAgent, CashOptimizationAgent,
RiskAgent) generate insights that are stored in the ``ai_insights``
table and surfaced through these endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user
from backend.modules.ai_agents.schemas import AIInsightResponse, AIInsightApplyResponse
from backend.modules.ai_agents import service

router = APIRouter(prefix="/api/ai-agents", tags=["ai-agents"])


# ---------------------------------------------------------------------------
# GET  /api/ai-agents/insights
# ---------------------------------------------------------------------------

@router.get("/insights", response_model=List[AIInsightResponse])
async def list_insights(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> List[AIInsightResponse]:
    """Return all AI agent insights.

    Each insight's ``id`` field corresponds to the ``insight_code`` column
    (e.g. "AI001") and ``type`` corresponds to ``insight_type`` to match
    the legacy API contract.
    """
    insights = await service.list_insights(db)
    return [AIInsightResponse.model_validate(i) for i in insights]


# ---------------------------------------------------------------------------
# POST /api/ai-agents/insights/{insight_id}/apply
# ---------------------------------------------------------------------------

@router.post("/insights/{insight_id}/apply", response_model=AIInsightApplyResponse)
async def apply_insight(
    insight_id: str,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> AIInsightApplyResponse:
    """Apply an AI agent insight / recommendation.

    Marks the insight as applied by setting ``applied=True``,
    ``applied_at`` to the current timestamp, and ``status`` to "APPLIED".

    Path parameters:
    - **insight_id**: the insight code (e.g. "AI001")
    """
    result = await service.apply_insight(db, insight_id)
    return AIInsightApplyResponse.model_validate(result)
