"""Reusable catalog-management services."""

import re
import secrets

from django.db import transaction
from django.utils.text import slugify


def _meta_field(model, field_name):
    """Return a model field when metadata supports it, otherwise None.

    shop-core is intentionally reusable and some unit tests use lightweight
    model doubles. Those doubles may expose only part of Django's _meta API,
    so catalog helpers should not crash merely while discovering limits.
    """
    meta = getattr(model, "_meta", None)
    if meta is None:
        return None

    get_field = getattr(meta, "get_field", None)
    if not callable(get_field):
        return None

    try:
        return get_field(field_name)
    except (LookupError, AttributeError, AssertionError):
        return None


def _field_max_length(model, field_name, default=200):
    field = _meta_field(model, field_name)
    value = getattr(field, "max_length", None) if field is not None else None
    return value or default


def _declared_field_names(model):
    """Return declared concrete field names, or None for lightweight doubles."""
    meta = getattr(model, "_meta", None)
    fields = getattr(meta, "fields", None)
    if fields is None:
        return None

    return {
        getattr(field, "name", None)
        for field in fields
        if getattr(field, "name", None)
    }


def admin_product_data(
    product_model,
    category_model,
    *,
    search=None,
    category_id=None,
    status=None,
):
    products = product_model.objects.all().order_by("-created_at")

    if search:
        products = products.filter(name__icontains=search)

    if category_id:
        products = products.filter(category_id=category_id)

    if status == "active":
        products = products.filter(is_active=True)
    elif status == "inactive":
        products = products.filter(is_active=False)

    categories = category_model.objects.filter(is_active=True)
    return products, categories


def deactivate_product(
    product_model,
    variant_model,
    product_id,
):
    with transaction.atomic():
        product = (
            product_model.objects
            .select_for_update()
            .get(pk=product_id)
        )

        product_name = product.name
        product.is_active = False
        product.is_available = False
        product.save(
            update_fields=[
                "is_active",
                "is_available",
                "updated_at",
            ]
        )

        variant_model.objects.filter(
            product=product
        ).update(
            is_active=False,
            is_default=False,
        )

    return product_name


def unique_catalog_slug(
    model,
    name,
    exclude_pk=None,
):
    # Real Django models expose a slug field. Lightweight reusable-core tests
    # may expose only a name field, so fall back safely instead of coupling
    # this helper to a complete Django Model _meta implementation.
    max_length = _field_max_length(
        model,
        "slug",
        default=_field_max_length(
            model,
            "name",
            default=200,
        ),
    )

    base = slugify(
        name,
        allow_unicode=True,
    ).strip("-")[:max_length]

    if not base:
        base = f"item-{secrets.token_hex(4)}"[:max_length]

    candidate = base
    serial = 2

    query = model.objects.all()
    if exclude_pk is not None:
        query = query.exclude(pk=exclude_pk)

    while query.filter(slug=candidate).exists():
        suffix = f"-{serial}"
        candidate = base[: max(1, max_length - len(suffix))] + suffix
        serial += 1

    return candidate


def create_named_catalog_item(
    model,
    name,
    *,
    slug=None,
    parent_id=None,
):
    normalized = (name or "").strip()
    max_length = _field_max_length(
        model,
        "name",
        default=200,
    )

    if not normalized:
        return None, "required", False

    if len(normalized) > max_length:
        return None, "too_long", False

    existing = model.objects.filter(
        name__iexact=normalized
    ).first()

    if existing:
        if hasattr(existing, "is_active") and not existing.is_active:
            existing.is_active = True
            existing.save(update_fields=["is_active"])

        return existing, None, True

    from .slugs import validate_manual_slug

    values = {
        "name": normalized,
        "slug": (
            validate_manual_slug(model, slug)
            or unique_catalog_slug(model, normalized)
        ),
    }

    field_names = _declared_field_names(model)

    # All real catalog models declare is_active where appropriate. When a
    # lightweight test double has no concrete-field list, keep the historical
    # reusable-core behavior and create catalog entries as active.
    if field_names is None or "is_active" in field_names:
        values["is_active"] = True

    if field_names is not None and "parent" in field_names:
        values["parent_id"] = parent_id or None

    # Real Django models are validated before save. Minimal model doubles used
    # by shop-core unit tests intentionally provide only Manager.create().
    if field_names is None:
        item = model.objects.create(**values)
    else:
        item = model(**values)
        item.full_clean(exclude=["slug"])
        item.save()

    return item, None, False


def upsert_color(
    color_model,
    *,
    name,
    code,
    image=None,
):
    normalized_name = (name or "").strip()
    normalized_code = (code or "").strip().upper()

    if not normalized_name:
        return None, "required", False

    if not re.fullmatch(r"#[0-9A-F]{6}", normalized_code):
        return None, "invalid_code", False

    from django.db.models import Q

    existing = (
        color_model.objects
        .filter(
            Q(name__iexact=normalized_name)
            | Q(code__iexact=normalized_code)
        )
        .order_by("id")
        .first()
    )

    if existing:
        if not existing.is_active:
            existing.is_active = True
            existing.save(update_fields=["is_active"])

        return existing, None, True

    color = color_model.objects.create(
        name=normalized_name,
        code=normalized_code,
        image=image,
        is_active=True,
    )
    return color, None, False


def delete_catalog_item(
    model,
    product_model,
    item_id,
    *,
    relation_field,
    reject_children=False,
):
    item = model.objects.filter(id=item_id).first()

    if item is None:
        return "not_found", 0

    product_count = product_model.objects.filter(
        **{relation_field: item}
    ).count()

    if product_count:
        return "in_use", product_count

    if reject_children and item.subcategories.exists():
        return "has_children", 0

    item.delete()
    return "deleted", 0


def update_named_catalog_item(item, *, name, slug=None, parent_id=None):
    """Preserve an omitted slug and reject category hierarchy cycles."""
    from django.core.exceptions import ValidationError
    from .slugs import validate_manual_slug

    model = type(item)
    name = str(name or "").strip()

    if not name:
        raise ValidationError("نام الزامی است.")

    if model.objects.filter(
        name__iexact=name
    ).exclude(pk=item.pk).exists():
        raise ValidationError("این نام قبلاً استفاده شده است.")

    item.name = name

    if slug is not None:
        item.slug = (
            validate_manual_slug(
                model,
                slug,
                item.pk,
            )
            or item.slug
            or unique_catalog_slug(
                model,
                name,
                item.pk,
            )
        )

    if hasattr(item, "parent_id"):
        parent = (
            model.objects.filter(pk=parent_id).first()
            if parent_id
            else None
        )

        if parent_id and parent is None:
            raise ValidationError(
                "دسته‌بندی والد معتبر نیست."
            )

        ancestor = parent
        seen = {item.pk}

        while ancestor:
            if ancestor.pk in seen:
                raise ValidationError(
                    "دسته‌بندی نمی‌تواند زیرمجموعه خود باشد."
                )

            seen.add(ancestor.pk)
            ancestor = ancestor.parent

        item.parent = parent

    item.full_clean(exclude=["slug"])
    item.save()
    return item
