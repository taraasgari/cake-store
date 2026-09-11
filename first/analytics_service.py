import calendar
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDay, TruncMonth
from django.utils import timezone

from .models import (
    Cart,
    Order,
    OrderItem,
    Product,
    ProductReview,
    User,
    Wishlist,
)


ZERO = Decimal('0')


def _decimal(value):
    return value if isinstance(value, Decimal) else Decimal(str(value or 0))


def _percent(part, whole):
    whole = float(whole or 0)
    return round((float(part or 0) / whole) * 100, 1) if whole else 0


def _change(current, previous):
    current = float(current or 0)
    previous = float(previous or 0)

    if previous:
        return round(((current - previous) / previous) * 100, 1)

    return 100.0 if current > 0 else 0.0


def _aware(day):
    value = datetime.combine(day, time.min)
    return timezone.make_aware(
        value,
        timezone.get_current_timezone(),
    )


def resolve_period(request):
    today = timezone.localdate()
    period = request.GET.get('period', 'month')

    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        month = min(12, max(1, month))
    except (TypeError, ValueError):
        year = today.year
        month = today.month

    custom_from = request.GET.get('date_from')
    custom_to = request.GET.get('date_to')

    if custom_from and custom_to:
        try:
            start_day = date.fromisoformat(custom_from)
            end_day = date.fromisoformat(custom_to)

            if end_day < start_day:
                start_day, end_day = end_day, start_day

            # جلوگیری از گزارش‌های بیش‌ازحد سنگین
            if (end_day - start_day).days > 730:
                end_day = start_day + timedelta(days=730)

            period = 'custom'

        except ValueError:
            custom_from = None
            custom_to = None

    if period != 'custom':
        if period == 'day':
            start_day = today
            end_day = today

        elif period == 'year':
            start_day = date(year, 1, 1)
            end_day = date(year, 12, 31)

        else:
            period = 'month'
            start_day = date(year, month, 1)
            end_day = date(
                year,
                month,
                calendar.monthrange(year, month)[1],
            )

    start = _aware(start_day)
    end = _aware(end_day + timedelta(days=1))

    duration = end - start
    previous_end = start
    previous_start = start - duration

    labels = {
        'day': f'{start_day:%Y/%m/%d}',
        'month': f'{year}/{month:02d}',
        'year': str(year),
        'custom': (
            f'{start_day:%Y/%m/%d} تا '
            f'{end_day:%Y/%m/%d}'
        ),
    }

    return {
        'period': period,
        'year': year,
        'month': month,

        'start': start,
        'end': end,

        'previous_start': previous_start,
        'previous_end': previous_end,

        'start_day': start_day,
        'end_day': end_day,

        'days': max(1, duration.days),
        'label': labels[period],

        'date_from': (
            start_day.isoformat()
            if period == 'custom'
            else ''
        ),
        'date_to': (
            end_day.isoformat()
            if period == 'custom'
            else ''
        ),
    }


def _financials(queryset):
    data = queryset.aggregate(
        revenue=Sum('total'),
        gross=Sum('subtotal'),
        order_discount=Sum('discount'),
        coupon_discount=Sum('coupon_discount'),
        shipping=Sum('shipping_cost'),
        average=Avg('total'),
    )

    data = {
        key: _decimal(value)
        for key, value in data.items()
    }

    data['discounts'] = (
        data['order_discount']
        + data['coupon_discount']
    )

    return data


def _timeline(
    paid_orders,
    start_day,
    end_day,
    days,
):
    use_month = days > 62

    trunc = (
        TruncMonth('created_at')
        if use_month
        else TruncDay('created_at')
    )

    rows = (
        paid_orders
        .annotate(bucket=trunc)
        .values('bucket')
        .annotate(
            revenue=Sum('total'),
            orders=Count('id'),
        )
        .order_by('bucket')
    )

    lookup = {}

    for row in rows:
        bucket = row['bucket']

        if timezone.is_aware(bucket):
            bucket = timezone.localtime(bucket)

        key = (
            (bucket.year, bucket.month)
            if use_month
            else bucket.date()
        )

        lookup[key] = row

    result = []
    cursor = start_day

    while cursor <= end_day:
        key = (
            (cursor.year, cursor.month)
            if use_month
            else cursor
        )

        row = lookup.get(key, {})

        result.append({
            'label': (
                f'{cursor.year}/{cursor.month:02d}'
                if use_month
                else f'{cursor.month:02d}/{cursor.day:02d}'
            ),
            'revenue': float(
                row.get('revenue') or 0
            ),
            'orders': int(
                row.get('orders') or 0
            ),
        })

        if use_month:
            cursor = date(
                cursor.year + (cursor.month == 12),
                1 if cursor.month == 12 else cursor.month + 1,
                1,
            )
        else:
            cursor += timedelta(days=1)

    return result


