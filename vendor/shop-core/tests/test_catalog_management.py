\
from shop_core.catalog.management import (
    create_named_catalog_item,
    unique_catalog_slug,
)


class _Field:
    max_length = 20


class _Meta:
    @staticmethod
    def get_field(name):
        assert name == "name"
        return _Field()


class _Exists:
    def __init__(self, value=False):
        self.value = value

    def exists(self):
        return self.value


class _Query:
    def __init__(self, manager):
        self.manager = manager

    def exclude(self, **kwargs):
        return self

    def filter(self, **kwargs):
        if "slug" in kwargs:
            return _Exists(False)
        return self

    def first(self):
        return self.manager.existing


class _Manager:
    def __init__(self):
        self.existing = None
        self.created = []

    def all(self):
        return _Query(self)

    def filter(self, **kwargs):
        return _Query(self)

    def create(self, **kwargs):
        self.created.append(kwargs)
        return type("Item", (), kwargs)()


class _Model:
    _meta = _Meta()
    objects = _Manager()


def test_unique_catalog_slug_uses_unicode_slug():
    value = unique_catalog_slug(
        _Model,
        "کرم صورت",
    )
    assert value


def test_create_named_catalog_item_creates_new_item():
    _Model.objects = _Manager()

    item, error, existing = create_named_catalog_item(
        _Model,
        "Brand X",
    )

    assert error is None
    assert existing is False
    assert item.name == "Brand X"
    assert _Model.objects.created[0]["is_active"] is True


def test_create_named_catalog_item_rejects_empty_name():
    _Model.objects = _Manager()

    item, error, existing = create_named_catalog_item(
        _Model,
        "   ",
    )

    assert item is None
    assert error == "required"
    assert existing is False
