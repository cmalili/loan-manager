"""Shared money helpers for financial service logic."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


MONEY_PLACES = Decimal("0.01")
ONE_HUNDRED = Decimal("100")
ZERO = Decimal("0.00")


def quantize_money(value: Decimal) -> Decimal:
    """Round money values to two decimal places using the project rule."""

    return value.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)
