"""
Field extraction service for Turkish receipts/invoices.
Extracts structured data from OCR text using regex patterns and heuristics.
"""
import re
import logging
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Structured extraction result."""
    vendor_name: Optional[str] = None
    vendor_vkn: Optional[str] = None
    vendor_tckn: Optional[str] = None
    doc_date: Optional[date] = None
    total_gross: Optional[Decimal] = None
    total_tax: Optional[Decimal] = None
    total_net: Optional[Decimal] = None
    doc_no: Optional[str] = None
    currency: str = "TRY"
    confidence: float = 0.0
    extraction_details: dict = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = asdict(self)
        # Convert date to string
        if result['doc_date']:
            result['doc_date'] = result['doc_date'].isoformat()
        # Convert Decimal to float
        for key in ['total_gross', 'total_tax', 'total_net']:
            if result[key]:
                result[key] = float(result[key])
        return result


class ExtractionService:
    """
    Service for extracting structured fields from OCR text.
    Optimized for Turkish receipts and invoices.
    """

    # Date patterns commonly used in Turkish receipts
    DATE_PATTERNS = [
        # DD.MM.YYYY or DD/MM/YYYY
        r'(\d{1,2})[./](\d{1,2})[./](20\d{2})',
        # DD-MM-YYYY
        r'(\d{1,2})-(\d{1,2})-(20\d{2})',
        # YYYY.MM.DD
        r'(20\d{2})[./](\d{1,2})[./](\d{1,2})',
        # DD MONTH YYYY (Turkish)
        r'(\d{1,2})\s+(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+(20\d{2})',
    ]
    
    # Turkish month names
    TURKISH_MONTHS = {
        'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
        'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
        'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12,
    }
    
    # Amount patterns for Turkish Lira
    AMOUNT_PATTERNS = [
        # *1.234,56 or *1234,56 (with asterisk prefix common in receipts)
        r'\*?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2}))',
        # 1.234,56 TL or 1234,56 TL
        r'(\d{1,3}(?:\.\d{3})*(?:,\d{2}))\s*(?:TL|TRY|₺)',
        # Just the amount pattern
        r'(\d{1,3}(?:\.\d{3})*,\d{2})',
    ]
    
    # Total keywords in Turkish
    TOTAL_KEYWORDS = [
        'toplam', 'genel toplam', 'ödenecek tutar', 'tutar',
        'net tutar', 'brüt tutar', 'total', 'grand total',
        'yekun', 'ödenen', 'nakit', 'kredi kartı',
    ]
    
    # Tax keywords
    TAX_KEYWORDS = [
        'kdv', 'k.d.v', 'vergi', 'tax', 'kdv toplam',
        'kdv tutarı', '%8', '%10', '%18', '%20',
    ]
    
    # VKN/TCKN patterns
    VKN_PATTERN = r'(?:VKN|V\.K\.N|VERGİ\s*(?:KİMLİK)?\s*(?:NO|NUMARASI)?)[:\s]*(\d{10,11})'
    TCKN_PATTERN = r'(?:TCKN|T\.C\.?(?:\s*KİMLİK)?\s*(?:NO|NUMARASI)?)[:\s]*(\d{11})'
    
    # Document number patterns
    DOC_NO_PATTERNS = [
        r'(?:FİŞ|BELGE|FATURA)\s*(?:NO|NUMARASI?)[:\s]*([A-Z0-9\-]+)',
        r'(?:NO|NUMARA)[:\s]*([A-Z0-9\-]+)',
    ]

    def extract(self, ocr_text: str) -> ExtractionResult:
        """
        Extract structured data from OCR text.
        
        Args:
            ocr_text: Raw text from OCR
            
        Returns:
            ExtractionResult with extracted fields
        """
        if not ocr_text:
            return ExtractionResult()
        
        # Normalize text
        text = ocr_text.upper()
        text_lower = ocr_text.lower()
        lines = ocr_text.split('\n')
        
        # Track what we found for confidence calculation
        found_fields = []
        details = {}
        
        # Extract vendor name (usually first non-empty lines)
        vendor_name = self._extract_vendor_name(lines)
        if vendor_name:
            found_fields.append('vendor_name')
            details['vendor_name_source'] = 'header'
        
        # Extract VKN
        vkn = self._extract_vkn(text)
        if vkn:
            found_fields.append('vkn')
        
        # Extract TCKN
        tckn = self._extract_tckn(text)
        if tckn:
            found_fields.append('tckn')
        
        # Extract date
        doc_date = self._extract_date(ocr_text)
        if doc_date:
            found_fields.append('doc_date')
        
        # Extract total amount
        total_gross = self._extract_total(text_lower, lines)
        if total_gross:
            found_fields.append('total_gross')
        
        # Extract tax amount
        total_tax = self._extract_tax(text_lower, lines)
        if total_tax:
            found_fields.append('total_tax')
        
        # Extract document number
        doc_no = self._extract_doc_no(text)
        if doc_no:
            found_fields.append('doc_no')
        
        # Calculate confidence based on found fields
        field_weights = {
            'vendor_name': 0.15,
            'vkn': 0.15,
            'tckn': 0.10,
            'doc_date': 0.15,
            'total_gross': 0.25,
            'total_tax': 0.15,
            'doc_no': 0.05,
        }
        confidence = sum(field_weights.get(f, 0) for f in found_fields)
        
        # Calculate net if we have gross and tax
        total_net = None
        if total_gross and total_tax:
            total_net = total_gross - total_tax
        
        return ExtractionResult(
            vendor_name=vendor_name,
            vendor_vkn=vkn,
            vendor_tckn=tckn,
            doc_date=doc_date,
            total_gross=total_gross,
            total_tax=total_tax,
            total_net=total_net,
            doc_no=doc_no,
            currency="TRY",
            confidence=round(confidence * 100, 1),
            extraction_details=details,
        )

    def _extract_vendor_name(self, lines: list[str]) -> Optional[str]:
        """Extract vendor name from the first lines."""
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            # Skip empty lines, dates, and numeric lines
            if not line:
                continue
            if re.match(r'^[\d\s\-\./]+$', line):
                continue
            if len(line) < 3:
                continue
            # Skip lines that look like addresses
            if any(k in line.lower() for k in ['sok.', 'cad.', 'mah.', 'no:', 'apt']):
                continue
            # This is likely the vendor name
            return line
        return None

    def _extract_vkn(self, text: str) -> Optional[str]:
        """Extract VKN (Vergi Kimlik Numarası)."""
        match = re.search(self.VKN_PATTERN, text, re.IGNORECASE)
        if match:
            vkn = match.group(1)
            # VKN should be 10 or 11 digits
            if len(vkn) in [10, 11]:
                return vkn
        
        # Try to find standalone 10-11 digit number near tax-related words
        tax_words = ['vergi', 'vkn', 'dairesi']
        for word in tax_words:
            idx = text.lower().find(word)
            if idx >= 0:
                nearby = text[idx:idx+50]
                numbers = re.findall(r'\b(\d{10,11})\b', nearby)
                if numbers:
                    return numbers[0]
        
        return None

    def _extract_tckn(self, text: str) -> Optional[str]:
        """Extract TCKN (TC Kimlik Numarası)."""
        match = re.search(self.TCKN_PATTERN, text, re.IGNORECASE)
        if match:
            tckn = match.group(1)
            if len(tckn) == 11:
                return tckn
        return None

    def _extract_date(self, text: str) -> Optional[date]:
        """Extract date from text."""
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    
                    # Handle Turkish month names
                    if len(groups) == 3:
                        if groups[1].lower() in self.TURKISH_MONTHS:
                            day = int(groups[0])
                            month = self.TURKISH_MONTHS[groups[1].lower()]
                            year = int(groups[2])
                        elif len(groups[0]) == 4:  # YYYY.MM.DD format
                            year = int(groups[0])
                            month = int(groups[1])
                            day = int(groups[2])
                        else:  # DD.MM.YYYY format
                            day = int(groups[0])
                            month = int(groups[1])
                            year = int(groups[2])
                        
                        return date(year, month, day)
                except (ValueError, IndexError):
                    continue
        return None

    def _parse_turkish_amount(self, amount_str: str) -> Optional[Decimal]:
        """
        Parse Turkish formatted amount (1.234,56) to Decimal.
        """
        try:
            # Remove spaces and currency symbols
            cleaned = amount_str.strip()
            cleaned = re.sub(r'[TL₺\s]', '', cleaned)
            
            # Remove thousand separators (dots) and replace decimal comma
            cleaned = cleaned.replace('.', '').replace(',', '.')
            
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None

    def _extract_total(self, text: str, lines: list[str]) -> Optional[Decimal]:
        """Extract total amount."""
        # First, look for lines containing total keywords
        for keyword in self.TOTAL_KEYWORDS:
            for line in lines:
                line_lower = line.lower()
                if keyword in line_lower:
                    # Find amount in this line
                    for pattern in self.AMOUNT_PATTERNS:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            amount = self._parse_turkish_amount(match.group(1))
                            if amount and amount > 0:
                                return amount
        
        # Fallback: find the largest amount (often the total)
        all_amounts = []
        for pattern in self.AMOUNT_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                amount = self._parse_turkish_amount(m)
                if amount and amount > 0:
                    all_amounts.append(amount)
        
        if all_amounts:
            # Return the largest amount
            return max(all_amounts)
        
        return None

    def _extract_tax(self, text: str, lines: list[str]) -> Optional[Decimal]:
        """Extract tax (KDV) amount."""
        for keyword in self.TAX_KEYWORDS:
            for line in lines:
                line_lower = line.lower()
                if keyword in line_lower:
                    # Skip if this is a rate line (e.g., "KDV %18")
                    if re.search(r'%\s*\d+', line):
                        # Find amount after the rate
                        match = re.search(r'%\s*\d+\s*[:\s]*(\d{1,3}(?:\.\d{3})*,\d{2})', line)
                        if match:
                            amount = self._parse_turkish_amount(match.group(1))
                            if amount and amount > 0:
                                return amount
                    else:
                        # Find amount in this line
                        for pattern in self.AMOUNT_PATTERNS:
                            match = re.search(pattern, line, re.IGNORECASE)
                            if match:
                                amount = self._parse_turkish_amount(match.group(1))
                                if amount and amount > 0:
                                    return amount
        
        return None

    def _extract_doc_no(self, text: str) -> Optional[str]:
        """Extract document/receipt number."""
        for pattern in self.DOC_NO_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None


# Singleton instance
_extraction_service: Optional[ExtractionService] = None


def get_extraction_service() -> ExtractionService:
    """Get or create extraction service instance."""
    global _extraction_service
    if _extraction_service is None:
        _extraction_service = ExtractionService()
    return _extraction_service
