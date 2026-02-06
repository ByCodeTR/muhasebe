"""
Vendor matching service for identifying vendors from OCR data.
Uses multiple matching strategies with configurable thresholds.
"""
import re
import logging
from typing import Optional
from dataclasses import dataclass
from difflib import SequenceMatcher
from uuid import UUID

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vendor import Vendor, VendorAlias

logger = logging.getLogger(__name__)


@dataclass
class VendorMatch:
    """Result of vendor matching."""
    vendor_id: Optional[UUID] = None
    vendor_name: Optional[str] = None
    match_type: Optional[str] = None  # 'vkn', 'exact', 'alias', 'fuzzy'
    confidence: float = 0.0
    is_new: bool = True


class VendorMatcher:
    """
    Service for matching OCR-extracted vendor info to existing vendors.
    
    Matching priority:
    1. VKN/TCKN exact match (highest confidence)
    2. Exact normalized name match
    3. Alias match
    4. Fuzzy name match (above threshold)
    5. No match - suggest creating new vendor
    """

    # Minimum similarity score for fuzzy matching
    FUZZY_THRESHOLD = 0.7
    
    # Common suffixes to remove when normalizing
    SUFFIXES_TO_REMOVE = [
        r'\s*ltd\.?\s*şti\.?',
        r'\s*a\.?s\.?',
        r'\s*tic\.?\s*(?:ltd\.?\s*şti\.?)?',
        r'\s*san\.?\s*(?:tic\.?)?',
        r'\s*org\.?',
        r'\s*holding',
        r'\s*group',
        r'\s*şirket(?:i)?',
        r'\s*market(?:i)?',
    ]

    def normalize_name(self, name: str) -> str:
        """
        Normalize vendor name for matching.
        
        Steps:
        1. Lowercase
        2. Remove common business suffixes
        3. Remove punctuation
        4. Collapse whitespace
        """
        if not name:
            return ""
        
        # Lowercase
        normalized = name.lower()
        
        # Remove common suffixes
        for suffix in self.SUFFIXES_TO_REMOVE:
            normalized = re.sub(suffix, '', normalized, flags=re.IGNORECASE)
        
        # Remove punctuation except spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Collapse whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()

    def calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity ratio between two strings."""
        if not s1 or not s2:
            return 0.0
        return SequenceMatcher(None, s1, s2).ratio()

    async def find_match(
        self,
        db: AsyncSession,
        user_id: UUID,
        vendor_name: Optional[str] = None,
        vkn: Optional[str] = None,
        tckn: Optional[str] = None,
    ) -> VendorMatch:
        """
        Find the best matching vendor for given criteria.
        
        Args:
            db: Database session
            user_id: User ID to scope the search
            vendor_name: Vendor name from OCR
            vkn: VKN from OCR
            tckn: TCKN from OCR
            
        Returns:
            VendorMatch with result
        """
        # 1. Try VKN match first (highest confidence)
        if vkn:
            result = await db.execute(
                select(Vendor).where(
                    Vendor.user_id == user_id,
                    Vendor.vkn == vkn
                )
            )
            vendor = result.scalar_one_or_none()
            if vendor:
                return VendorMatch(
                    vendor_id=vendor.id,
                    vendor_name=vendor.display_name,
                    match_type='vkn',
                    confidence=1.0,
                    is_new=False,
                )
        
        # 2. Try TCKN match
        if tckn:
            result = await db.execute(
                select(Vendor).where(
                    Vendor.user_id == user_id,
                    Vendor.tckn == tckn
                )
            )
            vendor = result.scalar_one_or_none()
            if vendor:
                return VendorMatch(
                    vendor_id=vendor.id,
                    vendor_name=vendor.display_name,
                    match_type='tckn',
                    confidence=1.0,
                    is_new=False,
                )
        
        # If no name provided, no more matching possible
        if not vendor_name:
            return VendorMatch()
        
        normalized = self.normalize_name(vendor_name)
        
        # 3. Try exact normalized name match
        result = await db.execute(
            select(Vendor).where(
                Vendor.user_id == user_id,
                Vendor.normalized_name == normalized
            )
        )
        vendor = result.scalar_one_or_none()
        if vendor:
            return VendorMatch(
                vendor_id=vendor.id,
                vendor_name=vendor.display_name,
                match_type='exact',
                confidence=0.95,
                is_new=False,
            )
        
        # 4. Try alias match
        result = await db.execute(
            select(Vendor)
            .join(VendorAlias, Vendor.id == VendorAlias.vendor_id)
            .where(
                Vendor.user_id == user_id,
                VendorAlias.normalized_alias == normalized
            )
        )
        vendor = result.scalar_one_or_none()
        if vendor:
            return VendorMatch(
                vendor_id=vendor.id,
                vendor_name=vendor.display_name,
                match_type='alias',
                confidence=0.9,
                is_new=False,
            )
        
        # 5. Try fuzzy matching
        result = await db.execute(
            select(Vendor).where(Vendor.user_id == user_id)
        )
        all_vendors = result.scalars().all()
        
        best_match = None
        best_score = 0.0
        
        for vendor in all_vendors:
            # Check against display name
            score = self.calculate_similarity(normalized, vendor.normalized_name)
            if score > best_score:
                best_score = score
                best_match = vendor
            
            # Check against aliases
            for alias in vendor.aliases:
                alias_score = self.calculate_similarity(normalized, alias.normalized_alias)
                if alias_score > best_score:
                    best_score = alias_score
                    best_match = vendor
        
        if best_match and best_score >= self.FUZZY_THRESHOLD:
            return VendorMatch(
                vendor_id=best_match.id,
                vendor_name=best_match.display_name,
                match_type='fuzzy',
                confidence=round(best_score, 2),
                is_new=False,
            )
        
        # 6. No match found - suggest creating new
        return VendorMatch(
            vendor_name=vendor_name,
            is_new=True,
        )

    async def create_or_get_vendor(
        self,
        db: AsyncSession,
        user_id: UUID,
        display_name: str,
        vkn: Optional[str] = None,
        tckn: Optional[str] = None,
        add_alias_from: Optional[str] = None,
    ) -> Vendor:
        """
        Get existing vendor or create a new one.
        Optionally learn a new alias from the OCR name.
        
        Args:
            db: Database session
            user_id: User ID
            display_name: Vendor display name
            vkn: VKN
            tckn: TCKN
            add_alias_from: If provided, add this as an alias to existing vendor
            
        Returns:
            Vendor instance
        """
        # First try to find existing
        match = await self.find_match(db, user_id, display_name, vkn, tckn)
        
        if not match.is_new and match.vendor_id:
            result = await db.execute(
                select(Vendor).where(Vendor.id == match.vendor_id)
            )
            vendor = result.scalar_one()
            
            # Learn new alias if provided and different from existing
            if add_alias_from:
                normalized_alias = self.normalize_name(add_alias_from)
                # Check if alias already exists
                existing_aliases = [a.normalized_alias for a in vendor.aliases]
                if normalized_alias not in existing_aliases and normalized_alias != vendor.normalized_name:
                    new_alias = VendorAlias(
                        vendor_id=vendor.id,
                        alias=add_alias_from,
                        normalized_alias=normalized_alias,
                    )
                    db.add(new_alias)
                    logger.info(f"Learned new alias '{add_alias_from}' for vendor '{vendor.display_name}'")
            
            return vendor
        
        # Create new vendor
        vendor = Vendor(
            user_id=user_id,
            display_name=display_name,
            normalized_name=self.normalize_name(display_name),
            vkn=vkn,
            tckn=tckn,
        )
        db.add(vendor)
        await db.flush()  # Get the ID
        
        logger.info(f"Created new vendor: {display_name}")
        return vendor


# Singleton instance
_vendor_matcher: Optional[VendorMatcher] = None


def get_vendor_matcher() -> VendorMatcher:
    """Get or create vendor matcher instance."""
    global _vendor_matcher
    if _vendor_matcher is None:
        _vendor_matcher = VendorMatcher()
    return _vendor_matcher
