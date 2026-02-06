"""
Vendor (Cari) model with alias support.
"""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Vendor(Base):
    """Vendor/Cari model for storing merchant information."""
    
    __tablename__ = "vendors"
    
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
    display_name: Mapped[str] = mapped_column(String(255))
    normalized_name: Mapped[str] = mapped_column(String(255), index=True)
    vkn: Mapped[str | None] = mapped_column(
        String(11),
        nullable=True,
        index=True,
        comment="Vergi Kimlik Numarası (10-11 digits)",
    )
    tckn: Mapped[str | None] = mapped_column(
        String(11),
        nullable=True,
        index=True,
        comment="TC Kimlik Numarası (11 digits)",
    )
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    
    # Relationships
    user = relationship("User", back_populates="vendors")
    aliases = relationship(
        "VendorAlias",
        back_populates="vendor",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    documents = relationship("Document", back_populates="vendor", lazy="dynamic")
    ledger_entries = relationship("LedgerEntry", back_populates="vendor", lazy="dynamic")
    
    def __repr__(self) -> str:
        return f"<Vendor {self.display_name}>"


class VendorAlias(Base):
    """Alternative names/variations for a vendor."""
    
    __tablename__ = "vendor_aliases"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="CASCADE"),
        index=True,
    )
    alias: Mapped[str] = mapped_column(String(255), index=True)
    normalized_alias: Mapped[str] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    
    # Relationships
    vendor = relationship("Vendor", back_populates="aliases")
    
    def __repr__(self) -> str:
        return f"<VendorAlias {self.alias}>"
