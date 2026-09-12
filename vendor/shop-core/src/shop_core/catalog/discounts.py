"""Reusable discounted-products view. Client Product model is dependency-injected."""
from django.core.paginator import Paginator
from django.shortcuts import render

def core_discounts(request, *, product_model):
    all_products = product_model.objects.filter(is_active=True).exclude(slug__isnull=True).exclude(slug='').prefetch_related('variants')
    discounted_products = []
    for product in all_products:
        has_discount = bool(product.discount_price and product.discount_price < product.price)
        if not has_discount and product.has_variants:
            for variant in product.variants.all():
                if not variant.is_active or not variant.discount_price:
                    continue
                base_price = variant.price if variant.price is not None else product.price
                if variant.discount_price < base_price:
                    has_discount = True
                    break
        if has_discount:
            discounted_products.append(product)
    discounted_products.sort(key=lambda item: item.discount_percent, reverse=True)
    page_obj = Paginator(discounted_products, 12).get_page(request.GET.get('page'))
    max_discount = max((product.discount_percent for product in page_obj), default=0)
    return render(request, 'products/discounts.html', {'page_obj': page_obj, 'title': 'محصولات با تخفیف ویژه', 'icon': 'fa-tags', 'description': 'بهترین محصولات با بهترین قیمت\u200cها', 'bg_gradient': 'from-red-500 to-pink-600', 'max_discount': max_discount})
