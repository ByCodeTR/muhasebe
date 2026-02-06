"""
Vendor schemas.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class VendorAliasBase(BaseModel):
    """Base vendor alias schema."""
    alias: str


class VendorAliasCreate(VendorAliasBase):
    """Schema for creating a vendor alias."""
    pass


class VendorAliasResponse(VendorAliasBase):
    """Schema for vendor alias response."""
    id: UUID
    created_at: datetime
    
    model_config = {"from_attributes": True}


class VendorBase(BaseModel):
    """Base vendor schema."""
    display_name: str
    vkn: str | None = Field(None, min_length=10, max_length=11)
    tckn: str | None = Field(None, min_length=11, max_length=11)
    address: str | None = None
    phone: str | None = None
    notes: str | None = None


class VendorCreate(VendorBase):
    """Schema for creating a vendor."""
    aliases: list[str] = []


class VendorUpdate(BaseModel):
    """Schema for updating a vendor."""
    display_name: str | None = None
    vkn: str | None = None
    tckn: str | None = None
    address: str | None = None
    phone: str | None = None
    notes: str | None = None


class VendorResponse(VendorBase):
    """Schema for vendor response."""
    id: UUID
    normalized_name: str
    aliases: list[VendorAliasResponse] = []
    created_at: datetime
    
    model_config = {"from_attributes": True}


class VendorSummary(BaseModel):
    """Minimal vendor info for dropdowns."""
    id: UUID
    display_name: str
    vkn: str | None = None
    
    model_config = {"from_attributes": True}
