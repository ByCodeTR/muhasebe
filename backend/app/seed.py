"""
Seed data script for initial data population.
"""
import asyncio
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import User, Category, Vendor


# Default user for single-user mode
DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# Default categories
DEFAULT_CATEGORIES = [
    {"name": "Market", "icon": "🛒", "color": "#22c55e"},
    {"name": "Restoran", "icon": "🍽️", "color": "#f59e0b"},
    {"name": "Ulaşım", "icon": "🚗", "color": "#3b82f6"},
    {"name": "Faturalar", "icon": "📄", "color": "#ef4444"},
    {"name": "Sağlık", "icon": "🏥", "color": "#ec4899"},
    {"name": "Eğlence", "icon": "🎬", "color": "#8b5cf6"},
    {"name": "Giyim", "icon": "👕", "color": "#06b6d4"},
    {"name": "Elektronik", "icon": "📱", "color": "#64748b"},
    {"name": "Ev", "icon": "🏠", "color": "#84cc16"},
    {"name": "Diğer", "icon": "📦", "color": "#9ca3af"},
]


# Common Turkish vendors for demo
DEMO_VENDORS = [
    {"display_name": "Migros", "vkn": "1234567890"},
    {"display_name": "BİM", "vkn": "0987654321"},
    {"display_name": "A101", "vkn": "1122334455"},
    {"display_name": "ŞOK", "vkn": "5544332211"},
    {"display_name": "CarrefourSA", "vkn": "6677889900"},
]


async def seed_database():
    """Populate database with initial seed data."""
    async with async_session_maker() as session:
        # Check if default user exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.id == DEFAULT_USER_ID)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Create default user
            user = User(
                id=DEFAULT_USER_ID,
                name="Demo Kullanıcı",
                email="demo@muhasebe.local",
                is_active=True,
            )
            session.add(user)
            print("✓ Created default user")
        
        # Create categories if not exist
        result = await session.execute(
            select(Category).where(Category.user_id == DEFAULT_USER_ID)
        )
        existing_categories = result.scalars().all()
        
        if not existing_categories:
            for cat_data in DEFAULT_CATEGORIES:
                category = Category(
                    user_id=DEFAULT_USER_ID,
                    name=cat_data["name"],
                    icon=cat_data["icon"],
                    color=cat_data["color"],
                )
                session.add(category)
            print(f"✓ Created {len(DEFAULT_CATEGORIES)} categories")
        
        # Create demo vendors if not exist
        result = await session.execute(
            select(Vendor).where(Vendor.user_id == DEFAULT_USER_ID)
        )
        existing_vendors = result.scalars().all()
        
        if not existing_vendors:
            for vendor_data in DEMO_VENDORS:
                vendor = Vendor(
                    user_id=DEFAULT_USER_ID,
                    display_name=vendor_data["display_name"],
                    normalized_name=vendor_data["display_name"].lower(),
                    vkn=vendor_data.get("vkn"),
                )
                session.add(vendor)
            print(f"✓ Created {len(DEMO_VENDORS)} demo vendors")
        
        await session.commit()
        print("✓ Seed data completed")


if __name__ == "__main__":
    asyncio.run(seed_database())
