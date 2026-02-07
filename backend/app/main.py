"""
Kişisel Muhasebe API - FastAPI Application
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import structlog

from app.config import get_settings
from app.database import init_db
from app.routers import (
    health_router,
    documents_router,
    vendors_router,
    ledger_router,
    reports_router,
    telegram_router,
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Muhasebe API", debug=settings.debug)
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down Muhasebe API")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Kişisel Muhasebe Sistemi - Fiş/Fatura takip ve raporlama",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
from app.middleware import setup_exception_handlers, log_request_middleware, rate_limit_middleware

# Setup exception handlers
setup_exception_handlers(app)

# Add request logging middleware
app.middleware("http")(log_request_middleware)

@app.middleware("http")
async def log_cors_headers(request, call_next):
    origin = request.headers.get("origin")
    logger.info(f"CORS Debug - Origin: {origin}, Allowed: {settings.cors_origins}")
    response = await call_next(request)
    return response

# Add rate limiting middleware (disable in debug mode)
if not settings.debug:
    app.middleware("http")(rate_limit_middleware)

# Include routers
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(vendors_router)
app.include_router(ledger_router)
app.include_router(reports_router)
app.include_router(telegram_router)

# Serve uploaded files (development only)
# Serve uploaded files (always enabled for local storage)
import os
upload_path = settings.upload_dir
if not os.path.exists(upload_path):
    os.makedirs(upload_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_path), name="uploads")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
