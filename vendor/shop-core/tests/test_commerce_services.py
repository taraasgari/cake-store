from shop_core.commerce.services import (
    CommerceError,
    checkout_payload,
    update_product_stock,
)


def test_checkout_payload_normalizes_persian_digits():
    payload = checkout_payload(
        address="Tehran sample address",
        postal_code="۱۲۳۴۵۶۷۸۹۰",
        phone="۰۹۱۲۳۴۵۶۷۸۹",
        payment_method="cash",
        note="",
        allowed_payment_methods={"cash", "online"},
    )

    assert payload["postal_code"] == "1234567890"
    assert payload["phone"] == "09123456789"
    assert payload["payment_method"] == "cash"


def test_checkout_payload_rejects_online_until_gateway_exists():
    try:
        checkout_payload(
            address="Tehran sample address",
            postal_code="1234567890",
            phone="09123456789",
            payment_method="online",
            note="",
            allowed_payment_methods={"cash", "online"},
        )
    except CommerceError as exc:
        assert exc.code == "online_disabled"
    else:
        raise AssertionError("online payment must be rejected")


class _Product:
    has_variants = False
    stock = 1
    is_available = True

    def __init__(self):
        self.saved = None

    def save(self, update_fields):
        self.saved = update_fields


def test_update_product_stock_updates_availability():
    product = _Product()
    value = update_product_stock(
        product,
        "0",
    )

    assert value == 0
    assert product.stock == 0
    assert product.is_available is False
    assert "updated_at" in product.saved
