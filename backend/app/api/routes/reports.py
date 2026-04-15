"""Reporting API routes."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reporting import (
    DashboardSummaryRead,
    OverdueLoanRead,
    RecentPaymentRead,
)
from app.services.reporting import (
    get_dashboard_summary,
    list_overdue_loans,
    list_recent_payments,
)


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/overdue-loans", response_model=list[OverdueLoanRead])
def list_overdue_loans_endpoint(
    as_of_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
) -> list[OverdueLoanRead]:
    """Return overdue loans derived from current delinquency state."""

    return list_overdue_loans(db, as_of_date=as_of_date)


@router.get("/recent-payments", response_model=list[RecentPaymentRead])
def list_recent_payments_endpoint(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[RecentPaymentRead]:
    """Return recent recorded payments."""

    return list_recent_payments(db, limit=limit)


@router.get("/dashboard-summary", response_model=DashboardSummaryRead)
def get_dashboard_summary_endpoint(
    as_of_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
) -> DashboardSummaryRead:
    """Return top-level dashboard metrics."""

    return get_dashboard_summary(db, as_of_date=as_of_date)
