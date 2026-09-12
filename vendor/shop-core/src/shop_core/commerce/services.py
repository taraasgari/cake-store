from __future__ import annotations

import re

from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone


class CommerceError(Exception):
    def __init__(self, code, **context):
        super().__init__(code)
        self.code = code
        self.context = context


def cart_context(cart):
    return {
        "cart": cart,
        "items": cart.items.all(),
        "total_price": cart.total_price,
        "total_discount": cart.total_discount,
        "final_price": cart.final_price,
        "total_items": cart.total_items,
    }


def add_to_cart(
    *,
    cart_model,
    cart_item_model,
    product_model,
    variant_model,
    user,
    product_id,
    quantity,
    variant_id=None,
    color_id=None,
):
    product = get_object_or_404(
        product_model,
        id=product_id,
        is_active=True,
    )

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        quantity = 1

    if quantity < 1:
        raise CommerceError(
            "invalid_quantity",
            product=product,
        )

    cart, _ = cart_model.objects.get_or_create(
        user=user
    )

    variant = None

    if variant_id:
        variant = get_object_or_404(
            variant_model,
            id=variant_id,
            product=product,
            is_active=True,
        )
    elif color_id:
        variant = (
            product.variants
            .filter(
                color_id=color_id,
                is_active=True,
                stock__gt=0,
            )
            .order_by("-is_default", "id")
            .first()
        )
        if variant is None:
            raise CommerceError(
                "color_unavailable",
                product=product,
            )
    elif product.has_variants:
        raise CommerceError(
            "variant_required",
            product=product,
        )

    if variant is not None:
        if not product.is_available:
            raise CommerceError(
                "product_unavailable",
                product=product,
            )
        if variant.stock < quantity:
            raise CommerceError(
                "variant_stock",
                product=product,
                variant=variant,
            )
        price = variant.price or product.price
        max_stock = variant.stock
    else:
        if (
            not product.is_available
            or product.stock < quantity
        ):
            raise CommerceError(
                "product_stock",
                product=product,
            )
        price = product.price
        max_stock = product.stock

    item, created = cart_item_model.objects.get_or_create(
        cart=cart,
        product=product,
        variant=variant,
        defaults={
            "quantity": quantity,
            "price": price,
        },
    )

    if created:
        return {
            "product": product,
            "variant": variant,
            "item": item,
            "result": "created",
        }

    if item.quantity + quantity > max_stock:
        return {
            "product": product,
            "variant": variant,
            "item": item,
            "result": "insufficient",
        }

    item.quantity += quantity
    item.price = price
    item.save()

    return {
        "product": product,
        "variant": variant,
        "item": item,
        "result": "increased",
    }


def remove_cart_item(item):
    name = item.item_name
    item.delete()
    return name


def update_cart_item(item, raw_quantity):
    try:
        quantity = int(raw_quantity)
    except (TypeError, ValueError):
        raise CommerceError("invalid_quantity")

    if quantity <= 0:
        name = item.item_name
        item.delete()
        return {
            "result": "deleted",
            "item_name": name,
        }

    if item.variant_id:
        max_stock = (
            item.variant.stock
            if (
                item.variant.is_active
                and item.product_id
                and item.product.is_active
                and item.product.is_available
            )
            else 0
        )
    elif item.product_id:
        max_stock = (
            item.product.stock
            if (
                item.product.is_active
                and item.product.is_available
            )
            else 0
        )
    else:
        max_stock = 0

    if quantity > max_stock:
        raise CommerceError("insufficient_stock")

    item.quantity = quantity
    item.save(
        update_fields=[
            "quantity",
            "updated_at",
        ]
    )

    return {
        "result": "updated",
        "item_name": item.item_name,
    }


def clear_cart(cart):
    cart.items.all().delete()


def checkout_payload(
    *,
    address,
    postal_code,
    phone,
    payment_method,
    note,
    allowed_payment_methods,
):
    address = (address or "").strip()
    postal_code = (postal_code or "").strip()
    phone = (phone or "").strip()
    payment_method = payment_method or "online"
    note = (note or "").strip()

    translation = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789",
    )

    postal_code = re.sub(
        r"\D+",
        "",
        postal_code.translate(translation),
    )
    phone = re.sub(
        r"\D+",
        "",
        phone.translate(translation),
    )

    if not address or not postal_code or not phone:
        raise CommerceError("required_fields")

    if len(address) < 10 or len(address) > 1500:
        raise CommerceError("invalid_address")

    if not re.fullmatch(r"09\d{9}", phone):
        raise CommerceError("invalid_phone")

    if not re.fullmatch(r"\d{10}", postal_code):
        raise CommerceError("invalid_postal")

    if len(note) > 1500:
        raise CommerceError("note_too_long")

    if payment_method not in allowed_payment_methods:
        raise CommerceError("invalid_payment")

    if payment_method == "online":
        raise CommerceError("online_disabled")

    return {
        "address": address,
        "postal_code": postal_code,
        "phone": phone,
        "payment_method": payment_method,
        "note": note,
    }


