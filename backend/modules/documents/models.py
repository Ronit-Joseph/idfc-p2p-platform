"""
Document Management Module — SQLAlchemy Models
Table: documents

Stores document metadata (invoice PDFs, PO attachments, GRN photos, contracts).
Actual files stored on filesystem or object storage — this table tracks metadata.
"""

import uuid

from sqlalchemy import Column, String, Integer, Text, DateTime, func

from backend.base_model import Base, TimestampMixin


class Document(TimestampMixin, Base):
    """Document metadata record.

    entity_type: INVOICE, PO, PR, GRN, SUPPLIER, CONTRACT
    document_type: INVOICE_PDF, PO_COPY, GRN_PHOTO, CONTRACT_SIGNED,
                   SUPPORTING_DOC, APPROVAL_NOTE, TAX_CERTIFICATE, OTHER
    storage_type: LOCAL, S3, AZURE_BLOB
    """

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    entity_type = Column(String(20), nullable=False, index=True)  # INVOICE, PO, PR, GRN, SUPPLIER, CONTRACT
    entity_id = Column(String(100), nullable=False, index=True)  # human-readable code (INV001, PO2024-001)
    document_type = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)  # bytes
    mime_type = Column(String(100), nullable=True)
    storage_type = Column(String(20), nullable=False, default="LOCAL")
    storage_path = Column(String(500), nullable=True)  # file path or S3 key
    checksum = Column(String(64), nullable=True)  # SHA-256 for integrity
    version = Column(Integer, nullable=False, default=1)
    uploaded_by = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(String(3), nullable=False, default="YES")  # YES/NO (soft delete)
