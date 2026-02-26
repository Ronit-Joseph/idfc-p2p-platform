"""
Analytics Module — Service Layer

Async business-logic for spend analytics.  No dedicated table — this
service aggregates data from the ``invoices`` table for real-time summary
KPIs and falls back to hardcoded prototype data for category breakdowns,
monthly trends, and top-supplier rankings.

For production, these hardcoded sections should be replaced with actual
queries against materialised views or a dedicated analytics data warehouse
fed via Kafka CDC events.
"""

from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.invoices.models import Invoice


# ---------------------------------------------------------------------------
# Hardcoded prototype data
# ---------------------------------------------------------------------------

_SPEND_BY_CATEGORY = [
    {"category": "IT Services", "amount": 12500000, "pct": 42.3},
    {"category": "Facilities", "amount": 8500000, "pct": 28.8},
    {"category": "Consulting", "amount": 4200000, "pct": 14.2},
    {"category": "Office Supplies", "amount": 2500000, "pct": 8.5},
    {"category": "Printing & Marketing", "amount": 1062400, "pct": 3.6},
    {"category": "Others", "amount": 762400, "pct": 2.6},
]

_MONTHLY_TREND = [
    {"month": "Oct 2024", "amount": 14200000},
    {"month": "Nov 2024", "amount": 16800000},
    {"month": "Dec 2024", "amount": 12400000},
    {"month": "Jan 2025", "amount": 22100000},
    {"month": "Feb 2025", "amount": 19800000},
    {"month": "Mar 2025", "amount": 18762400},
]

_TOP_SUPPLIERS = [
    {"supplier": "TechMahindra Solutions", "amount": 5310000, "invoices": 1},
    {"supplier": "Deloitte Advisory LLP", "amount": 4200000, "invoices": 1},
    {"supplier": "Sodexo Facilities India", "amount": 3540000, "invoices": 1},
    {"supplier": "Karnataka Tech MSME Solutions", "amount": 2360000, "invoices": 1},
    {"supplier": "Gujarat Tech Solutions", "amount": 1770000, "invoices": 1},
]


# ---------------------------------------------------------------------------
# Main analytics query
# ---------------------------------------------------------------------------

async def get_spend_analytics(db: AsyncSession) -> Dict[str, Any]:
    """Build the spend analytics payload.

    Summary KPIs are computed from the ``invoices`` table in real time:
    - ``total_spend_mtd`` — sum of ``net_payable`` for APPROVED / POSTED_TO_EBS / PAID invoices.
    - ``total_invoices`` — total count of invoices.
    - ``avg_cycle_days`` — average processing cycle (hardcoded for prototype).
    - ``auto_approval_rate`` — percentage of invoices with status beyond PENDING_APPROVAL.
    - ``three_way_match_rate`` — percentage of invoices with a 3-way match status.
    - ``early_payment_savings`` — hardcoded for prototype.

    Category breakdown, monthly trends, and top suppliers use hardcoded
    prototype data.
    """

    # ── Total spend MTD (approved / posted / paid) ─────────────────
    spend_result = await db.execute(
        select(func.coalesce(func.sum(Invoice.net_payable), 0)).where(
            Invoice.status.in_(["APPROVED", "POSTED_TO_EBS", "PAID"])
        )
    )
    total_spend_mtd: float = float(spend_result.scalar_one())

    # ── Total invoice count ────────────────────────────────────────
    count_result = await db.execute(select(func.count(Invoice.id)))
    total_invoices: int = int(count_result.scalar_one())

    # ── Auto-approval rate ─────────────────────────────────────────
    # Invoices that progressed past PENDING_APPROVAL without rejection
    auto_approved_statuses = ["APPROVED", "POSTED_TO_EBS", "PAID"]
    auto_result = await db.execute(
        select(func.count(Invoice.id)).where(
            Invoice.status.in_(auto_approved_statuses)
        )
    )
    auto_count: int = int(auto_result.scalar_one())
    auto_approval_rate = round(
        (auto_count / total_invoices * 100) if total_invoices > 0 else 0.0,
        1,
    )

    # ── Three-way match rate ───────────────────────────────────────
    match_result = await db.execute(
        select(func.count(Invoice.id)).where(
            Invoice.match_status.in_(["3WAY_MATCH_PASSED"])
        )
    )
    match_count: int = int(match_result.scalar_one())
    three_way_match_rate = round(
        (match_count / total_invoices * 100) if total_invoices > 0 else 0.0,
        1,
    )

    # ── Assemble response ──────────────────────────────────────────
    return {
        "summary": {
            "total_spend_mtd": total_spend_mtd,
            "total_invoices": total_invoices,
            "avg_cycle_days": 5.2,  # hardcoded for prototype
            "auto_approval_rate": auto_approval_rate,
            "three_way_match_rate": three_way_match_rate,
            "early_payment_savings": 45000,  # hardcoded for prototype
        },
        "spend_by_category": _SPEND_BY_CATEGORY,
        "monthly_trend": _MONTHLY_TREND,
        "top_suppliers": _TOP_SUPPLIERS,
    }
