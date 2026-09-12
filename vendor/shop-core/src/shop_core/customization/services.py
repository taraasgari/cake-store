import json
import re
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from shop_core.catalog.management import unique_catalog_slug


_CUSTOMIZER_COLORS = re.compile(
    r"^#[0-9a-fA-F]{6}$"
)

_CUSTOMIZER_IDS = re.compile(
    r"^[a-zA-Z0-9_-]{1,120}$"
)

_CUSTOMIZER_LENGTH = re.compile(
    r"^(?:0|\d{1,4}(?:\.\d{1,2})?)"
    r"(?:px|%|rem|em|vw|vh)?$"
)

_CUSTOMIZER_STYLES = {
    "color",
    "backgroundColor",
    "fontSize",
    "fontWeight",
    "fontFamily",
    "textAlign",
    "lineHeight",
    "letterSpacing",
    "borderRadius",
    "opacity",
    "padding",
    "margin",
    "objectFit",
    "boxShadow",
}

CUSTOMIZER_DEFAULT_THEME = {
    "primary": "#C9954D",
    "secondary": "#75471F",
    "accent": "#E3C286",
    "bg": "#090706",
    "text": "#F7F0E7",
}


def owner_dashboard_context(
    *,
    product_model,
    user_model,
    order_model,
    review_model,
    wishlist_model,
):
    return {
        "total_products": product_model.objects.count(),
        "total_users": user_model.objects.count(),
        "total_orders": order_model.objects.count(),
        "total_revenue": (
            order_model.objects
            .filter(is_paid=True)
            .aggregate(total=Sum("total"))["total"]
            or 0
        ),
        "pending_orders": order_model.objects.filter(
            status="pending"
        ).count(),
        "total_reviews": review_model.objects.count(),
        "total_wishlist": wishlist_model.objects.count(),
        "best_products": (
            product_model.objects
            .filter(is_active=True)
            .order_by("-sales_count")[:5]
        ),
        "recent_users": (
            user_model.objects
            .all()
            .order_by("-date_joined")[:5]
        ),
        "recent_orders": (
            order_model.objects
            .all()
            .order_by("-created_at")[:5]
        ),
    }


def apply_site_settings(site, post, files):
    fields = (
        "site_name",
        "site_title",
        "site_description",
        "primary_color",
        "secondary_color",
        "accent_color",
        "background_color",
        "text_color",
        "footer_text",
        "footer_bg_color",
        "phone",
        "email",
        "address",
        "instagram",
        "telegram",
        "whatsapp",
        "youtube",
    )

    for field in fields:
        setattr(
            site,
            field,
            post.get(
                field,
                getattr(site, field),
            ),
        )

    file_fields = (
        "logo",
        "favicon",
        "default_product_image",
        "default_avatar",
        "background_image",
    )

    for field in file_fields:
        upload = files.get(field)
        if upload:
            setattr(site, field, upload)

    site.save()
    return site


def reset_site_settings(site):
    site.delete()


def toggle_number_format(site):
    site.number_format = (
        "english"
        if site.number_format == "persian"
        else "persian"
    )
    site.save(
        update_fields=[
            "number_format",
            "updated_at",
        ]
    )
    return site


def set_number_format(site, value):
    if value not in {"persian", "english"}:
        raise ValidationError(
            "invalid number format"
        )

    site.number_format = value
    site.save(
        update_fields=[
            "number_format",
            "updated_at",
        ]
    )
    return site


def customizer_number(
    value,
    minimum,
    maximum,
    default=0,
):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(
        minimum,
        min(maximum, number),
    )


def customizer_url(value, *, image=False):
    value = str(value or "").strip()[:1000]

    if not value:
        return ""

    allowed = (
        "/",
        "https://",
        "http://",
    )

    if not image:
        allowed += (
            "#",
            "mailto:",
            "tel:",
        )

    return (
        value
        if value.startswith(allowed)
        else ""
    )


def clean_customizer_styles(styles):
    if not isinstance(styles, dict):
        return {}

    cleaned = {}

    for key, raw_value in styles.items():
        if key not in _CUSTOMIZER_STYLES:
            continue

        value = str(
            raw_value or ""
        ).strip()[:160]

        if not value:
            continue

        if key in {
            "color",
            "backgroundColor",
        }:
            if (
                _CUSTOMIZER_COLORS.fullmatch(
                    value
                )
                or value == "transparent"
            ):
                cleaned[key] = value

        elif key in {
            "fontSize",
            "lineHeight",
            "letterSpacing",
            "borderRadius",
        }:
            if _CUSTOMIZER_LENGTH.fullmatch(
                value
            ):
                cleaned[key] = value

        elif (
            key == "fontWeight"
            and value in {
                "300",
                "400",
                "500",
                "600",
                "700",
                "800",
                "900",
            }
        ):
            cleaned[key] = value

        elif (
            key == "textAlign"
            and value in {
                "right",
                "center",
                "left",
                "justify",
            }
        ):
            cleaned[key] = value

        elif (
            key == "objectFit"
            and value in {
                "cover",
                "contain",
                "fill",
                "none",
            }
        ):
            cleaned[key] = value

        elif key == "opacity":
            cleaned[key] = str(
                customizer_number(
                    value,
                    0,
                    1,
                    1,
                )
            )

        elif (
            key in {"padding", "margin"}
            and _CUSTOMIZER_LENGTH.fullmatch(
                value
            )
        ):
            cleaned[key] = value

        elif (
            key == "fontFamily"
            and value in {
                "Vazirmatn",
                "Tahoma",
                "Arial",
                "serif",
            }
        ):
            cleaned[key] = value

        elif (
            key == "boxShadow"
            and len(value) <= 120
        ):
            cleaned[key] = value

    return cleaned


