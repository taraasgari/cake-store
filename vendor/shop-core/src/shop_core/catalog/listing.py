"""Reusable product listing view. Client catalog models are dependency-injected."""
from decimal import Decimal
from decimal import InvalidOperation
from django.core.paginator import Paginator
from django.db.models import DecimalField, F, Min, Q
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.shortcuts import render

def core_product_list(request, *, product_model, category_model, brand_model):
    products = product_model.objects.filter(is_active=True).exclude(slug__isnull=True).exclude(slug='').select_related('category', 'brand').annotate(variant_min_price=Min(Coalesce('variants__discount_price', 'variants__price', F('price'), output_field=DecimalField(max_digits=12, decimal_places=0)), filter=Q(variants__is_active=True, variants__stock__gt=0))).annotate(effective_catalog_price=Coalesce('variant_min_price', 'discount_price', F('price'), output_field=DecimalField(max_digits=12, decimal_places=0)))
    category_slug = (request.GET.get('category') or '').strip()
    if category_slug:
        category = get_object_or_404(category_model, slug=category_slug, is_active=True)
        products = products.filter(category=category)
    brand_slug = (request.GET.get('brand') or '').strip()
    if brand_slug:
        brand = get_object_or_404(brand_model, slug=brand_slug, is_active=True)
        products = products.filter(brand=brand)

    def parse_price(value):
        value = (value or '').strip()
        if not value:
            return None
        try:
            number = Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            return None
        return number if number >= 0 else None
    min_price = parse_price(request.GET.get('min_price'))
    max_price = parse_price(request.GET.get('max_price'))
    if min_price is not None and max_price is not None and (min_price > max_price):
        (min_price, max_price) = (max_price, min_price)
    if min_price is not None:
        products = products.filter(effective_catalog_price__gte=min_price)
    if max_price is not None:
        products = products.filter(effective_catalog_price__lte=max_price)
    sort = request.GET.get('sort', '-created_at')
    sort_options = {'price': 'effective_catalog_price', '-price': '-effective_catalog_price', 'created_at': 'created_at', '-created_at': '-created_at', 'sales_count': '-sales_count', 'rating': '-rating'}
    products = products.order_by(sort_options.get(sort, '-created_at'))
    page_obj = Paginator(products, 12).get_page(request.GET.get('page'))
    return render(request, 'products/product_list.html', {'page_obj': page_obj, 'categories': category_model.objects.filter(is_active=True).exclude(slug__isnull=True).exclude(slug=''), 'brands': brand_model.objects.filter(is_active=True).exclude(slug__isnull=True).exclude(slug=''), 'current_sort': sort, 'selected_category': category_slug, 'selected_brand': brand_slug, 'total_products': product_model.objects.filter(is_active=True).count()})
