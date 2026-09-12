"""Reusable product add/edit services.

The client project keeps permissions, presentation, redirects and concrete
model ownership. These services operate on dependency-injected models and the
request payload so stores can reuse the same product-write rules.
"""

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404
from .slugs import build_unique_product_slug


def parse_nonnegative_decimal(value, label, required=False):
    value = str(value or "").strip()

    if not value:
        if required:
            raise ValidationError(f"{label} الزامی است")
        return None

    try:
        number = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(f"{label} معتبر نیست")

    if number < 0:
        raise ValidationError(f"{label} نمی‌تواند منفی باشد")

    return number


def parse_nonnegative_int(value, label, default=0):
    value = str(value if value is not None else "").strip()

    if value == "":
        return default

    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{label} معتبر نیست")

    if number < 0:
        raise ValidationError(f"{label} نمی‌تواند منفی باشد")

    return number


def admin_product_form_context(
    *,
    category_model,
    brand_model,
    product_type_model,
    tag_model,
    color_model,
    form_data=None,
    product=None,
):
    context = {
        "categories": category_model.objects.filter(
            is_active=True
        ).order_by("name"),
        "brands": brand_model.objects.filter(
            is_active=True
        ).order_by("name"),
        "product_types": product_type_model.objects.filter(
            is_active=True
        ).order_by("name"),
        "tags": tag_model.objects.all().order_by("name"),
        "colors": color_model.objects.filter(
            is_active=True
        ).order_by("name"),
        "form_data": form_data,
    }

    if product is not None:
        context["product"] = product

    return context


