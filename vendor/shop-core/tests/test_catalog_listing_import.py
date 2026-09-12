from shop_core.catalog.listing import core_product_list


def test_catalog_listing_import():
    assert callable(core_product_list)
