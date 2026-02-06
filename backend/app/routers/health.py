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
