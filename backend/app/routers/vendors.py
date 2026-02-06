"""
Vendor (Cari) endpoints.
"""
import re
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.vendor import Vendor, VendorAlias
from app.schemas.vendor import (
    VendorCreate,
    VendorUpdate,
    VendorResponse,
    VendorSummary,
)

router = APIRouter(prefix="/vendors", tags=["Vendors"])


def normalize_name(name: str) -> str:
    """Normalize vendor name for matching."""
    # Lowercase
    name = name.lower()
    # Remove common suffixes
    name = re.sub(r'\b(ltd|a\.?s\.?|tic\.?|san\.?|ltd\.?\s*şti\.?)\b', '', name)
    # Remove punctuation
    name = re.sub(r'[^\w\s]', '', name)
    # Remove extra whitespace
    name = ' '.join(name.split())
    return name.strip()


@router.get("/", response_model=list[VendorResponse])
async def list_vendors(
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List all vendors with optional search."""
    query = select(Vendor).order_by(Vendor.display_name)
    
    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(Vendor.display_name).like(search_term),
                func.lower(Vendor.normalized_name).like(search_term),
                Vendor.vkn.like(search_term),
            )
        )
    
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/search", response_model=list[VendorSummary])
async def search_vendors(
    q: Annotated[str, Query(min_length=2)],
    db: AsyncSession = Depends(get_db),
):
    """Quick search for vendor autocomplete."""
    search_term = f"%{q.lower()}%"
    query = (
        select(Vendor)
        .where(
            or_(
                func.lower(Vendor.display_name).like(search_term),
                func.lower(Vendor.normalized_name).like(search_term),
            )
        )
        .limit(10)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific vendor by ID."""
    result = await db.execute(
        select(Vendor).where(Vendor.id == vendor_id)
    )
    vendor = result.scalar_one_or_none()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )
    
    return vendor


@router.post("/", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    data: VendorCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new vendor."""
    # Check for duplicate VKN
    if data.vkn:
        existing = await db.execute(
            select(Vendor).where(Vendor.vkn == data.vkn)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vendor with this VKN already exists",
            )
    
    vendor = Vendor(
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),  # TODO: get from auth
        display_name=data.display_name,
        normalized_name=normalize_name(data.display_name),
        vkn=data.vkn,
        tckn=data.tckn,
        address=data.address,
        phone=data.phone,
        notes=data.notes,
    )
    db.add(vendor)
    
    # Add aliases
    for alias_name in data.aliases:
        alias = VendorAlias(
            vendor_id=vendor.id,
            alias=alias_name,
            normalized_alias=normalize_name(alias_name),
        )
        db.add(alias)
    
    await db.commit()
    await db.refresh(vendor)
    
    return vendor


@router.patch("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: uuid.UUID,
    data: VendorUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a vendor."""
    result = await db.execute(
        select(Vendor).where(Vendor.id == vendor_id)
    )
    vendor = result.scalar_one_or_none()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )
    
    update_data = data.model_dump(exclude_unset=True)
    
    if "display_name" in update_data:
        update_data["normalized_name"] = normalize_name(update_data["display_name"])
    
    for field, value in update_data.items():
        setattr(vendor, field, value)
    
    await db.commit()
    await db.refresh(vendor)
    
    return vendor


@router.post("/{vendor_id}/aliases", response_model=VendorResponse)
async def add_vendor_alias(
    vendor_id: uuid.UUID,
    alias_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Add an alias to a vendor."""
    result = await db.execute(
        select(Vendor).where(Vendor.id == vendor_id)
    )
    vendor = result.scalar_one_or_none()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )
    
    alias = VendorAlias(
        vendor_id=vendor.id,
        alias=alias_name,
        normalized_alias=normalize_name(alias_name),
    )
    db.add(alias)
    await db.commit()
    await db.refresh(vendor)
    
    return vendor
