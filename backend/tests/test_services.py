"""
Tests for service layer - OCR, extraction, and vendor matching.
"""
import pytest
from datetime import date
from decimal import Decimal

from app.services.extraction_service import ExtractionService
from app.services.vendor_matcher import VendorMatcher


class TestExtractionService:
    """Tests for the extraction service."""

    def setup_method(self):
        """Setup extraction service for each test."""
        self.service = ExtractionService()

    def test_extract_empty_text(self):
        """Test extraction with empty text."""
        result = self.service.extract("")
        assert result.vendor_name is None
        assert result.total_gross is None

    def test_extract_date_dd_mm_yyyy(self):
        """Test extracting date in DD.MM.YYYY format."""
        text = "Tarih: 15.01.2026"
        result = self.service.extract(text)
        assert result.doc_date == date(2026, 1, 15)

    def test_extract_date_slash_format(self):
        """Test extracting date in DD/MM/YYYY format."""
        text = "Tarih: 20/03/2026"
        result = self.service.extract(text)
        assert result.doc_date == date(2026, 3, 20)

    def test_extract_amount_turkish_format(self):
        """Test extracting amount in Turkish format (1.234,56)."""
        text = "TOPLAM *1.234,56"
        result = self.service.extract(text)
        assert result.total_gross == Decimal("1234.56")

    def test_extract_amount_with_tl(self):
        """Test extracting amount with TL suffix."""
        text = "Tutar: 999,99 TL"
        result = self.service.extract(text)
        assert result.total_gross == Decimal("999.99")

    def test_extract_vkn(self):
        """Test extracting VKN."""
        text = "VKN: 1234567890"
        result = self.service.extract(text)
        assert result.vendor_vkn == "1234567890"

    def test_extract_vendor_name_from_header(self):
        """Test extracting vendor name from first lines."""
        text = """MİGROS TİCARET A.Ş.
İstanbul Şubesi
Tarih: 01.01.2026
TOPLAM: 50,00 TL"""
        result = self.service.extract(text)
        assert result.vendor_name == "MİGROS TİCARET A.Ş."

    def test_parse_turkish_amount(self):
        """Test parsing Turkish amount format."""
        assert self.service._parse_turkish_amount("1.234,56") == Decimal("1234.56")
        assert self.service._parse_turkish_amount("999,99") == Decimal("999.99")
        assert self.service._parse_turkish_amount("50,00 TL") == Decimal("50.00")

    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        text = """BİM A.Ş.
VKN: 1234567890
Tarih: 15.01.2026
TOPLAM: 100,00 TL
KDV: 18,00"""
        result = self.service.extract(text)
        assert result.confidence > 50  # Should have decent confidence


class TestVendorMatcher:
    """Tests for the vendor matcher service."""

    def setup_method(self):
        """Setup vendor matcher for each test."""
        self.matcher = VendorMatcher()

    def test_normalize_name_basic(self):
        """Test basic name normalization."""
        assert self.matcher.normalize_name("MİGROS") == "migros"
        assert self.matcher.normalize_name("  BİM  ") == "bim"

    def test_normalize_name_removes_suffixes(self):
        """Test that company suffixes are removed."""
        assert self.matcher.normalize_name("Migros Tic. Ltd. Şti.") == "migros"
        assert self.matcher.normalize_name("ABC Şirketi A.Ş.") == "abc"

    def test_normalize_name_removes_punctuation(self):
        """Test punctuation removal."""
        assert self.matcher.normalize_name("A&B Market") == "ab market"

    def test_similarity_exact_match(self):
        """Test similarity for exact match."""
        score = self.matcher.calculate_similarity("migros", "migros")
        assert score == 1.0

    def test_similarity_partial_match(self):
        """Test similarity for partial match."""
        score = self.matcher.calculate_similarity("migros", "migroz")
        assert score > 0.7  # Should be similar

    def test_similarity_no_match(self):
        """Test similarity for non-matching strings."""
        score = self.matcher.calculate_similarity("abc", "xyz")
        assert score < 0.5


class TestExtractionEdgeCases:
    """Edge case tests for extraction."""

    def setup_method(self):
        self.service = ExtractionService()

    def test_multiple_amounts_returns_largest(self):
        """Test that largest amount is returned as total."""
        text = """
Item 1: 10,00 TL
Item 2: 20,00 TL
TOPLAM: 50,00 TL
"""
        result = self.service.extract(text)
        assert result.total_gross == Decimal("50.00")

    def test_kdv_extraction(self):
        """Test KDV (tax) extraction."""
        text = "KDV %18: 18,00 TL\nTOPLAM: 100,00 TL"
        result = self.service.extract(text)
        assert result.total_tax == Decimal("18.00")

    def test_handles_ocr_noise(self):
        """Test handling of OCR noise in text."""
        text = "M|GR0S\n123 456 78 90\nT0PLAM: 50,00"
        result = self.service.extract(text)
        # Should not crash, may or may not extract correctly
        assert result is not None
