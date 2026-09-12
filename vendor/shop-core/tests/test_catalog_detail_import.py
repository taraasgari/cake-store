from shop_core.catalog.detail import core_product_detail


def test_catalog_detail_import():
    assert callable(core_product_detail)
