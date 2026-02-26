"""
AI Agents Module — SQLAlchemy Models
Tables: ai_insights, agent_configs

AI agents: InvoiceCodingAgent, FraudDetectionAgent, SLAPredictionAgent,
           CashOptimizationAgent, RiskAgent.

Derived from the 7-record AI_INSIGHTS and the agents config in the prototype.
"""

import uuid

from sqlalchemy import Column, String, Boolean, Float, Text, DateTime, JSON, func

from backend.base_model import Base, TimestampMixin


class AIInsight(TimestampMixin, Base):
    """AI agent insight / recommendation / alert.

    Each insight is linked to either an invoice or a supplier (or both).
    insight_type: GL_CODING, FRAUD_ALERT, MSME_SLA_RISK, MSME_SLA_BREACH,
                  EARLY_PAYMENT, SUPPLIER_RISK, etc.
    status: PENDING_ACTION, RECOMMENDED, APPLIED, ESCALATED.
    """

    __tablename__ = "ai_insights"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    insight_code = Column(String(20), nullable=True, index=True)  # e.g. "AI001"
    agent = Column(String(50), nullable=False)  # Agent name
    invoice_id = Column(String(36), nullable=True, index=True)  # FK conceptual to invoices
    supplier_id = Column(String(36), nullable=True, index=True)  # FK conceptual to suppliers
    insight_type = Column(String(30), nullable=False)
    confidence = Column(Float, nullable=True)
    recommendation = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    applied = Column(Boolean, nullable=False, default=False)
    applied_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="PENDING_ACTION")


class AgentConfig(TimestampMixin, Base):
    """Configuration and metadata for each AI agent.

    Tracks the model version, status, average confidence, and
    runtime configuration as a JSON blob.
    """

    __tablename__ = "agent_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    name = Column(String(50), unique=True, nullable=False)  # e.g. "InvoiceCodingAgent"
    display_name = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)  # e.g. "fine-tuned-bert-v2.1"
    status = Column(String(20), nullable=False, default="ACTIVE")
    avg_confidence = Column(Float, nullable=True)
    config_json = Column(JSON, nullable=True)  # Flexible configuration
