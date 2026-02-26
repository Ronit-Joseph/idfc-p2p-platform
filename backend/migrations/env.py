"""Alembic migration environment.

Supports both sync (for autogenerate) and async (for runtime) execution.
"""

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import settings
from backend.base_model import Base

# Import ALL models so that Base.metadata is fully populated
from backend.modules.auth.models import User  # noqa: F401
from backend.modules.suppliers.models import Supplier  # noqa: F401
from backend.modules.budgets.models import Budget, BudgetEncumbrance  # noqa: F401
from backend.modules.purchase_requests.models import PurchaseRequest, PRLineItem  # noqa: F401
from backend.modules.purchase_orders.models import (  # noqa: F401
    PurchaseOrder, POLineItem, GoodsReceiptNote, GRNLineItem,
)
from backend.modules.invoices.models import Invoice  # noqa: F401
from backend.modules.matching.models import *  # noqa: F401, F403
from backend.modules.gst_cache.models import GSTRecord, GSTSyncLog  # noqa: F401
from backend.modules.ebs_integration.models import EBSEvent  # noqa: F401
from backend.modules.ai_agents.models import AIInsight, AgentConfig  # noqa: F401
from backend.modules.workflow.models import *  # noqa: F401, F403
from backend.modules.notifications.models import *  # noqa: F401, F403
from backend.modules.audit.models import *  # noqa: F401, F403
from backend.modules.analytics.models import *  # noqa: F401, F403
from backend.modules.vendor_portal.models import VendorPortalEvent  # noqa: F401

# Alembic Config object
config = context.config

# Override sqlalchemy.url with our runtime setting
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — emit SQL to stdout."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Configure the migration context with an existing connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode — connect to the database."""
    connectable_url = config.get_main_option("sqlalchemy.url", "")
    if "sqlite" in connectable_url or "aiosqlite" in connectable_url:
        # For SQLite / aiosqlite, use async path
        asyncio.run(run_async_migrations())
    else:
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
