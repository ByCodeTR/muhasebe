"""
OCR Service using Tesseract with image preprocessing.
"""
import io
import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image
import pytesseract

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OCRService:
    """
    OCR service for extracting text from receipt/invoice images.
    Uses Tesseract with OpenCV preprocessing for better accuracy.
    """

    def __init__(self):
        """Initialize OCR service."""
        # Set Tesseract path if configured
        if settings.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_path
        
        # OCR configuration for Turkish receipts
        self.ocr_config = r'--oem 3 --psm 6 -l tur+eng'

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy.
        
        Steps:
        1. Convert to grayscale
        2. Denoise
        3. Threshold (binarization)
        4. Deskew
        5. Remove borders
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Increase contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Adaptive thresholding for varying lighting conditions
        thresh = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Deskew the image
        deskewed = self._deskew(thresh)
        
        return deskewed

    def _deskew(self, image: np.ndarray) -> np.ndarray:
        """Deskew the image using Hough line transform."""
        try:
            # Find lines in the image
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(
                edges, 1, np.pi / 180, 100, 
                minLineLength=100, maxLineGap=10
            )
            
            if lines is None:
                return image
            
            # Calculate the average angle
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                if -45 < angle < 45:  # Only consider near-horizontal lines
                    angles.append(angle)
            
            if not angles:
                return image
            
            median_angle = np.median(angles)
            
            # Only deskew if angle is significant
            if abs(median_angle) < 0.5:
                return image
            
            # Rotate the image
            height, width = image.shape[:2]
            center = (width // 2, height // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(
                image, rotation_matrix, (width, height),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            
            return rotated
        except Exception as e:
            logger.warning(f"Deskew failed: {e}")
            return image

    def extract_text(self, image_path: str) -> dict:
        """
        Extract text from an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            dict with:
                - text: Extracted text
                - confidence: Average confidence score (0-100)
                - words: List of word data with bounding boxes
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Preprocess
            processed = self.preprocess_image(image)
            
            # OCR with detailed output
            data = pytesseract.image_to_data(
                processed, 
                config=self.ocr_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text and calculate confidence
            words = []
            confidences = []
            text_parts = []
            
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                conf = int(data['conf'][i])
                text = data['text'][i].strip()
                
                if text and conf > 0:
                    words.append({
                        'text': text,
                        'confidence': conf,
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                    })
                    confidences.append(conf)
                    text_parts.append(text)
            
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Get full text (also preserving line breaks)
            full_text = pytesseract.image_to_string(
                processed, 
                config=self.ocr_config
            )
            
            return {
                'text': full_text.strip(),
                'confidence': round(avg_confidence, 2),
                'words': words,
                'word_count': len(words),
            }
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return {
                'text': '',
                'confidence': 0,
                'words': [],
                'word_count': 0,
                'error': str(e),
            }

    def extract_text_from_bytes(self, image_bytes: bytes) -> dict:
        """
        Extract text from image bytes (for uploaded files).
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Same as extract_text()
        """
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Could not decode image bytes")
            
            # Preprocess
            processed = self.preprocess_image(image)
            
            # OCR
            full_text = pytesseract.image_to_string(
                processed, 
                config=self.ocr_config
            )
            
            # Get confidence data
            data = pytesseract.image_to_data(
                processed, 
                config=self.ocr_config,
                output_type=pytesseract.Output.DICT
            )
            
            confidences = [int(c) for c in data['conf'] if int(c) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'text': full_text.strip(),
                'confidence': round(avg_confidence, 2),
                'word_count': len([t for t in data['text'] if t.strip()]),
            }
            
        except Exception as e:
            logger.error(f"OCR extraction from bytes failed: {e}")
            return {
                'text': '',
                'confidence': 0,
                'word_count': 0,
                'error': str(e),
            }


# Singleton instance
_ocr_service: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    """Get or create OCR service instance."""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
