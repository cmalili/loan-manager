"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.router import api_router


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Loan Manager API",
        version="0.1.0",
    )

    @app.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        """Basic health-check endpoint."""

        return {"status": "ok"}

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_application()