def place_order(
    *,
    cart_model,
    cart_item_model,
    order_model,
    order_item_model,
    product_model,
    variant_model,
    user,
    cart,
    payload,
):
    with transaction.atomic():
        locked_cart = (
            cart_model.objects
            .select_for_update()
            .get(
                pk=cart.pk,
                user=user,
            )
        )

        cart_items = list(
            cart_item_model.objects
            .select_for_update()
            .filter(cart=locked_cart)
            .select_related(
                "product",
                "variant",
                "variant__color",
            )
        )

        if not cart_items:
            raise CommerceError("empty_cart")

        locked_products = {}
        lines = []

        for item in cart_items:
            if (
                not item.product_id
                or item.quantity < 1
            ):
                raise CommerceError("invalid_item")

            product = locked_products.get(
                item.product_id
            )

            if product is None:
                product = (
                    product_model.objects
                    .select_for_update()
                    .get(pk=item.product_id)
                )
                locked_products[
                    item.product_id
                ] = product

            if not product.is_active:
                raise CommerceError(
                    "product_inactive",
                    product_name=product.name,
                )
            if not product.is_available:
                raise CommerceError(
                    "product_unavailable",
                    product_name=product.name,
                )

            variant = None

            if item.variant_id:
                variant = (
                    variant_model.objects
                    .select_for_update()
                    .select_related("color")
                    .filter(
                        pk=item.variant_id,
                        product_id=product.id,
                        is_active=True,
                    )
                    .first()
                )

                if variant is None:
                    raise CommerceError(
                        "variant_missing",
                        product_name=product.name,
                    )

                if variant.stock < item.quantity:
                    raise CommerceError(
                        "variant_stock",
                        variant_name=str(variant),
                    )

                base_unit_price = (
                    variant.price
                    or product.price
                )
                final_unit_price = (
                    variant.final_price
                )
            else:
                if product.has_variants:
                    raise CommerceError(
                        "variant_required",
                        product_name=product.name,
                    )

                if (
                    not product.is_available
                    or product.stock < item.quantity
                ):
                    raise CommerceError(
                        "product_stock",
                        product_name=product.name,
                    )

                base_unit_price = product.price
                final_unit_price = (
                    product.final_price
                )

            line_subtotal = (
                base_unit_price
                * item.quantity
            )
            line_total = (
                final_unit_price
                * item.quantity
            )
            line_discount = (
                line_subtotal
                - line_total
            )

            if line_discount < 0:
                line_discount = 0

            lines.append({
                "item": item,
                "product": product,
                "variant": variant,
                "final_unit_price": (
                    final_unit_price
                ),
                "subtotal": line_subtotal,
                "discount": line_discount,
                "total": line_total,
            })

        subtotal = sum(
            line["subtotal"]
            for line in lines
        )
        discount = sum(
            line["discount"]
            for line in lines
        )
        total = sum(
            line["total"]
            for line in lines
        )

        order_kwargs = {
            "user": user,
            "subtotal": subtotal,
            "discount": discount,
            "shipping_cost": 0,
            "total": total,
            **payload,
        }
        order_fields = {field.name for field in order_model._meta.get_fields()}
        if "customer_name" in order_fields:
            order_kwargs["customer_name"] = (
                user.get_full_name().strip() or user.username
            )
        if "customer_email" in order_fields:
            order_kwargs["customer_email"] = user.email or ""

        order = order_model.objects.create(**order_kwargs)

        for line in lines:
            item = line["item"]
            product = line["product"]
            variant = line["variant"]

            order_item_model.objects.create(
                order=order,
                product=product,
                variant=variant,
                product_name=(
                    str(variant)
                    if variant
                    else product.name
                ),
                price=line["final_unit_price"],
                quantity=item.quantity,
                total=line["total"],
                variant_info={
                    "color": (
                        variant.color.name
                        if (
                            variant
                            and variant.color
                        )
                        else None
                    ),
                    "color_code": (
                        variant.color_code
                        if variant
                        else None
                    ),
                    "volume": (
                        variant.volume_ml
                        if variant
                        else None
                    ),
                    "size": (
                        variant.size
                        if variant
                        else None
                    ),
                },
            )

            if variant:
                variant.stock -= item.quantity
                variant.save(
                    update_fields=[
                        "stock",
                        "updated_at",
                    ]
                )
            else:
                product.stock -= item.quantity
                product.is_available = (
                    product.stock > 0
                )
                product.save(
                    update_fields=[
                        "stock",
                        "is_available",
                        "updated_at",
                    ]
                )

            if order.is_paid or order.payment_method == "cash":
                product_model.objects.filter(
                    pk=product.pk
                ).update(
                    sales_count=(
                        F("sales_count")
                        + item.quantity
                    )
                )

        locked_cart.items.all().delete()

    return order


def get_order_for_user(
    order_model,
    *,
    order_number,
    user,
):
    return get_object_or_404(
        order_model,
        order_number=order_number,
        user=user,
    )


