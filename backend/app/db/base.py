"""SQLAlchemy declarative base and model registry."""

from app.db.base_class import Base


# Import models so Alembic and metadata discovery can see every table.
from app.models.audit_log import AuditLog  # noqa: E402,F401
from app.models.borrower import Borrower  # noqa: E402,F401
from app.models.late_charge import LateCharge  # noqa: E402,F401
from app.models.loan import Loan  # noqa: E402,F401
from app.models.payment import Payment  # noqa: E402,F401
from app.models.payment_allocation import PaymentAllocation  # noqa: E402,F401
from app.models.repayment_schedule_item import RepaymentScheduleItem  # noqa: E402,F401
from app.models.user import User  # noqa: E402,F401
