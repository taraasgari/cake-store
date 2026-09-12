from shop_core.catalog.slugs import build_unique_product_slug


def test_catalog_slug_helper_imports():
    assert callable(build_unique_product_slug)
