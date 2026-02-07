
import sys
import os
from pathlib import Path

# Add backend directory to path so we can import app modules
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

try:
    from app.services.ocr_service import OCRService
    import pytesseract

    print("Attempting to initialize OCRService...")
    service = OCRService()
    
    print(f"\n[RESULT] Resolved Tesseract Command: {pytesseract.pytesseract.tesseract_cmd}")
    
    # Check if it actually exists
    cmd = pytesseract.pytesseract.tesseract_cmd
    if cmd and os.path.exists(cmd):
        print("[SUCCESS] Tesseract executable found on disk.")
    else:
        print("[FAILURE] Tesseract executable NOT found on disk.")

    # Try to run version check
    import subprocess
    try:
        result = subprocess.run([cmd, "--version"], capture_output=True, text=True)
        print(f"[VERSION OUTPUT]\n{result.stdout}")
    except Exception as e:
        print(f"[FAILURE] Could not run tesseract: {e}")

except Exception as e:
    print(f"\n[CRITICAL ERROR] Failed to initialize service: {e}")
    import traceback
    traceback.print_exc()
