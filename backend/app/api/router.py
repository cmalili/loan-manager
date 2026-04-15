"""Top-level API router."""

from fastapi import APIRouter

from app.api.routes import borrowers_router, loans_router, payments_router, reports_router

api_router = APIRouter()
api_router.include_router(borrowers_router)
api_router.include_router(loans_router)
api_router.include_router(payments_router)
api_router.include_router(reports_router)
