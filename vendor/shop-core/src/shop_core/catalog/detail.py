"""Reusable product-detail view. Client Product model is dependency-injected."""
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.shortcuts import render

def core_product_detail(request, slug, *, product_model):
    product = get_object_or_404(product_model.objects.select_related('category', 'brand'), slug=slug, is_active=True)
    product_model.objects.filter(pk=product.pk).update(views_count=F('views_count') + 1)
    similar_products = product_model.objects.filter(category=product.category, is_active=True).exclude(id=product.id).select_related('category', 'brand')[:8]
    reviews = product.reviews.filter(is_verified=True).select_related('user')
    user_review = None
    if request.user.is_authenticated:
        user_review = product.reviews.filter(user=request.user).first()
    available_variants = product.variants.filter(is_active=True, stock__gt=0).select_related('color')
    color_variants = []
    seen_color_ids = set()
    for variant in available_variants:
        if variant.color_id and variant.color_id not in seen_color_ids:
            seen_color_ids.add(variant.color_id)
            color_variants.append(variant)
    return render(request, 'products/product_detail.html', {'product': product, 'similar_products': similar_products, 'reviews': reviews, 'user_review': user_review, 'available_variants': available_variants, 'available_colors': [variant.color for variant in color_variants], 'color_variants': color_variants})
