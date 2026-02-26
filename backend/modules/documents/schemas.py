"""
Document Management Module — Pydantic Schemas
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_type: str
    entity_id: str
    document_type: str
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    storage_type: str
    storage_path: Optional[str] = None
    checksum: Optional[str] = None
    version: int
    uploaded_by: Optional[str] = None
    description: Optional[str] = None
    is_active: str
    created_at: Optional[str] = None


class DocumentCreateRequest(BaseModel):
    entity_type: str
    entity_id: str
    document_type: str
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    storage_path: Optional[str] = None
    description: Optional[str] = None


class DocumentSummaryResponse(BaseModel):
    total_documents: int
    by_entity_type: dict
    by_document_type: dict
    total_size_bytes: int
