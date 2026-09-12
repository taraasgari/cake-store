from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from shop_core.catalog.product_writes import (
    parse_nonnegative_decimal,
    parse_nonnegative_int,
)


def test_parse_nonnegative_decimal():
    assert parse_nonnegative_decimal("12.50", "price") == Decimal("12.50")
    assert parse_nonnegative_decimal("", "price") is None


def test_parse_nonnegative_decimal_rejects_negative():
    with pytest.raises(ValidationError):
        parse_nonnegative_decimal("-1", "price")


def test_parse_nonnegative_int():
    assert parse_nonnegative_int("7", "stock") == 7
    assert parse_nonnegative_int("", "stock", default=3) == 3


def test_parse_nonnegative_int_rejects_invalid():
    with pytest.raises(ValidationError):
        parse_nonnegative_int("x", "stock")
