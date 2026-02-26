"""
Document Management Module — Service Layer

Document metadata CRUD. Actual file upload/download would integrate
with object storage (S3/Azure Blob) in production.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.documents.models import Document


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

async def create_document(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
    document_type: str,
    file_name: str,
    uploaded_by: Optional[str] = None,
    file_size: Optional[int] = None,
    mime_type: Optional[str] = None,
    storage_path: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Register a new document. In production, file upload happens separately."""
    # Calculate version (increment for same entity + document_type)
    ver_result = await db.execute(
        select(func.max(Document.version)).where(
            Document.entity_type == entity_type,
            Document.entity_id == entity_id,
            Document.document_type == document_type,
        )
    )
    current_version = ver_result.scalar() or 0

    doc = Document(
        entity_type=entity_type,
        entity_id=entity_id,
        document_type=document_type,
        file_name=file_name,
        file_size=file_size,
        mime_type=mime_type,
        storage_type="LOCAL",
        storage_path=storage_path or f"/documents/{entity_type}/{entity_id}/{file_name}",
        checksum=hashlib.sha256(f"{entity_id}:{file_name}:{current_version + 1}".encode()).hexdigest(),
        version=current_version + 1,
        uploaded_by=uploaded_by,
        description=description,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return _doc_to_dict(doc)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

async def list_documents(
    db: AsyncSession,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    document_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List documents with optional filters."""
    q = select(Document).where(Document.is_active == "YES")
    if entity_type:
        q = q.where(Document.entity_type == entity_type)
    if entity_id:
        q = q.where(Document.entity_id == entity_id)
    if document_type:
        q = q.where(Document.document_type == document_type)
    q = q.order_by(Document.created_at.desc())

    result = await db.execute(q)
    return [_doc_to_dict(d) for d in result.scalars().all()]


async def get_entity_documents(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
) -> List[Dict[str, Any]]:
    """Get all documents for a specific entity."""
    result = await db.execute(
        select(Document).where(
            Document.entity_type == entity_type,
            Document.entity_id == entity_id,
            Document.is_active == "YES",
        ).order_by(Document.document_type, Document.version.desc())
    )
    return [_doc_to_dict(d) for d in result.scalars().all()]


async def get_document_summary(db: AsyncSession) -> Dict[str, Any]:
    """Summary statistics for documents."""
    total_result = await db.execute(
        select(func.count(Document.id)).where(Document.is_active == "YES")
    )
    total = total_result.scalar() or 0

    by_entity = {}
    entity_result = await db.execute(
        select(Document.entity_type, func.count(Document.id))
        .where(Document.is_active == "YES")
        .group_by(Document.entity_type)
    )
    for row in entity_result.all():
        by_entity[row[0]] = row[1]

    by_doc_type = {}
    type_result = await db.execute(
        select(Document.document_type, func.count(Document.id))
        .where(Document.is_active == "YES")
        .group_by(Document.document_type)
    )
    for row in type_result.all():
        by_doc_type[row[0]] = row[1]

    size_result = await db.execute(
        select(func.sum(Document.file_size)).where(Document.is_active == "YES")
    )
    total_size = size_result.scalar() or 0

    return {
        "total_documents": total,
        "by_entity_type": by_entity,
        "by_document_type": by_doc_type,
        "total_size_bytes": total_size,
    }


# ---------------------------------------------------------------------------
# Soft delete
# ---------------------------------------------------------------------------

async def delete_document(db: AsyncSession, document_id: str) -> bool:
    """Soft-delete a document (set is_active = NO)."""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        return False
    doc.is_active = "NO"
    await db.commit()
    return True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doc_to_dict(d: Document) -> Dict[str, Any]:
    return {
        "id": d.id,
        "entity_type": d.entity_type,
        "entity_id": d.entity_id,
        "document_type": d.document_type,
        "file_name": d.file_name,
        "file_size": d.file_size,
        "mime_type": d.mime_type,
        "storage_type": d.storage_type,
        "storage_path": d.storage_path,
        "checksum": d.checksum,
        "version": d.version,
        "uploaded_by": d.uploaded_by,
        "description": d.description,
        "is_active": d.is_active,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }
