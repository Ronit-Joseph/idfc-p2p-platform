"""
Budgets Module — SQLAlchemy Models
Tables: budgets, budget_encumbrances

Derived from the 6-record BUDGETS list in the prototype.
"""

import uuid

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, func

from backend.base_model import Base, TimestampMixin


class Budget(TimestampMixin, Base):
    """Department budget allocation for a fiscal year.

    Amounts stored in paise (integer) for precision in production.
    For the prototype/SQLite layer, Float is acceptable.
    """

    __tablename__ = "budgets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    department_code = Column(String(10), nullable=False, index=True)  # e.g. TECH, OPS, FIN
    department_name = Column(String(100), nullable=False)
    gl_account = Column(String(20), nullable=True)
    cost_center = Column(String(20), nullable=True)
    fiscal_year = Column(String(20), nullable=False)  # e.g. FY2024-25
    total_amount = Column(Float, nullable=False, default=0)
    committed_amount = Column(Float, nullable=False, default=0)
    actual_amount = Column(Float, nullable=False, default=0)
    available_amount = Column(Float, nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="INR")


class BudgetEncumbrance(Base):
    """Records budget encumbrance against a PR or PO.

    When a PR is approved, budget is encumbered.
    When PO is issued, encumbrance converts.
    When payment is made, encumbrance is consumed/released.
    """

    __tablename__ = "budget_encumbrances"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    budget_id = Column(String(36), ForeignKey("budgets.id"), nullable=False, index=True)
    reference_type = Column(String(10), nullable=False)  # PR / PO
    reference_id = Column(String(20), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="ENCUMBERED")  # ENCUMBERED / RELEASED / CONSUMED
    created_at = Column(DateTime, nullable=False, server_default=func.now())
