"""Route modules package."""

from app.api.routes.borrowers import router as borrowers_router
from app.api.routes.loans import router as loans_router
from app.api.routes.payments import router as payments_router
from app.api.routes.reports import router as reports_router

__all__ = ["borrowers_router", "loans_router", "payments_router", "reports_router"]
