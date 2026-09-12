from types import SimpleNamespace

from shop_core.config import get_shop_features


def test_feature_defaults_and_override():
    settings_obj = SimpleNamespace(
        SHOP_FEATURES={
            "analytics": False,
            "unknown": False,
        }
    )

    features = get_shop_features(settings_obj)

    assert features["analytics"] is False
    assert features["wishlist"] is True
    assert "unknown" not in features