def _add_money_value(raw_value, label, required=False):
    raw_value = (raw_value or "").replace(",", "").strip()

    if not raw_value:
        if required:
            raise ValidationError(f"{label} الزامی است.")
        return None

    try:
        value = Decimal(raw_value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError(f"{label} معتبر نیست.") from exc

    if value < 0:
        raise ValidationError(f"{label} نمی‌تواند منفی باشد.")

    return value


def _add_integer_value(raw_value, label, default=None):
    raw_value = str(raw_value or "").strip()

    if not raw_value:
        return default

    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{label} باید عدد صحیح باشد.") from exc

    if value < 0:
        raise ValidationError(f"{label} نمی‌تواند منفی باشد.")

    return value


def _list_item(items, index):
    return items[index].strip() if index < len(items) else ""


def create_product_from_request(
    request,
    *,
    product_model,
    product_image_model,
    product_variant_model,
    tag_model,
    color_model,
    prepare_image,
):
    name = (request.POST.get("name") or "").strip()
    if not name:
        raise ValidationError("نام محصول الزامی است.")

    price = _add_money_value(
        request.POST.get("price"),
        "قیمت محصول",
        required=True,
    )
    discount_price = _add_money_value(
        request.POST.get("discount_price"),
        "قیمت تخفیف‌خورده",
    )
    if discount_price is not None and discount_price >= price:
        raise ValidationError(
            "قیمت تخفیف‌خورده باید کمتر از قیمت اصلی باشد."
        )

    stock = _add_integer_value(
        request.POST.get("stock"),
        "موجودی",
        default=0,
    )

    product_images = request.FILES.getlist("product_images")
    if not product_images:
        raise ValidationError("حداقل یک تصویر برای محصول انتخاب کنید.")
    if len(product_images) > 8:
        raise ValidationError("حداکثر ۸ تصویر برای هر محصول مجاز است.")

    main_image_index = _add_integer_value(
        request.POST.get("main_image_index"),
        "شماره تصویر اصلی",
        default=0,
    )
    if (
        main_image_index is None
        or not 0 <= main_image_index < len(product_images)
    ):
        raise ValidationError("تصویر اصلی انتخاب‌شده معتبر نیست.")

    prepared_images = [
        prepare_image(image, name_prefix=f"product-{index + 1}")
        for index, image in enumerate(product_images)
    ]

    has_variants = request.POST.get("has_variants") == "on"
    variant_payloads = []

    if has_variants:
        variant_colors = request.POST.getlist("variant_colors")
        variant_volumes = request.POST.getlist("variant_volumes")
        variant_sizes = request.POST.getlist("variant_sizes")
        variant_prices = request.POST.getlist("variant_prices")
        variant_discount_prices = request.POST.getlist(
            "variant_discount_prices"
        )
        variant_stocks = request.POST.getlist("variant_stocks")

        variant_count = max(
            len(variant_colors),
            len(variant_volumes),
            len(variant_sizes),
            len(variant_prices),
            len(variant_discount_prices),
            len(variant_stocks),
            0,
        )

        default_variant_index = _add_integer_value(
            request.POST.get("variant_default"),
            "تنوع پیش‌فرض",
            default=0,
        )
        used_combinations = set()

        for index in range(variant_count):
            color_id = _list_item(variant_colors, index)
            volume = _add_integer_value(
                _list_item(variant_volumes, index),
                f"حجم تنوع {index + 1}",
                default=None,
            )
            size = _list_item(variant_sizes, index) or None
            variant_price = _add_money_value(
                _list_item(variant_prices, index),
                f"قیمت تنوع {index + 1}",
            )
            variant_discount = _add_money_value(
                _list_item(variant_discount_prices, index),
                f"قیمت تخفیف تنوع {index + 1}",
            )
            variant_stock = _add_integer_value(
                _list_item(variant_stocks, index),
                f"موجودی تنوع {index + 1}",
                default=0,
            )

            if not color_id and volume is None and not size:
                continue

            if color_id and not color_model.objects.filter(
                id=color_id,
                is_active=True,
            ).exists():
                raise ValidationError(
                    f"رنگ تنوع {index + 1} معتبر نیست."
                )

            effective_price = (
                variant_price
                if variant_price is not None
                else price
            )
            if (
                variant_discount is not None
                and variant_discount >= effective_price
            ):
                raise ValidationError(
                    f"قیمت تخفیف تنوع {index + 1} باید کمتر از قیمت آن باشد."
                )

            combination = (
                color_id or None,
                volume,
                (size or "").lower(),
            )
            if combination in used_combinations:
                raise ValidationError(
                    f"تنوع شماره {index + 1} تکراری است."
                )
            used_combinations.add(combination)

            variant_image = request.FILES.get(
                f"variant_image_{index}"
            )
            prepared_variant_image = None
            if variant_image:
                prepared_variant_image = prepare_image(
                    variant_image,
                    min_width=300,
                    min_height=300,
                    max_dimension=1400,
                    name_prefix=f"variant-{index + 1}",
                )

            variant_payloads.append({
                "source_index": index,
                "color_id": color_id or None,
                "volume_ml": volume,
                "size": size,
                "price": variant_price,
                "discount_price": variant_discount,
                "stock": variant_stock,
                "image": prepared_variant_image,
                "is_default": index == default_variant_index,
            })

        if not variant_payloads:
            raise ValidationError(
                "برای محصول دارای تنوع، حداقل یک تنوع کامل ثبت کنید."
            )
        if not any(item["is_default"] for item in variant_payloads):
            variant_payloads[0]["is_default"] = True

    unique_slug = build_unique_product_slug(
        product_model, product_model(), request.POST.get("slug"), name
    )

    with transaction.atomic():
        product = product_model.objects.create(
            name=name,
            slug=unique_slug,
            category_id=request.POST.get("category") or None,
            brand_id=request.POST.get("brand") or None,
            product_type_id=request.POST.get("product_type") or None,
            price=price,
            discount_price=discount_price,
            stock=0 if has_variants else stock,
            description=(request.POST.get("description") or "").strip(),
            short_description=(
                request.POST.get("short_description") or ""
            ).strip(),
            main_image=prepared_images[main_image_index],
            has_variants=has_variants,
            is_featured=request.POST.get("is_featured") == "on",
            is_new=request.POST.get("is_new") == "on",
            is_best_seller=request.POST.get("is_best_seller") == "on",
            is_active=request.POST.get("is_active") == "on",
        )

        valid_tag_ids = tag_model.objects.filter(
            id__in=request.POST.getlist("tags")
        ).values_list("id", flat=True)
        product.tags.set(valid_tag_ids)

        gallery_order = 0
        for index, image in enumerate(prepared_images):
            if index == main_image_index:
                continue
            product_image_model.objects.create(
                product=product,
                image=image,
                alt_text=name,
                order=gallery_order,
                is_main=False,
            )
            gallery_order += 1

        for payload in variant_payloads:
            color = None
            if payload["color_id"]:
                color = color_model.objects.get(id=payload["color_id"])
            product_variant_model.objects.create(
                product=product,
                color=color,
                color_code=color.code if color else None,
                volume_ml=payload["volume_ml"],
                size=payload["size"],
                price=payload["price"],
                discount_price=payload["discount_price"],
                stock=payload["stock"],
                image=payload["image"],
                is_default=payload["is_default"],
                is_active=True,
            )

    return product


def update_product_from_request(
    request,
    product,
    *,
    product_model,
    product_image_model,
    product_variant_model,
    category_model,
    brand_model,
    product_type_model,
    tag_model,
    color_model,
    prepare_image,
    slug_builder,
):
    name = (request.POST.get("name") or "").strip()
    if not name:
        raise ValidationError("نام محصول الزامی است")

    price = parse_nonnegative_decimal(
        request.POST.get("price"),
        "قیمت اصلی",
        required=True,
    )
    discount = parse_nonnegative_decimal(
        request.POST.get("discount_price"),
        "قیمت تخفیف",
    )
    if discount is not None and discount >= price:
        raise ValidationError(
            "قیمت تخفیف باید کمتر از قیمت اصلی باشد"
        )

    stock = parse_nonnegative_int(
        request.POST.get("stock"),
        "موجودی",
    )
    has_variants = "has_variants" in request.POST

    category = None
    category_id = request.POST.get("category")
    if category_id:
        category = get_object_or_404(
            category_model,
            pk=category_id,
            is_active=True,
        )

    brand = None
    brand_id = request.POST.get("brand")
    if brand_id:
        brand = get_object_or_404(
            brand_model,
            pk=brand_id,
            is_active=True,
        )

    product_type = None
    product_type_id = request.POST.get("product_type")
    if product_type_id:
        product_type = get_object_or_404(
            product_type_model,
            pk=product_type_id,
            is_active=True,
        )

    tag_ids = [
        value
        for value in request.POST.getlist("tags")
        if str(value).isdigit()
    ]

    main_upload = (
        request.FILES.get("new_main_image")
        or request.FILES.get("main_image")
    )
    prepared_main = None
    if main_upload:
        prepared_main = prepare_image(
            main_upload,
            min_width=500,
            min_height=500,
            max_dimension=1800,
            name_prefix="product",
        )

    keys = request.POST.getlist("variant_keys")
    ids = request.POST.getlist("variant_ids")
    colors = request.POST.getlist("variant_colors")
    volumes = request.POST.getlist("variant_volumes")
    sizes = request.POST.getlist("variant_sizes")
    prices = request.POST.getlist("variant_prices")
    discounts = request.POST.getlist("variant_discount_prices")
    stocks = request.POST.getlist("variant_stocks")
    default_key = request.POST.get("variant_default")

    payloads = []
    seen = set()

    if has_variants:
        lengths = {
            len(keys),
            len(ids),
            len(colors),
            len(volumes),
            len(sizes),
            len(prices),
            len(discounts),
            len(stocks),
        }

        if len(lengths) != 1 or not keys:
            raise ValidationError("اطلاعات تنوع‌های محصول ناقص است")

        color_map = {
            str(item.pk): item
            for item in color_model.objects.filter(is_active=True)
        }

        for index, key in enumerate(keys):
            key = str(key or "").strip()
            existing_id = str(ids[index] or "").strip()
            color_id = str(colors[index] or "").strip()

            color = None
            if color_id:
                color = color_map.get(color_id)
                if color is None:
                    raise ValidationError(
                        "یکی از رنگ‌های انتخابی معتبر نیست"
                    )

            volume = None
            if str(volumes[index] or "").strip():
                volume = parse_nonnegative_int(
                    volumes[index],
                    "حجم تنوع",
                )

            size = str(sizes[index] or "").strip()[:20] or None
            variant_price = parse_nonnegative_decimal(
                prices[index],
                "قیمت تنوع",
            )
            variant_discount = parse_nonnegative_decimal(
                discounts[index],
                "قیمت تخفیف تنوع",
            )

            effective_price = (
                variant_price
                if variant_price is not None
                else price
            )
            if (
                variant_discount is not None
                and variant_discount >= effective_price
            ):
                raise ValidationError(
                    "قیمت تخفیف هر تنوع باید کمتر از قیمت آن باشد"
                )

            variant_stock = parse_nonnegative_int(
                stocks[index],
                "موجودی تنوع",
            )

            combo = (
                color.pk if color else None,
                volume,
                size or "",
            )
            if combo in seen:
                raise ValidationError("دو تنوع یکسان ثبت شده است")
            seen.add(combo)

            upload = request.FILES.get(f"variant_image_{key}")
            prepared_image = None
            if upload:
                prepared_image = prepare_image(
                    upload,
                    min_width=250,
                    min_height=250,
                    max_dimension=1400,
                    name_prefix="variant",
                )

            payloads.append({
                "key": key,
                "existing_id": existing_id,
                "color": color,
                "volume": volume,
                "size": size,
                "price": variant_price,
                "discount": variant_discount,
                "stock": variant_stock,
                "image": prepared_image,
                "is_default": key == default_key,
            })

        if payloads and not any(
            item["is_default"] for item in payloads
        ):
            payloads[0]["is_default"] = True

    delete_gallery_ids = [
        value
        for value in request.POST.getlist("delete_gallery_ids")
        if str(value).isdigit()
    ]

    gallery_uploads = list(
        request.FILES.getlist("new_gallery_images")
    )

    remaining_gallery = product.images.exclude(
        pk__in=delete_gallery_ids
    ).count()

    if remaining_gallery + len(gallery_uploads) > 8:
        raise ValidationError("حداکثر ۸ تصویر گالری مجاز است")

    prepared_gallery = [
        prepare_image(
            upload,
            min_width=500,
            min_height=500,
            max_dimension=1800,
            name_prefix="gallery",
        )
        for upload in gallery_uploads
    ]

    with transaction.atomic():
        product = (
            product_model.objects
            .select_for_update()
            .get(pk=product.pk)
        )

        product.name = name
        product.slug = slug_builder(
            product,
            request.POST.get("slug"),
            name,
        )
        product.category = category
        product.brand = brand
        product.product_type = product_type
        product.price = price
        product.discount_price = discount
        product.stock = 0 if has_variants else stock
        product.description = (
            request.POST.get("description") or ""
        ).strip()
        product.short_description = (
            request.POST.get("short_description") or ""
        ).strip()[:300]
        product.has_variants = has_variants
        product.is_featured = "is_featured" in request.POST
        product.is_new = "is_new" in request.POST
        product.is_best_seller = "is_best_seller" in request.POST
        product.is_active = "is_active" in request.POST
        product.is_available = True if has_variants else stock > 0

        if prepared_main:
            product.main_image = prepared_main

        product.save()

        product.tags.set(
            tag_model.objects.filter(id__in=tag_ids)
        )

        if delete_gallery_ids:
            product_image_model.objects.filter(
                product=product,
                pk__in=delete_gallery_ids,
            ).delete()

        current_max = (
            product.images.aggregate(maximum=Max("order"))
            .get("maximum")
            or 0
        )

        for image in prepared_gallery:
            current_max += 1
            product_image_model.objects.create(
                product=product,
                image=image,
                order=current_max,
            )

        existing = {
            item.pk: item
            for item in (
                product_variant_model.objects
                .select_for_update()
                .filter(product=product)
            )
        }

        active_ids = set()

        if has_variants:
            for payload in payloads:
                variant = None
                existing_id = payload["existing_id"]

                if existing_id.isdigit():
                    variant = existing.get(int(existing_id))
                    if variant is None:
                        raise ValidationError(
                            "یکی از تنوع‌های ویرایش‌شده متعلق به این محصول نیست"
                        )

                if variant is None:
                    variant = (
                        product_variant_model.objects
                        .filter(
                            product=product,
                            color=payload["color"],
                            volume_ml=payload["volume"],
                            size=payload["size"],
                        )
                        .order_by("id")
                        .first()
                    )

                if variant is None:
                    variant = product_variant_model(product=product)

                variant.color = payload["color"]
                variant.color_code = (
                    payload["color"].code
                    if payload["color"]
                    else None
                )
                variant.volume_ml = payload["volume"]
                variant.size = payload["size"]
                variant.price = payload["price"]
                variant.discount_price = payload["discount"]
                variant.stock = payload["stock"]
                variant.is_default = payload["is_default"]
                variant.is_active = True

                if payload["image"]:
                    variant.image = payload["image"]

                variant.save()
                active_ids.add(variant.pk)

            product_variant_model.objects.filter(
                product=product
            ).exclude(
                pk__in=active_ids
            ).update(
                is_active=False,
                is_default=False,
            )
        else:
            product_variant_model.objects.filter(
                product=product
            ).update(
                is_active=False,
                is_default=False,
            )

    return product
