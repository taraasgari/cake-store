\
"""Reusable catalog-management services."""

import re
import secrets

from django.db import transaction
from django.utils.text import slugify


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
    max_length = model._meta.get_field("slug").max_length
    base = slugify(
        name,
        allow_unicode=True,
    ).strip("-")[:max_length]

    if not base:
        base = f"item-{secrets.token_hex(4)}"

    candidate = base
    serial = 2

    query = model.objects.all()
    if exclude_pk is not None:
        query = query.exclude(pk=exclude_pk)

    while query.filter(slug=candidate).exists():
        suffix = f"-{serial}"
        candidate = base[: max_length - len(suffix)] + suffix
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
    max_length = model._meta.get_field("name").max_length or 200

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
    values = dict(name=normalized, slug=validate_manual_slug(model, slug) or unique_catalog_slug(model, normalized))
    if any(field.name == "is_active" for field in model._meta.fields):
        values["is_active"] = True
    if any(field.name == "parent" for field in model._meta.fields):
        values["parent_id"] = parent_id or None
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
    name = str(name or '').strip()
    if not name:
        raise ValidationError('نام الزامی است.')
    if model.objects.filter(name__iexact=name).exclude(pk=item.pk).exists():
        raise ValidationError('این نام قبلاً استفاده شده است.')
    item.name = name
    if slug is not None:
        item.slug = validate_manual_slug(model, slug, item.pk) or item.slug or unique_catalog_slug(model, name, item.pk)
    if hasattr(item, 'parent_id'):
        parent = model.objects.filter(pk=parent_id).first() if parent_id else None
        if parent_id and parent is None:
            raise ValidationError('دسته‌بندی والد معتبر نیست.')
        ancestor = parent
        seen = {item.pk}
        while ancestor:
            if ancestor.pk in seen:
                raise ValidationError('دسته‌بندی نمی‌تواند زیرمجموعه خود باشد.')
            seen.add(ancestor.pk)
            ancestor = ancestor.parent
        item.parent = parent
    item.full_clean(exclude=['slug'])
    item.save()
    return item
