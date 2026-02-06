"""
Document model for receipts and invoices.
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from sqlalchemy import String, DateTime, Date, ForeignKey, Text, Numeric, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DocumentStatus(str, Enum):
    """Document processing status."""
    DRAFT = "draft"
    POSTED = "posted"
    CANCELLED = "cancelled"


class DocumentType(str, Enum):
    """Document type classification."""
    RECEIPT = "receipt"
    INVOICE = "invoice"
    OTHER = "other"


class Document(Base):
    """Receipt/Invoice document model."""
    
    __tablename__ = "documents"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=DocumentStatus.DRAFT.value,
        index=True,
    )
    doc_type: Mapped[str] = mapped_column(
        String(20),
        default=DocumentType.RECEIPT.value,
    )
    
    # Document details
    doc_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    doc_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="TRY")
    
    # Amounts
    total_gross: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    total_tax: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
        comment="KDV tutarı",
    )
    total_net: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    
    # OCR data
    raw_ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Image storage
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # Metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    
    # Relationships
    user = relationship("User", back_populates="documents")
    vendor = relationship("Vendor", back_populates="documents")
    ledger_entry = relationship(
        "LedgerEntry",
        back_populates="document",
        uselist=False,
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Document {self.id} - {self.status}>"
