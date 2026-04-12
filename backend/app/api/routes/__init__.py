"""Route modules package."""

from app.api.routes.borrowers import router as borrowers_router
from app.api.routes.loans import router as loans_router

__all__ = ["borrowers_router", "loans_router"]
