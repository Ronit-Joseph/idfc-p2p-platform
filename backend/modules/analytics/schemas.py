"""
Analytics Module — Pydantic Schemas

Defines response models for the Spend Analytics API.

The analytics module has no dedicated database table — it aggregates data
from other modules' tables (invoices, suppliers, purchase_orders) and
combines real-time query results with hardcoded prototype trend data.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Nested models for spend analytics response
# ---------------------------------------------------------------------------

class SpendSummary(BaseModel):
    """Top-level KPI summary for month-to-date spend analytics."""

    model_config = ConfigDict(from_attributes=True)

    total_spend_mtd: float
    total_invoices: int
    avg_cycle_days: float
    auto_approval_rate: float
    three_way_match_rate: float
    early_payment_savings: float


class SpendByCategory(BaseModel):
    """Spend breakdown by procurement category."""

    model_config = ConfigDict(from_attributes=True)

    category: str
    amount: float
    pct: float


class MonthlyTrend(BaseModel):
    """Monthly spend trend data point."""

    model_config = ConfigDict(from_attributes=True)

    month: str
    amount: float


class TopSupplier(BaseModel):
    """Top supplier by spend volume."""

    model_config = ConfigDict(from_attributes=True)

    supplier: str
    amount: float
    invoices: int


# ---------------------------------------------------------------------------
# Top-level analytics response
# ---------------------------------------------------------------------------

class SpendAnalyticsResponse(BaseModel):
    """Complete spend analytics payload returned by ``GET /api/analytics/spend``.

    Combines real-time summary KPIs (queried from the Invoice table) with
    hardcoded prototype data for category breakdown, monthly trends, and
    top suppliers.
    """

    model_config = ConfigDict(from_attributes=True)

    summary: SpendSummary
    spend_by_category: List[SpendByCategory]
    monthly_trend: List[MonthlyTrend]
    top_suppliers: List[TopSupplier]