def build_analytics(request):
    selected = resolve_period(request)

    start = selected['start']
    end = selected['end']

    previous_start = selected['previous_start']
    previous_end = selected['previous_end']

    orders = Order.objects.filter(
        created_at__gte=start,
        created_at__lt=end,
    )

    previous_orders = Order.objects.filter(
        created_at__gte=previous_start,
        created_at__lt=previous_end,
    )

    paid_orders = orders.filter(is_paid=True)
    previous_paid = previous_orders.filter(is_paid=True)

    finance = _financials(paid_orders)
    previous_finance = _financials(previous_paid)

    order_count = orders.count()
    previous_order_count = previous_orders.count()
    paid_count = paid_orders.count()

    sold_items = (
        paid_orders.aggregate(
            total=Sum('items__quantity')
        )['total']
        or 0
    )

    unique_buyers = (
        paid_orders
        .values('user_id')
        .distinct()
        .count()
    )

    # ============================================
    # وضعیت سفارش‌ها
    # ============================================

    status_rows = (
        orders
        .values('status')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    status_map = {
        value: 0
        for value, _ in Order.STATUS_CHOICES
    }

    status_map.update({
        row['status']: row['count']
        for row in status_rows
    })

    status_labels = dict(Order.STATUS_CHOICES)

    order_status = [
        {
            'key': key,
            'label': status_labels[key],
            'count': value,
            'percent': _percent(
                value,
                order_count,
            ),
        }
        for key, value in status_map.items()
    ]

    # ============================================
    # روش‌های پرداخت
    # ============================================

    payment_labels = dict(Order.PAYMENT_METHODS)

    payment_rows = (
        paid_orders
        .values('payment_method')
        .annotate(
            count=Count('id'),
            revenue=Sum('total'),
        )
        .order_by('-count')
    )

    payment_methods = [
        {
            'key': row['payment_method'],
            'label': payment_labels.get(
                row['payment_method'],
                row['payment_method'],
            ),
            'count': row['count'],
            'revenue': float(
                row['revenue'] or 0
            ),
            'percent': _percent(
                row['count'],
                paid_count,
            ),
        }
        for row in payment_rows
    ]

    # ============================================
    # محصولات پرفروش و مقایسه دوره قبل
    # ============================================

    previous_product_rows = (
        OrderItem.objects
        .filter(order__in=previous_paid)
        .values(
            'product_id',
            'product_name',
        )
        .annotate(
            quantity=Sum('quantity')
        )
    )

    previous_product_sales = {
        (
            row['product_id'],
            row['product_name'],
        ): row['quantity'] or 0

        for row in previous_product_rows
    }

    product_rows = (
        OrderItem.objects
        .filter(order__in=paid_orders)
        .values(
            'product_id',
            'product_name',
        )
        .annotate(
            quantity=Sum('quantity'),
            revenue=Sum('total'),
            orders=Count(
                'order_id',
                distinct=True,
            ),
        )
        .order_by(
            '-quantity',
            '-revenue',
        )[:15]
    )

    top_products = []

    for row in product_rows:
        previous_quantity = (
            previous_product_sales.get(
                (
                    row['product_id'],
                    row['product_name'],
                ),
                0,
            )
        )

        product = None

        if row['product_id']:
            product = (
                Product.objects
                .filter(pk=row['product_id'])
                .only('main_image')
                .first()
            )

        top_products.append({
            'id': row['product_id'],
            'name': row['product_name'],

            'quantity': (
                row['quantity'] or 0
            ),

            'revenue': float(
                row['revenue'] or 0
            ),

            'orders': row['orders'],

            'previous_quantity': (
                previous_quantity
            ),

            'change': _change(
                row['quantity'],
                previous_quantity,
            ),

            'image_url': (
                product.main_image.url
                if (
                    product
                    and product.main_image
                )
                else None
            ),
        })

    # ============================================
    # دسته‌بندی‌های پرفروش
    # ============================================

    category_rows = (
        OrderItem.objects
        .filter(order__in=paid_orders)
        .values(
            'product__category__name'
        )
        .annotate(
            quantity=Sum('quantity'),
            revenue=Sum('total'),
            orders=Count(
                'order_id',
                distinct=True,
            ),
        )
        .order_by('-revenue')[:12]
    )

    category_sales = [
        {
            'name': (
                row['product__category__name']
                or 'بدون دسته‌بندی'
            ),

            'quantity': (
                row['quantity'] or 0
            ),

            'revenue': float(
                row['revenue'] or 0
            ),

            'orders': row['orders'],

            'share': _percent(
                row['revenue'],
                finance['revenue'],
            ),
        }
        for row in category_rows
    ]

    # ============================================
    # مشتریان برتر
    # ============================================

    top_customer_rows = (
        paid_orders
        .values(
            'user_id',
            'user__username',
            'user__phone',
        )
        .annotate(
            orders=Count('id'),
            spent=Sum('total'),
            average=Avg('total'),
        )
        .order_by('-spent')[:15]
    )

    top_customers = [
        {
            'id': row['user_id'],
            'username': row['user__username'],
            'phone': row['user__phone'],

            'orders': row['orders'],

            'spent': float(
                row['spent'] or 0
            ),

            'average': float(
                row['average'] or 0
            ),
        }
        for row in top_customer_rows
    ]

    # ============================================
    # آمار مشتریان
    # ============================================

    customers = User.objects.filter(role='user')
    total_customers = customers.count()

    new_customers = customers.filter(
        date_joined__gte=start,
        date_joined__lt=end,
    ).count()

    previous_new_customers = (
        customers.filter(
            date_joined__gte=previous_start,
            date_joined__lt=previous_end,
        ).count()
    )

    buying_customers = (
        customers
        .filter(orders__in=paid_orders)
        .distinct()
        .count()
    )

    returning_customers = (
        customers
        .annotate(
            paid_order_count=Count(
                'orders',
                filter=Q(
                    orders__is_paid=True
                ),
            )
        )
        .filter(
            paid_order_count__gt=1,
            orders__in=paid_orders,
        )
        .distinct()
        .count()
    )

    all_time_buyers = (
        customers
        .filter(orders__is_paid=True)
        .distinct()
        .count()
    )

    no_purchase_customers = max(
        0,
        total_customers - all_time_buyers,
    )

    # ============================================
    # کوپن‌ها
    # ============================================

    coupon_rows = (
        paid_orders
        .filter(coupon__isnull=False)
        .values('coupon__code')
        .annotate(
            uses=Count('id'),
            revenue=Sum('total'),
            discount=Sum(
                'coupon_discount'
            ),
        )
        .order_by('-uses')[:10]
    )

    coupons = [
        {
            'code': row['coupon__code'],
            'uses': row['uses'],

            'revenue': float(
                row['revenue'] or 0
            ),

            'discount': float(
                row['discount'] or 0
            ),
        }
        for row in coupon_rows
    ]

    # ============================================
    # نظرات و امتیازها
    # ============================================

    review_queryset = (
        ProductReview.objects.filter(
            created_at__gte=start,
            created_at__lt=end,
        )
    )

    review_total = review_queryset.count()

    verified_reviews = (
        review_queryset.filter(
            is_verified=True
        )
    )

    review_average = (
        verified_reviews.aggregate(
            value=Avg('rating')
        )['value']
        or 0
    )

    rating_map = {
        row['rating']: row['count']

        for row in (
            verified_reviews
            .values('rating')
            .annotate(count=Count('id'))
        )
    }

    rating_distribution = [
        {
            'rating': rating,
            'count': rating_map.get(
                rating,
                0,
            ),
        }
        for rating in range(1, 6)
    ]

    # ============================================
    # علاقه‌مندی‌ها
    # ============================================

    period_wishlist = Wishlist.objects.filter(
        created_at__gte=start,
        created_at__lt=end,
    )

    wishlist_count = period_wishlist.count()

    wishlist_rows = (
        period_wishlist
        .values(
            'product_id',
            'product__name',
        )
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    popular_wishlist = [
        {
            'id': row['product_id'],
            'name': row['product__name'],
            'count': row['count'],
        }
        for row in wishlist_rows
    ]

    # ============================================
    # وضعیت انبار
    # ============================================

    sold_product_ids = set(
        OrderItem.objects.filter(
            order__in=paid_orders,
            product_id__isnull=False,
        ).values_list(
            'product_id',
            flat=True,
        )
    )

    inventory_rows = []
    inventory_value = ZERO

    active_products = (
        Product.objects
        .filter(is_active=True)
        .prefetch_related('variants')
    )

    out_of_stock = 0
    low_stock = 0
    inventory_units = 0

    for product in active_products:
        if product.has_variants:
            active_variants = [
                variant
                for variant in product.variants.all()
                if variant.is_active
            ]

            stock = sum(
                variant.stock
                for variant in active_variants
            )

            value = sum(
                (
                    _decimal(
                        variant.final_price
                    ) * variant.stock

                    for variant in active_variants
                ),
                ZERO,
            )

        else:
            stock = product.stock

            value = (
                _decimal(product.final_price)
                * stock
            )

        inventory_units += stock
        inventory_value += value

        if stock <= 0:
            out_of_stock += 1

        elif stock <= 5:
            low_stock += 1

        if (
            stock <= 5
            or (
                stock > 0
                and product.id
                not in sold_product_ids
            )
        ):
            inventory_rows.append({
                'id': product.id,
                'name': product.name,
                'stock': stock,
                'value': float(value),

                'status': (
                    'out'
                    if stock <= 0

                    else 'low'
                    if stock <= 5

                    else 'stagnant'
                ),
            })

    inventory_rows.sort(
        key=lambda item: (
            0
            if item['status'] == 'out'

            else 1
            if item['status'] == 'low'

            else 2,

            item['stock'],
        )
    )

    inventory_rows = inventory_rows[:20]

    stagnant_products = sum(
        1
        for row in inventory_rows
        if row['status'] == 'stagnant'
    )

    # ============================================
    # سبد خرید رهاشده
    # ============================================

    abandoned_carts = (
        Cart.objects
        .filter(
            items__isnull=False,
            updated_at__lt=(
                timezone.now()
                - timedelta(hours=24)
            ),
        )
        .distinct()
        .count()
    )

    # ============================================
    # روند زمانی و پیش‌بینی
    # ============================================

    timeline = _timeline(
        paid_orders,
        selected['start_day'],
        selected['end_day'],
        selected['days'],
    )

    peak = max(
        timeline,
        key=lambda row: row['revenue'],
        default={
            'label': '-',
            'revenue': 0,
            'orders': 0,
        },
    )

    daily_average = (
        finance['revenue']
        / selected['days']
        if selected['days']
        else ZERO
    )

    forecast_30_days = (
        daily_average * 30
    )

    # ============================================
    # هشدارهای مدیریتی
    # ============================================

    alerts = []

    if out_of_stock:
        alerts.append({
            'level': 'danger',
            'icon': 'fa-box-open',
            'title': 'محصول ناموجود',
            'message': (
                f'{out_of_stock} محصول فعال '
                f'موجودی صفر دارد.'
            ),
        })

    if low_stock:
        alerts.append({
            'level': 'warning',
            'icon': 'fa-triangle-exclamation',
            'title': 'موجودی رو به اتمام',
            'message': (
                f'{low_stock} محصول حداکثر '
                f'۵ عدد موجودی دارد.'
            ),
        })

    cancellation_rate = _percent(
        status_map.get('cancelled', 0),
        order_count,
    )

    if cancellation_rate >= 10:
        alerts.append({
            'level': 'danger',
            'icon': 'fa-ban',
            'title': 'نرخ لغو بالا',
            'message': (
                f'{cancellation_rate}٪ سفارش‌های '
                f'این دوره لغو شده‌اند.'
            ),
        })

    if status_map.get('pending', 0):
        alerts.append({
            'level': 'info',
            'icon': 'fa-clock',
            'title': 'سفارش در انتظار',
            'message': (
                f'{status_map["pending"]} سفارش '
                f'هنوز در انتظار پرداخت یا بررسی است.'
            ),
        })

    if abandoned_carts:
        alerts.append({
            'level': 'info',
            'icon': 'fa-cart-shopping',
            'title': 'سبد خرید رهاشده',
            'message': (
                f'{abandoned_carts} سبد بیش از '
                f'۲۴ ساعت بدون تکمیل باقی مانده است.'
            ),
        })

    if stagnant_products:
        alerts.append({
            'level': 'warning',
            'icon': 'fa-chart-line',
            'title': 'کالای بدون فروش',
            'message': (
                f'حداقل {stagnant_products} محصول '
                f'موجود در این بازه فروشی نداشته است.'
            ),
        })

    # ============================================
    # آخرین سفارش‌ها
    # ============================================

    recent_orders = [
        {
            'number': order.order_number,
            'username': order.user.username,
            'total': float(order.total),
            'status': order.get_status_display(),
            'is_paid': order.is_paid,

            'date': timezone.localtime(
                order.created_at
            ).strftime('%Y/%m/%d %H:%M'),
        }

        for order in (
            orders
            .select_related('user')
            .order_by('-created_at')[:12]
        )
    ]

    # ============================================
    # KPIها
    # ============================================

    kpis = {
        'revenue': float(
            finance['revenue']
        ),

        'revenue_change': _change(
            finance['revenue'],
            previous_finance['revenue'],
        ),

        'gross': float(
            finance['gross']
        ),

        'discounts': float(
            finance['discounts']
        ),

        'shipping': float(
            finance['shipping']
        ),

        'orders': order_count,

        'orders_change': _change(
            order_count,
            previous_order_count,
        ),

        'paid_orders': paid_count,

        'payment_success_rate': _percent(
            paid_count,
            order_count,
        ),

        'average_order': float(
            finance['average']
        ),

        'average_order_change': _change(
            finance['average'],
            previous_finance['average'],
        ),

        'sold_items': sold_items,
        'unique_buyers': unique_buyers,

        'new_customers': new_customers,

        'new_customers_change': _change(
            new_customers,
            previous_new_customers,
        ),

        'returning_customers': (
            returning_customers
        ),

        'return_rate': _percent(
            returning_customers,
            buying_customers,
        ),

        'customer_purchase_rate': _percent(
            all_time_buyers,
            total_customers,
        ),

        'cancel_rate': (
            cancellation_rate
        ),
    }

    chart_data = {
        'timeline': timeline,
        'statuses': order_status,
        'payments': payment_methods,
        'categories': category_sales,
        'top_products': top_products[:8],
        'ratings': rating_distribution,
    }

    return {
        'selected_period': (
            selected['period']
        ),

        'selected_year': (
            selected['year']
        ),

        'selected_month': (
            selected['month']
        ),

        'selected_date_from': (
            selected['date_from']
        ),

        'selected_date_to': (
            selected['date_to']
        ),

        'period_label': (
            selected['label']
        ),

        'period_start': (
            selected['start_day']
        ),

        'period_end': (
            selected['end_day']
        ),

        'years': list(
            range(
                timezone.localdate().year - 4,
                timezone.localdate().year + 2,
            )
        ),

        'months': [
            {
                'value': number,
                'name': calendar.month_name[number],
            }
            for number in range(1, 13)
        ],

        'kpis': kpis,

        'finance': {
            key: float(value)
            for key, value in finance.items()
        },

        'order_status': order_status,
        'payment_methods': payment_methods,

        'top_products': top_products,
        'category_sales': category_sales,
        'top_customers': top_customers,

        'coupons': coupons,

        'rating_distribution': (
            rating_distribution
        ),

        'review_total': review_total,

        'verified_review_count': (
            verified_reviews.count()
        ),

        'review_average': round(
            float(review_average),
            1,
        ),

        'wishlist_count': wishlist_count,
        'popular_wishlist': popular_wishlist,

        'total_customers': total_customers,
        'buying_customers': buying_customers,

        'returning_customers': (
            returning_customers
        ),

        'no_purchase_customers': (
            no_purchase_customers
        ),

        'active_products': (
            active_products.count()
        ),

        'inventory_units': inventory_units,

        'inventory_value': float(
            inventory_value
        ),

        'out_of_stock': out_of_stock,
        'low_stock': low_stock,

        'inventory_rows': inventory_rows,

        'abandoned_carts': abandoned_carts,

        'peak': peak,

        'daily_average': float(
            daily_average
        ),

        'forecast_30_days': float(
            forecast_30_days
        ),

        'alerts': alerts,
        'recent_orders': recent_orders,

        'chart_data': chart_data,

        'generated_at': (
            timezone.localtime()
        ),
    }