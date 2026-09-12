"""Reusable review domain services.

The client project owns request/auth/permission/presentation concerns and
supplies the concrete model classes. This module owns reusable review logic.
"""


def create_product_review(*, review_model, product, user, rating, comment):
    if review_model.objects.filter(user=user, product=product).exists():
        return None, "duplicate"

    try:
        normalized_rating = int(rating)
    except (TypeError, ValueError):
        normalized_rating = 0

    normalized_comment = (comment or "").strip()

    if normalized_rating not in {1, 2, 3, 4, 5}:
        return None, "invalid_rating"
    if not normalized_comment:
        return None, "empty_comment"
    if len(normalized_comment) > 5000:
        return None, "comment_too_long"

    review = review_model.objects.create(
        product=product,
        user=user,
        rating=normalized_rating,
        comment=normalized_comment,
        is_verified=False,
    )
    return review, None


def recalculate_product_rating(product):
    reviews = product.reviews.filter(is_verified=True)

    if reviews.exists():
        rating = sum(review.rating for review in reviews) / reviews.count()
    else:
        rating = 0

    product.rating = rating
    product.save()
    return rating


def verify_product_review(review):
    review.is_verified = True
    review.save()
    recalculate_product_rating(review.product)
    return review


def delete_product_review(review):
    product = review.product
    review.delete()
    recalculate_product_rating(product)
    return product


def admin_review_data(review_model, status=None):
    reviews = review_model.objects.all().order_by("-created_at")

    if status == "verified":
        reviews = reviews.filter(is_verified=True)
    elif status == "unverified":
        reviews = reviews.filter(is_verified=False)

    counts = {
        "total_reviews": review_model.objects.count(),
        "verified_count": review_model.objects.filter(is_verified=True).count(),
        "unverified_count": review_model.objects.filter(is_verified=False).count(),
    }
    return reviews, counts
