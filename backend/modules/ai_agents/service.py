"""
AI Agents Module — Service Layer

Async business-logic operations against the ``ai_insights`` table.  All
database access for the AI-agents domain should go through these functions
so that routes (and future Kafka consumers) share one code-path.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.event_bus import Event, event_bus
from backend.exceptions import NotFoundError
from backend.modules.ai_agents.models import AIInsight


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

async def list_insights(db: AsyncSession) -> List[Dict[str, Any]]:
    """Return all AI insights as dicts with legacy field mappings.

    ``insight_code`` is mapped to ``id`` and ``insight_type`` is mapped to
    ``type`` so that the response matches the legacy API contract.

    The ``invoice_id`` and ``supplier_id`` fields already store human-readable
    codes (e.g. "INV001", "SUP009") rather than UUIDs, so they are passed
    through as-is.

    Results are ordered by ``created_at`` descending so the most recent
    insights appear first.
    """
    result = await db.execute(
        select(AIInsight).order_by(AIInsight.created_at.desc())
    )
    insights = list(result.scalars().all())

    rows: List[Dict[str, Any]] = []
    for ins in insights:
        rows.append({
            "id": ins.insight_code,
            "agent": ins.agent,
            "invoice_id": ins.invoice_id,
            "supplier_id": ins.supplier_id,
            "type": ins.insight_type,
            "confidence": ins.confidence,
            "recommendation": ins.recommendation,
            "reasoning": ins.reasoning,
            "applied": ins.applied,
            "applied_at": ins.applied_at,
            "status": ins.status,
        })

    return rows


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------

async def apply_insight(db: AsyncSession, insight_code: str) -> Dict[str, Any]:
    """Mark an AI insight as applied.

    Business rules:
    - Looks up the insight by ``insight_code`` (e.g. "AI001").
    - Sets ``applied`` to True, ``applied_at`` to the current UTC time,
      and ``status`` to "APPLIED".
    - Publishes an ``ai.insight_applied`` domain event on the event bus.

    Returns a dict suitable for serialisation as ``AIInsightApplyResponse``.

    Raises:
        NotFoundError: if no insight matches the given insight_code.
    """
    result = await db.execute(
        select(AIInsight).where(AIInsight.insight_code == insight_code)
    )
    insight = result.scalar_one_or_none()

    if insight is None:
        raise NotFoundError(f"AI insight {insight_code} not found")

    now = datetime.now(timezone.utc)
    insight.applied = True
    insight.applied_at = now
    insight.status = "APPLIED"

    await db.flush()
    await db.refresh(insight)

    # Publish domain event
    await event_bus.publish(Event(
        name="ai.insight_applied",
        data={
            "insight_code": insight.insight_code,
            "agent": insight.agent,
            "insight_type": insight.insight_type,
            "invoice_id": insight.invoice_id,
            "supplier_id": insight.supplier_id,
        },
        source="ai_agents",
    ))

    return {
        "id": insight.insight_code,
        "status": insight.status,
        "applied": insight.applied,
        "applied_at": insight.applied_at,
    }
