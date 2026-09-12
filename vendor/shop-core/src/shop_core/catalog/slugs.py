"""Canonical Unicode product slug validation and uniqueness."""
from django.core.exceptions import ValidationError
from django.core.validators import validate_unicode_slug
from .management import unique_catalog_slug


def validate_manual_slug(model, value, exclude_pk=None):
    value = str(value or '').strip()
    if not value:
        return ''
    if len(value) > model._meta.get_field('slug').max_length:
        raise ValidationError('اسلاگ بیش از حد طولانی است.')
    try:
        validate_unicode_slug(value)
    except ValidationError as exc:
        raise ValidationError('اسلاگ فقط می‌تواند شامل حروف، عدد، خط تیره و زیرخط باشد.') from exc
    if model.objects.filter(slug=value).exclude(pk=exclude_pk).exists():
        raise ValidationError('این اسلاگ قبلاً استفاده شده است.')
    return value


def build_unique_product_slug(product_model, product, value, name):
    return validate_manual_slug(product_model, value, product.pk) or unique_catalog_slug(
        product_model, name, exclude_pk=product.pk
    )