def get_order_detail(
    order_model,
    *,
    order_number,
    user,
):
    order = get_object_or_404(
        order_model.objects.prefetch_related(
            "items",
            "action_requests",
            "support_tickets",
        ),
        order_number=order_number,
        user=user,
    )

    open_statuses = [
        "pending",
        "approved",
        "received",
        "refund_pending",
    ]

    cancel_request = (
        order.action_requests
        .filter(
            kind="cancel",
            status__in=open_statuses,
        )
        .order_by("-created_at")
        .first()
    )

    return_request = (
        order.action_requests
        .filter(
            kind="return",
            status__in=open_statuses,
        )
        .order_by("-created_at")
        .first()
    )

    return order, cancel_request, return_request


def user_orders_data(
    order_model,
    *,
    user,
    raw_code,
):
    translation = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789",
    )

    order_code = (
        (raw_code or "")
        .strip()
        .translate(translation)
        .replace("#", "")
    )

    order_code = re.sub(
        r"\s+",
        "",
        order_code,
    )

    orders = (
        order_model.objects
        .filter(user=user)
        .prefetch_related(
            "items",
            "action_requests",
        )
        .order_by("-created_at")
    )

    searched = bool(order_code)
    tracked_order = None

    if searched:
        tracked_order = (
            orders
            .filter(
                order_number__iexact=order_code
            )
            .first()
        )

    status_flow = [
        "pending",
        "paid",
        "processing",
        "shipped",
        "delivered",
    ]

    tracked_status_index = -1

    if (
        tracked_order
        and tracked_order.status
        in status_flow
    ):
        tracked_status_index = (
            status_flow.index(
                tracked_order.status
            )
        )

    return {
        "orders": orders,
        "tracked_order": tracked_order,
        "order_code": order_code,
        "searched": searched,
        "tracked_status_index": (
            tracked_status_index
        ),
    }


def wishlist_items(
    wishlist_model,
    user,
):
    return wishlist_model.objects.filter(
        user=user,
        product__is_active=True,
    ).select_related("product")


def add_to_wishlist(
    wishlist_model,
    *,
    user,
    product,
):
    _, created = (
        wishlist_model.objects
        .get_or_create(
            user=user,
            product=product,
        )
    )
    return created


def remove_from_wishlist(
    wishlist_model,
    *,
    user,
    product,
):
    wishlist_model.objects.filter(
        user=user,
        product=product,
    ).delete()


def admin_order_queryset(order_model):
    return (
        order_model.objects
        .all()
        .order_by("-created_at")
    )


def transition_order(
    order_model,
    *,
    order_id,
    requested,
):
    with transaction.atomic():
        order = (
            order_model.objects
            .select_for_update()
            .get(pk=order_id)
        )

        if requested == order.status:
            return order, "unchanged"

        transitions = {
            "pending": (
                {"processing"}
                if order.payment_method == "cash"
                else {"paid"}
            ),
            "paid": {"processing"},
            "processing": {"shipped"},
            "shipped": {"delivered"},
            "delivered": set(),
            "cancelled": set(),
            "refunded": set(),
        }

        if requested not in transitions.get(
            order.status,
            set(),
        ):
            raise CommerceError(
                "invalid_transition"
            )

        now = timezone.now()
        order.status = requested

        update_fields = [
            "status",
            "updated_at",
        ]

        if requested == "paid":
            order.is_paid = True
            order.paid_at = now
            update_fields.extend([
                "is_paid",
                "paid_at",
            ])

        if requested == "delivered":
            order.delivered_at = now
            update_fields.append(
                "delivered_at"
            )

            if (
                order.payment_method == "cash"
                and not order.is_paid
            ):
                order.is_paid = True
                order.paid_at = now
                update_fields.extend([
                    "is_paid",
                    "paid_at",
                ])

        order.save(
            update_fields=list(
                dict.fromkeys(
                    update_fields
                )
            )
        )

    return order, "changed"


def warehouse_products_data(
    product_model,
    *,
    effective_stock,
    search=None,
    stock_status=None,
):
    queryset = (
        product_model.objects
        .all()
        .prefetch_related("variants")
    )

    search = (search or "").strip()
    if search:
        queryset = queryset.filter(
            name__icontains=search
        )

    products = list(queryset)

    for product in products:
        product.display_stock = (
            effective_stock(product)
        )

    if stock_status == "in_stock":
        products = [
            item
            for item in products
            if item.display_stock > 0
        ]
    elif stock_status == "out_of_stock":
        products = [
            item
            for item in products
            if item.display_stock == 0
        ]
    elif stock_status == "low_stock":
        products = [
            item
            for item in products
            if 0 < item.display_stock <= 5
        ]

    products.sort(
        key=lambda item: item.display_stock
    )
    return products


def update_product_stock(
    product,
    raw_stock,
):
    if product.has_variants:
        raise CommerceError(
            "variant_stock_managed_separately"
        )

    try:
        new_stock = int(raw_stock)
    except (TypeError, ValueError):
        raise CommerceError(
            "invalid_stock"
        )

    if new_stock < 0:
        raise CommerceError(
            "invalid_stock"
        )

    product.stock = new_stock
    product.is_available = (
        new_stock > 0
    )
    product.save(
        update_fields=[
            "stock",
            "is_available",
            "updated_at",
        ]
    )

    return new_stock