def clean_customizer_rule(rule):
    if not isinstance(rule, dict):
        return None

    rule_id = str(
        rule.get("id") or ""
    ).strip()

    if not _CUSTOMIZER_IDS.fullmatch(
        rule_id
    ):
        return None

    cleaned = {
        "id": rule_id,
        "name": str(
            rule.get("name")
            or rule_id
        ).strip()[:120],
        "created": bool(
            rule.get("created")
        ),
        "kind": (
            rule.get("kind")
            if rule.get("kind")
            in {"text", "image", "box"}
            else "text"
        ),
        "text": str(
            rule.get("text") or ""
        )[:5000],
        "src": customizer_url(
            rule.get("src"),
            image=True,
        ),
        "href": customizer_url(
            rule.get("href")
        ),
        "hidden": bool(
            rule.get("hidden")
        ),
        "styles": clean_customizer_styles(
            rule.get("styles")
        ),
    }

    parent = str(
        rule.get("parent")
        or "main-content"
    ).strip()

    cleaned["parent"] = (
        parent
        if _CUSTOMIZER_IDS.fullmatch(
            parent
        )
        else "main-content"
    )

    responsive = rule.get("responsive")
    if not isinstance(responsive, dict):
        responsive = {}

    legacy = (
        rule.get("position")
        if isinstance(
            rule.get("position"),
            dict,
        )
        else {}
    )

    cleaned["responsive"] = {}

    for breakpoint in (
        "desktop",
        "tablet",
        "mobile",
    ):
        values = responsive.get(
            breakpoint
        )

        if not isinstance(values, dict):
            values = (
                legacy
                if breakpoint == "desktop"
                else {}
            )

        cleaned["responsive"][
            breakpoint
        ] = {
            "x": customizer_number(
                values.get("x"),
                -3000,
                3000,
            ),
            "y": customizer_number(
                values.get("y"),
                -3000,
                3000,
            ),
            "width": customizer_number(
                values.get("width"),
                0,
                3000,
            ),
            "height": customizer_number(
                values.get("height"),
                0,
                3000,
            ),
            "zIndex": int(
                customizer_number(
                    values.get("zIndex"),
                    -10,
                    999,
                    0,
                )
            ),
        }

    return cleaned


def _normalize_customizer_payload(data):
    if not isinstance(data, dict):
        raise ValueError

    raw_rules = data.get(
        "rules",
        [],
    )

    if (
        not isinstance(raw_rules, list)
        or len(raw_rules) > 300
    ):
        raise ValidationError(
            "invalid rules"
        )

    rules = []
    seen_ids = set()

    for raw_rule in raw_rules:
        rule = clean_customizer_rule(
            raw_rule
        )

        if (
            rule
            and rule["id"]
            not in seen_ids
        ):
            seen_ids.add(
                rule["id"]
            )
            rules.append(rule)

    incoming_theme = data.get(
        "theme",
        {},
    )

    if not isinstance(
        incoming_theme,
        dict,
    ):
        incoming_theme = {}

    theme = {}

    for key, default in (
        CUSTOMIZER_DEFAULT_THEME.items()
    ):
        value = str(
            incoming_theme.get(
                key,
                default,
            )
        ).strip()

        theme[key] = (
            value
            if _CUSTOMIZER_COLORS.fullmatch(
                value
            )
            else default
        )

    return rules, theme


def customizer_payload(site):
    try:
        rules = json.loads(
            site.customizer_rules
            or "[]"
        )
    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        rules = []

    if not isinstance(rules, list):
        rules = []

    theme = {
        "primary": site.primary_color,
        "secondary": site.secondary_color,
        "accent": site.accent_color,
        "bg": site.background_color,
        "text": site.text_color,
    }

    return {
        "rules": rules,
        "theme": theme,
    }


def save_customizer_state(site, data):
    rules, theme = (
        _normalize_customizer_payload(
            data
        )
    )

    site.customizer_rules = json.dumps(
        rules,
        ensure_ascii=False,
    )
    site.customizer_theme = theme
    site.primary_color = theme["primary"]
    site.secondary_color = theme[
        "secondary"
    ]
    site.accent_color = theme["accent"]
    site.background_color = theme["bg"]
    site.text_color = theme["text"]

    site.save(
        update_fields=[
            "customizer_rules",
            "customizer_theme",
            "primary_color",
            "secondary_color",
            "accent_color",
            "background_color",
            "text_color",
            "updated_at",
        ]
    )

    return {
        "rules": rules,
        "theme": theme,
    }


