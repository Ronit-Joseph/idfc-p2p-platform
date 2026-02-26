"""
Suppliers Module — Service Layer

Async CRUD operations against the ``suppliers`` table.  All database access
for the suppliers domain should go through these functions so that routes
(and future Kafka consumers) share one code-path.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.exceptions import ConflictError, NotFoundError
from backend.modules.suppliers.models import Supplier
from backend.modules.suppliers.schemas import SupplierCreate, SupplierUpdate


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

async def list_suppliers(db: AsyncSession) -> list[Supplier]:
    """Return every supplier, ordered by code ascending."""
    result = await db.execute(
        select(Supplier).order_by(Supplier.code)
    )
    return list(result.scalars().all())


async def get_supplier_by_code(db: AsyncSession, code: str) -> Supplier | None:
    """Look up a supplier by its human-readable ``code`` (e.g. "SUP001")."""
    result = await db.execute(
        select(Supplier).where(Supplier.code == code)
    )
    return result.scalar_one_or_none()


async def get_supplier_by_id(db: AsyncSession, id: str) -> Supplier | None:
    """Look up a supplier by its UUID primary key."""
    result = await db.execute(
        select(Supplier).where(Supplier.id == id)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------

async def _generate_next_code(db: AsyncSession) -> str:
    """Generate the next sequential supplier code (e.g. "SUP016").

    Finds the current maximum numeric suffix among existing codes that
    match the ``SUPnnn`` pattern and increments by one.
    """
    result = await db.execute(select(func.count()).select_from(Supplier))
    count = result.scalar() or 0
    # Start from count + 1 and keep incrementing until we find an unused code
    next_num = count + 1
    while True:
        candidate = f"SUP{next_num:03d}"
        existing = await db.execute(
            select(Supplier.code).where(Supplier.code == candidate)
        )
        if existing.scalar_one_or_none() is None:
            return candidate
        next_num += 1


async def create_supplier(db: AsyncSession, data: SupplierCreate) -> Supplier:
    """Insert a new supplier.

    * Auto-generates a ``code`` like "SUP016".
    * Raises ``ConflictError`` if the GSTIN already exists.
    """
    # Check GSTIN uniqueness
    existing = await db.execute(
        select(Supplier).where(Supplier.gstin == data.gstin)
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(f"Supplier with GSTIN {data.gstin} already exists")

    code = await _generate_next_code(db)

    supplier = Supplier(
        code=code,
        **data.model_dump(exclude_unset=False),
    )
    db.add(supplier)
    await db.flush()          # flush so the object gets its defaults (id, timestamps)
    await db.refresh(supplier)
    return supplier


async def update_supplier(
    db: AsyncSession,
    code: str,
    data: SupplierUpdate,
) -> Supplier:
    """Partially update an existing supplier identified by ``code``.

    Only fields that are explicitly set in the payload are written.
    Raises ``NotFoundError`` if the code does not exist, and
    ``ConflictError`` if a GSTIN change would collide with another record.
    """
    supplier = await get_supplier_by_code(db, code)
    if supplier is None:
        raise NotFoundError(f"Supplier {code} not found")

    update_data = data.model_dump(exclude_unset=True)

    # If GSTIN is changing, verify uniqueness
    if "gstin" in update_data and update_data["gstin"] != supplier.gstin:
        dup = await db.execute(
            select(Supplier).where(Supplier.gstin == update_data["gstin"])
        )
        if dup.scalar_one_or_none() is not None:
            raise ConflictError(
                f"Supplier with GSTIN {update_data['gstin']} already exists"
            )

    for field, value in update_data.items():
        setattr(supplier, field, value)

    await db.flush()
    await db.refresh(supplier)
    return supplier
