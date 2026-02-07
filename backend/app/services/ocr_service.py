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
        import shutil
        
        # Try to find tesseract binary dynamically
        # 1. Check specific common paths first (Docker/Linux standard)
        common_paths = ["/usr/bin/tesseract", "/usr/local/bin/tesseract"]
        found_path = None
        
        for p in common_paths:
            if Path(p).exists() and Path(p).is_file():
                found_path = p
                logger.info(f"Tesseract found at explicit path: {p}")
                break
        
        # 2. If not found, try shutil.which (PATH lookup)
        if not found_path:
            found_path = shutil.which("tesseract")
            if found_path:
                logger.info(f"Tesseract found via PATH: {found_path}")

        # 3. Configure PyTesseract
        if found_path:
            pytesseract.pytesseract.tesseract_cmd = found_path
        else:
            logger.error("CRITICAL: Tesseract binary NOT found in paths or PATH variable!")
            # Don't set cmd, let it default (and likely fail, but we logged it)
        
        # Tesseract language auto-discovery
        try:
            available_langs = pytesseract.get_languages(config='')
            logger.info(f"Available Tesseract languages: {available_langs}")
            if 'tur' in available_langs:
                self.ocr_config = r'--oem 3 --psm 6 -l tur+eng'
            else:
                logger.warning("'tur' language data not found, falling back to 'eng'")
                self.ocr_config = r'--oem 3 --psm 6 -l eng'
        except Exception as e:
            logger.error(f"Failed to detect languages: {e}. Defaulting to 'eng'.")
            self.ocr_config = r'--oem 3 --psm 6 -l eng'

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
            try:
                # Try with preprocessed image
                data = pytesseract.image_to_data(
                    processed, 
                    config=self.ocr_config,
                    output_type=pytesseract.Output.DICT
                )
                
                # If no text found, try raw image
                if not any(t.strip() for t in data['text']):
                    logger.warning("No text found in preprocessed image, trying raw image")
                    data = pytesseract.image_to_data(
                        image, 
                        config=self.ocr_config,
                        output_type=pytesseract.Output.DICT
                    )
            except pytesseract.TesseractError as e:
                logger.error(f"Tesseract error with config {self.ocr_config}: {e}")
                # Fallback to English only if Turkish fails
                fallback_config = '--oem 3 --psm 6'
                data = pytesseract.image_to_data(
                    image, 
                    config=fallback_config,
                    output_type=pytesseract.Output.DICT
                )

            # Extract text and calculate confidence
            words = []
            confidences = []
            
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
            
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Reconstruct full text
            full_text = " ".join([w['text'] for w in words])
            
            # If still empty, return debug info
            if not full_text:
                import shutil
                tess_path = shutil.which("tesseract") or "Not found"
                return {
                    'text': f"[DEBUG] OCR returned empty. Tesseract path: {tess_path}. Config: {self.ocr_config}",
                    'confidence': 0,
                    'words': [],
                    'word_count': 0,
                }
            
            return {
                'text': full_text,
                'confidence': round(avg_confidence, 2),
                'words': words,
                'word_count': len(words),
            }
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            import traceback
            return {
                'text': f"[ERROR] OCR Failed: {str(e)}\n{traceback.format_exc()}",
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
