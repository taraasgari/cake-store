from shop_core.catalog.discounts import core_discounts


def test_catalog_discounts_import():
    assert callable(core_discounts)
