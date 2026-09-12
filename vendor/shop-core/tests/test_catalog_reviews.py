from shop_core.catalog.reviews import (
    create_product_review,
    recalculate_product_rating,
)


class _ExistsResult:
    def __init__(self, value):
        self.value = value

    def exists(self):
        return self.value


class _CreateManager:
    def __init__(self):
        self.exists_value = False
        self.created = []

    def filter(self, **kwargs):
        return _ExistsResult(self.exists_value)

    def create(self, **kwargs):
        self.created.append(kwargs)
        return kwargs


def test_create_product_review_normalizes_input():
    manager = _CreateManager()

    class ReviewModel:
        objects = manager

    review, error = create_product_review(
        review_model=ReviewModel,
        product=object(),
        user=object(),
        rating="5",
        comment="  useful review  ",
    )

    assert error is None
    assert review["rating"] == 5
    assert review["comment"] == "useful review"
    assert review["is_verified"] is False


def test_create_product_review_rejects_duplicate_first():
    manager = _CreateManager()
    manager.exists_value = True

    class ReviewModel:
        objects = manager

    review, error = create_product_review(
        review_model=ReviewModel,
        product=object(),
        user=object(),
        rating="5",
        comment="ok",
    )

    assert review is None
    assert error == "duplicate"
    assert manager.created == []


class _VerifiedReviews:
    def __init__(self, ratings):
        self.items = [type("Review", (), {"rating": rating})() for rating in ratings]

    def exists(self):
        return bool(self.items)

    def count(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)


class _ReviewRelation:
    def __init__(self, ratings):
        self.ratings = ratings

    def filter(self, **kwargs):
        assert kwargs == {"is_verified": True}
        return _VerifiedReviews(self.ratings)


class _Product:
    def __init__(self, ratings):
        self.reviews = _ReviewRelation(ratings)
        self.rating = None
        self.saved = False

    def save(self):
        self.saved = True


def test_recalculate_product_rating():
    product = _Product([5, 3, 4])
    rating = recalculate_product_rating(product)
    assert rating == 4
    assert product.rating == 4
    assert product.saved is True


def test_recalculate_empty_product_rating_is_zero():
    product = _Product([])
    rating = recalculate_product_rating(product)
    assert rating == 0
    assert product.rating == 0
    assert product.saved is True
