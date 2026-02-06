"""
Document schemas.
"""
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.document import DocumentStatus, DocumentType


class DocumentBase(BaseModel):
    """Base document schema."""
    doc_type: DocumentType = DocumentType.RECEIPT
    doc_date: date | None = None
    doc_no: str | None = None
    currency: str = "TRY"
    total_gross: Decimal | None = None
    total_tax: Decimal | None = None
    total_net: Decimal | None = None
    notes: str | None = None


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    vendor_id: UUID | None = None


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    vendor_id: UUID | None = None
    doc_type: DocumentType | None = None
    doc_date: date | None = None
    doc_no: str | None = None
    currency: str | None = None
    total_gross: Decimal | None = None
    total_tax: Decimal | None = None
    total_net: Decimal | None = None
    notes: str | None = None
    status: DocumentStatus | None = None


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    id: UUID
    user_id: UUID
    vendor_id: UUID | None = None
    status: DocumentStatus
    image_url: str | None = None
    confidence_score: float | None = None
    created_at: datetime
    updated_at: datetime
    
    # Nested vendor info
    vendor_name: str | None = None
    
    model_config = {"from_attributes": True}


class DocumentDraft(BaseModel):
    """Schema for OCR-extracted draft."""
    vendor_name: str | None = None
    vendor_confidence: float | None = None
    suggested_vendor_id: UUID | None = None
    doc_date: date | None = None
    total_gross: Decimal | None = None
    total_tax: Decimal | None = None
    currency: str = "TRY"
    raw_ocr_text: str | None = None
    confidence_score: float | None = None
    extraction_details: dict | None = None


class DocumentConfirm(BaseModel):
    """Schema for confirming a draft."""
    vendor_id: UUID | None = None
    create_vendor_name: str | None = None
    doc_date: date | None = None
    total_gross: Decimal | None = None
    total_tax: Decimal | None = None
    direction: str = "expense"
    category_id: UUID | None = None
