"""add late charge interest period tracking

Revision ID: 2960f8f6d267
Revises: b10787dd0d5f
Create Date: 2026-04-14 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2960f8f6d267"
down_revision = "b10787dd0d5f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "late_charges",
        sa.Column(
            "interest_periods_accrued",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.create_check_constraint(
        "ck_late_charges_interest_periods_accrued_nonnegative",
        "late_charges",
        "interest_periods_accrued >= 0",
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "ck_late_charges_interest_periods_accrued_nonnegative",
        "late_charges",
        type_="check",
    )
    op.drop_column("late_charges", "interest_periods_accrued")
