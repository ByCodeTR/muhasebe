"""
Ledger entry endpoints.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ledger import LedgerEntry, Category
from app.schemas.ledger import (
    LedgerEntryCreate,
    LedgerEntryUpdate,
    LedgerEntryResponse,
    CategoryCreate,
    CategoryResponse,
)

router = APIRouter(prefix="/ledger", tags=["Ledger"])


# ============ Ledger Entries ============

@router.get("/entries", response_model=list[LedgerEntryResponse])
async def list_entries(
    direction: str | None = None,
    vendor_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List ledger entries with optional filtering."""
    query = select(LedgerEntry).order_by(LedgerEntry.entry_date.desc())
    
    if direction:
        query = query.where(LedgerEntry.direction == direction)
    if vendor_id:
        query = query.where(LedgerEntry.vendor_id == vendor_id)
    if category_id:
        query = query.where(LedgerEntry.category_id == category_id)
    
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    
    return result.scalars().all()


@router.get("/entries/{entry_id}", response_model=LedgerEntryResponse)
async def get_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific ledger entry."""
    result = await db.execute(
        select(LedgerEntry).where(LedgerEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ledger entry not found",
        )
    
    return entry


@router.post("/entries", response_model=LedgerEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_entry(
    data: LedgerEntryCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a manual ledger entry."""
    entry = LedgerEntry(
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),  # TODO: get from auth
        vendor_id=data.vendor_id,
        document_id=data.document_id,
        category_id=data.category_id,
        direction=data.direction.value,
        amount=data.amount,
        tax_amount=data.tax_amount,
        currency=data.currency,
        notes=data.notes,
        entry_date=data.entry_date or datetime.utcnow(),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    
    return entry


@router.patch("/entries/{entry_id}", response_model=LedgerEntryResponse)
async def update_entry(
    entry_id: uuid.UUID,
    data: LedgerEntryUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a ledger entry."""
    result = await db.execute(
        select(LedgerEntry).where(LedgerEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ledger entry not found",
        )
    
    update_data = data.model_dump(exclude_unset=True)
    if "direction" in update_data and update_data["direction"]:
        update_data["direction"] = update_data["direction"].value
    
    for field, value in update_data.items():
        setattr(entry, field, value)
    
    await db.commit()
    await db.refresh(entry)
    
    return entry


@router.delete("/entries/{entry_id}")
async def delete_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a ledger entry."""
    result = await db.execute(
        select(LedgerEntry).where(LedgerEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ledger entry not found",
        )
    
    await db.delete(entry)
    await db.commit()
    
    return {"message": "Entry deleted"}


# ============ Categories ============

@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """List all categories."""
    result = await db.execute(
        select(Category).order_by(Category.name)
    )
    return result.scalars().all()


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new category."""
    category = Category(
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),  # TODO: get from auth
        name=data.name,
        icon=data.icon,
        color=data.color,
        parent_id=data.parent_id,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    
    return category


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
):
    """Update a category."""
    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    category.name = data.name
    category.icon = data.icon
    category.color = data.color
    category.parent_id = data.parent_id
    
    await db.commit()
    await db.refresh(category)
    
    return category
