"""Business services package."""

from app.services.audit import record_audit_log, snapshot_model
from app.services.auth import (
    AuthenticationError,
    InactiveUserError,
    authenticate_user,
    get_user_by_email,
    get_user_by_id,
    issue_access_token_for_user,
)
from app.services.borrower import (
    BorrowerNotFoundError,
    create_borrower,
    deactivate_borrower,
    get_borrower,
    list_borrowers,
    update_borrower,
)
from app.services.loan import (
    ActiveLoanConflictError,
    LoanBorrowerNotFoundError,
    LoanCreatorNotFoundError,
    LoanValidationError,
    create_loan,
)
from app.services.payment import (
    BackdatedPaymentNotAllowedError,
    PaymentBorrowerNotFoundError,
    PaymentLoanNotFoundError,
    PaymentRecorderNotFoundError,
    PaymentValidationError,
    record_payment,
)
from app.services.overdue import (
    OverdueProcessingResult,
    process_loan_overdue_state,
    process_overdue_loans,
)
from app.services.reporting import (
    get_dashboard_summary,
    list_borrower_loan_history,
    list_overdue_loans,
    list_recent_payments,
)
from app.services.repayment_schedule import (
    build_repayment_schedule,
    build_schedule_items,
)

__all__ = [
    "ActiveLoanConflictError",
    "AuthenticationError",
    "BackdatedPaymentNotAllowedError",
    "BorrowerNotFoundError",
    "InactiveUserError",
    "LoanBorrowerNotFoundError",
    "LoanCreatorNotFoundError",
    "LoanValidationError",
    "PaymentBorrowerNotFoundError",
    "PaymentLoanNotFoundError",
    "PaymentRecorderNotFoundError",
    "PaymentValidationError",
    "OverdueProcessingResult",
    "build_repayment_schedule",
    "build_schedule_items",
    "create_borrower",
    "create_loan",
    "deactivate_borrower",
    "get_borrower",
    "get_user_by_email",
    "get_user_by_id",
    "get_dashboard_summary",
    "issue_access_token_for_user",
    "list_borrowers",
    "list_borrower_loan_history",
    "list_overdue_loans",
    "list_recent_payments",
    "process_loan_overdue_state",
    "process_overdue_loans",
    "record_audit_log",
    "record_payment",
    "authenticate_user",
    "snapshot_model",
    "update_borrower",
]
