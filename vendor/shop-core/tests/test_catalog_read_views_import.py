from shop_core.catalog.read_views import (
    core_category_products,
    core_brand_products,
    core_search_products,
    core_best_sellers,
)


def test_catalog_read_views_import():
    assert callable(core_category_products)
    assert callable(core_brand_products)
    assert callable(core_search_products)
    assert callable(core_best_sellers)
