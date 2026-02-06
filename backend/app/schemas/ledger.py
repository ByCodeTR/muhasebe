"""
Ledger and category schemas.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models.ledger import EntryDirection


class CategoryBase(BaseModel):
    """Base category schema."""
    name: str
    icon: str | None = None
    color: str | None = None
    parent_id: UUID | None = None


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""
    pass


class CategoryResponse(CategoryBase):
    """Schema for category response."""
    id: UUID
    created_at: datetime
    
    model_config = {"from_attributes": True}


class LedgerEntryBase(BaseModel):
    """Base ledger entry schema."""
    direction: EntryDirection = EntryDirection.EXPENSE
    amount: Decimal
    tax_amount: Decimal | None = None
    currency: str = "TRY"
    notes: str | None = None
    entry_date: datetime | None = None


class LedgerEntryCreate(LedgerEntryBase):
    """Schema for creating a ledger entry."""
    vendor_id: UUID | None = None
    document_id: UUID | None = None
    category_id: UUID | None = None


class LedgerEntryUpdate(BaseModel):
    """Schema for updating a ledger entry."""
    direction: EntryDirection | None = None
    amount: Decimal | None = None
    tax_amount: Decimal | None = None
    vendor_id: UUID | None = None
    category_id: UUID | None = None
    notes: str | None = None


class LedgerEntryResponse(LedgerEntryBase):
    """Schema for ledger entry response."""
    id: UUID
    user_id: UUID
    vendor_id: UUID | None = None
    document_id: UUID | None = None
    category_id: UUID | None = None
    created_at: datetime
    
    # Nested info
    vendor_name: str | None = None
    category_name: str | None = None
    
    model_config = {"from_attributes": True}


class ReportSummary(BaseModel):
    """Summary report schema."""
    period_start: datetime
    period_end: datetime
    total_income: Decimal
    total_expense: Decimal
    net: Decimal
    tax_total: Decimal
    transaction_count: int
    by_category: list[dict] = []
    by_vendor: list[dict] = []
