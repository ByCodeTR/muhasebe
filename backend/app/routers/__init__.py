"""
API Routers
"""
from app.routers.health import router as health_router
from app.routers.documents import router as documents_router
from app.routers.vendors import router as vendors_router
from app.routers.ledger import router as ledger_router
from app.routers.reports import router as reports_router
from app.routers.telegram import router as telegram_router

__all__ = [
    "health_router",
    "documents_router",
    "vendors_router",
    "ledger_router",
    "reports_router",
    "telegram_router",
]
