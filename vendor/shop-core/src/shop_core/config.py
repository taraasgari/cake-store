from __future__ import annotations

from copy import deepcopy

DEFAULT_FEATURES = {
    "wishlist": True,
    "reviews": True,
    "support": True,
    "returns": True,
    "analytics": True,
    "warehouse": True,
    "customizer": True,
}


def get_shop_features(settings_obj):
    """Return normalized per-client feature flags."""
    configured = getattr(settings_obj, "SHOP_FEATURES", {}) or {}
    features = deepcopy(DEFAULT_FEATURES)

    for key, value in configured.items():
        if key in features:
            features[key] = bool(value)

    return features
