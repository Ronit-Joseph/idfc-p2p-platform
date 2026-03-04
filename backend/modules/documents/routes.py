"""
Document Management Module — FastAPI Routes

Prefix: ``/api/documents``

Document metadata management for invoices, POs, GRNs, contracts, etc.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user, require_role, paginate
from backend.modules.documents.schemas import (
    DocumentResponse,
    DocumentCreateRequest,
    DocumentSummaryResponse,
)
from backend.modules.documents import service

router = APIRouter(prefix="/api/documents", tags=["documents"])


# ---------------------------------------------------------------------------
# GET  /api/documents
# ---------------------------------------------------------------------------

@router.get("")
async def list_documents(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    document_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """List documents with optional filters."""
    items = await service.list_documents(
        db, entity_type=entity_type, entity_id=entity_id, document_type=document_type,
    )
    results = [DocumentResponse.model_validate(i) for i in items]
    return paginate(results, skip, limit)


# ---------------------------------------------------------------------------
# GET  /api/documents/summary
# ---------------------------------------------------------------------------

@router.get("/summary", response_model=DocumentSummaryResponse)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> DocumentSummaryResponse:
    """Document summary statistics."""
    summary = await service.get_document_summary(db)
    return DocumentSummaryResponse(**summary)


# ---------------------------------------------------------------------------
# GET  /api/documents/entity/{entity_type}/{entity_id}
# ---------------------------------------------------------------------------

@router.get("/entity/{entity_type}/{entity_id}")
async def entity_documents(
    entity_type: str,
    entity_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get all documents for a specific entity."""
    items = await service.get_entity_documents(db, entity_type, entity_id)
    results = [DocumentResponse.model_validate(i) for i in items]
    return paginate(results, skip, limit)


# ---------------------------------------------------------------------------
# POST  /api/documents
# ---------------------------------------------------------------------------

@router.post("", response_model=DocumentResponse, status_code=201)
async def create_document(
    body: DocumentCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(require_role("DEPARTMENT_HEAD")),
) -> DocumentResponse:
    """Register a new document (metadata). File upload handled separately."""
    result = await service.create_document(
        db,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        document_type=body.document_type,
        file_name=body.file_name,
        uploaded_by=user.get("name", "Unknown"),
        file_size=body.file_size,
        mime_type=body.mime_type,
        storage_path=body.storage_path,
        description=body.description,
    )
    return DocumentResponse.model_validate(result)


# ---------------------------------------------------------------------------
# DELETE  /api/documents/{doc_id}
# ---------------------------------------------------------------------------

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(require_role("PROCUREMENT_MANAGER")),
) -> Dict[str, Any]:
    """Soft-delete a document."""
    deleted = await service.delete_document(db, doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": True}
