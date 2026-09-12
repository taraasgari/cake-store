from shop_core.accounts.decorators import (
    admin_required,
    owner_required,
)


def test_access_decorators_import():
    assert callable(admin_required)
    assert callable(owner_required)
