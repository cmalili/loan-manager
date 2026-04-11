"""Top-level API router."""

from fastapi import APIRouter

from app.api.routes import borrowers_router

api_router = APIRouter()
api_router.include_router(borrowers_router)