def reset_customizer_state(site):
    theme = (
        CUSTOMIZER_DEFAULT_THEME.copy()
    )

    site.customizer_rules = "[]"
    site.customizer_theme = theme
    site.primary_color = theme["primary"]
    site.secondary_color = theme[
        "secondary"
    ]
    site.accent_color = theme["accent"]
    site.background_color = theme["bg"]
    site.text_color = theme["text"]

    site.save(
        update_fields=[
            "customizer_rules",
            "customizer_theme",
            "primary_color",
            "secondary_color",
            "accent_color",
            "background_color",
            "text_color",
            "updated_at",
        ]
    )

    return {
        "rules": [],
        "theme": theme,
    }


def load_customizer_state(site):
    payload = customizer_payload(site)

    theme = {
        **CUSTOMIZER_DEFAULT_THEME,
        **(
            site.customizer_theme
            or {}
        ),
        **payload["theme"],
    }

    return {
        "rules": payload["rules"],
        "theme": theme,
    }


def save_simple_product(
    *,
    product_model,
    category_model,
    brand_model,
    post,
    prepared_image=None,
):
    product_id = (
        post.get("id") or ""
    ).strip()

    name = (
        post.get("name") or ""
    ).strip()

    if not name or len(name) > 200:
        raise ValidationError(
            "نام محصول معتبر نیست"
        )

    try:
        price = Decimal(
            (
                post.get("price")
                or ""
            ).strip()
        )
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ):
        raise ValidationError(
            "قیمت محصول معتبر نیست"
        )

    if price < 0:
        raise ValidationError(
            "قیمت محصول نمی‌تواند منفی باشد"
        )

    raw_discount = (
        post.get("discount_price")
        or ""
    ).strip()

    discount_price = None

    if raw_discount:
        try:
            discount_price = Decimal(
                raw_discount
            )
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            raise ValidationError(
                "قیمت تخفیف معتبر نیست"
            )

        if (
            discount_price < 0
            or discount_price >= price
        ):
            raise ValidationError(
                "قیمت تخفیف باید کمتر "
                "از قیمت اصلی باشد"
            )

    try:
        stock = int(
            post.get("stock", 0)
        )
    except (
        TypeError,
        ValueError,
    ):
        raise ValidationError(
            "موجودی معتبر نیست"
        )

    if stock < 0:
        raise ValidationError(
            "موجودی نمی‌تواند منفی باشد"
        )

    product = None

    if product_id:
        if not product_id.isdigit():
            raise ValidationError(
                "شناسه محصول معتبر نیست"
            )

        product = (
            product_model.objects
            .filter(
                pk=int(product_id)
            )
            .first()
        )

        if product is None:
            raise ValidationError(
                "محصول پیدا نشد"
            )

        if product.has_variants:
            raise ValidationError(
                "محصول دارای تنوع باید از "
                "ویرایشگر کامل محصول "
                "ویرایش شود"
            )

    category = None
    category_id = (
        post.get("category_id")
        or ""
    ).strip()

    if category_id:
        if not category_id.isdigit():
            raise ValidationError(
                "دسته‌بندی معتبر نیست"
            )

        category = (
            category_model.objects
            .filter(
                pk=int(category_id),
                is_active=True,
            )
            .first()
        )

        if category is None:
            raise ValidationError(
                "دسته‌بندی معتبر نیست"
            )

    brand = None
    brand_id = (
        post.get("brand_id")
        or ""
    ).strip()

    if brand_id:
        if not brand_id.isdigit():
            raise ValidationError(
                "برند معتبر نیست"
            )

        brand = (
            brand_model.objects
            .filter(
                pk=int(brand_id),
                is_active=True,
            )
            .first()
        )

        if brand is None:
            raise ValidationError(
                "برند معتبر نیست"
            )

    if product is None:
        if prepared_image is None:
            raise ValidationError(
                "تصویر اصلی برای محصول "
                "جدید الزامی است"
            )
        product = product_model()

    with transaction.atomic():
        product.name = name
        product.slug = unique_catalog_slug(
            product_model,
            name,
            exclude_pk=product.pk,
        )
        product.category = category
        product.brand = brand
        product.price = price
        product.discount_price = (
            discount_price
        )
        product.stock = stock
        product.description = (
            post.get("description")
            or ""
        ).strip()[:10000]
        product.is_available = (
            post.get("is_available")
            == "on"
            and stock > 0
        )
        product.is_featured = (
            post.get("is_featured")
            == "on"
        )
        product.is_new = (
            post.get("is_new")
            == "on"
        )
        product.is_active = True
        product.has_variants = False

        if prepared_image is not None:
            product.main_image = (
                prepared_image
            )

        product.save()

    return product
