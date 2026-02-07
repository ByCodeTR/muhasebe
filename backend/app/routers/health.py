"""
Health check endpoint.
"""
from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "muhasebe-api",
        "version": "0.1.0",
    }


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Kişisel Muhasebe API",
        "docs": "/docs",
    }

@router.get("/health/ocr")
async def ocr_debug():
    """Diagnostic endpoint for OCR system."""
    import shutil
    import os
    import subprocess
    
    tesseract_path = shutil.which("tesseract")
    
    # Check common paths explicitly
    common_paths = [
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/bin/tesseract"
    ]
    path_checks = {p: os.path.exists(p) for p in common_paths}
    
    # Try running tesseract --version
    version_output = "Failed to run"
    if tesseract_path:
        try:
            result = subprocess.run(
                [tesseract_path, "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            version_output = result.stdout + result.stderr
        except Exception as e:
            version_output = str(e)
            
    # Check languages
    langs = "Unknown"
    if tesseract_path:
        try:
            result = subprocess.run(
                [tesseract_path, "--list-langs"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            langs = result.stdout
        except Exception as e:
            langs = str(e)

    return {
        "shutil_which": tesseract_path,
        "path_checks": path_checks,
        "path_env": os.environ.get("PATH"),
        "tesseract_version": version_output,
        "available_languages": langs,
    }
