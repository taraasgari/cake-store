#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations
import shutil, subprocess, sys, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / ".perfume_frontend_backup"
FILES = {}

def run(cmd):
    print("\n> " + " ".join(map(str, cmd)))
    r = subprocess.run(cmd, cwd=ROOT, text=True)
    if r.returncode:
        raise RuntimeError("Command failed: " + " ".join(map(str, cmd)))

def backup(path):
    if not path.exists():
        return
    dst = BACKUP / path.relative_to(ROOT)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)

def write(rel, content):
    path = ROOT / rel
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    print("[WRITE]", rel)

FILES["first/templates/perfume_base.html"] = r'''
{% load static %}
<!doctype html>
<html lang="fa" dir="rtl" data-perfume-theme="night">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#090806">
<title>{% block title %}{{ settings.site_title|default:"VÉLORA Parfums" }}{% endblock %}</title>
<script>
try{
 const t=localStorage.getItem("perfume-luxury-theme");
 document.documentElement.dataset.perfumeTheme=(t==="day"||t==="night")?t:"night";
}catch(e){}
</script>
<link rel="stylesheet" href="{% static 'vendor/vazir/font-face.css' %}">
<link rel="stylesheet" href="{% static 'vendor/fontawesome/css/all.min.css' %}">
<link rel="stylesheet" href="{% static 'css/perfume-luxury.css' %}">
{% block extra_css %}{% endblock %}
</head>
<body>
<header class="lux-header" data-header>
  <a class="brand" href="{% url 'first:home' %}"><b>{{ settings.site_name|default:"VÉLORA" }}</b><small>SCENTS BEYOND TIME</small></a>
  <nav>
    <a href="{% url 'first:home' %}">خانه</a>
    <a href="{% url 'first:product_list' %}">عطرها</a>
    <a href="{% url 'first:best_sellers' %}">پرفروش‌ها</a>
    <a href="{% url 'first:discounts' %}">پیشنهاد ویژه</a>
    <a href="{% url 'first:customer_service' 'shopping-guide' %}">راهنما</a>
  </nav>
  <div class="actions">
    <button data-search-open><i class="fa-solid fa-magnifying-glass"></i></button>
    <button data-theme-toggle><i class="fa-regular fa-moon nicon"></i><i class="fa-regular fa-sun dicon"></i></button>
    {% if user.is_authenticated %}<a href="{% url 'first:profile' %}"><i class="fa-regular fa-user"></i></a>{% else %}<a href="{% url 'first:login' %}"><i class="fa-regular fa-user"></i></a>{% endif %}
    <a href="{% url 'first:cart' %}"><i class="fa-solid fa-bag-shopping"></i></a>
    <button data-menu-open class="hamb"><span></span><span></span></button>
  </div>
</header>

<aside class="mobile-menu" data-menu>
<button data-menu-close class="close">×</button>
<a class="menu-brand" href="{% url 'first:home' %}">VÉLORA</a>
<nav>
<a href="{% url 'first:home' %}">خانه</a><a href="{% url 'first:product_list' %}">همه عطرها</a><a href="{% url 'first:best_sellers' %}">پرفروش‌ها</a><a href="{% url 'first:discounts' %}">پیشنهاد ویژه</a><a href="{% url 'first:wishlist' %}">علاقه‌مندی‌ها</a>
{% if user.is_authenticated %}<a href="{% url 'first:user_orders' %}">سفارش‌ها</a><a href="{% url 'first:profile' %}">حساب من</a>{% else %}<a href="{% url 'first:login' %}">ورود</a><a href="{% url 'first:signup' %}">ثبت‌نام</a>{% endif %}
</nav>
</aside>

<div class="search-overlay" data-search>
<button data-search-close>×</button>
<form method="get" action="{% url 'first:search_products' %}">
<span class="eyebrow">SEARCH THE COLLECTION</span>
<label>چه رایحه‌ای می‌خواهی؟</label>
<div><input name="q" placeholder="نام عطر، برند یا رایحه..." autocomplete="off"><button><i class="fa-solid fa-arrow-left"></i></button></div>
</form>
</div>

{% if messages %}<div class="toasts">{% for message in messages %}<div>{{ message }}<button data-toast-close>×</button></div>{% endfor %}</div>{% endif %}

<main>{% block content %}{% endblock %}</main>

<footer>
<div class="footer-grid">
<div><a class="brand" href="{% url 'first:home' %}"><b>{{ settings.site_name|default:"VÉLORA" }}</b><small>SCENTS BEYOND TIME</small></a><p>رایحه‌ای برای لحظه‌هایی که قرار است در خاطر بمانند.</p></div>
<div><h4>فروشگاه</h4><a href="{% url 'first:product_list' %}">همه عطرها</a><a href="{% url 'first:best_sellers' %}">پرفروش‌ها</a><a href="{% url 'first:discounts' %}">تخفیف‌ها</a></div>
<div><h4>خدمات</h4><a href="{% url 'customer_care:support_home' %}">پشتیبانی</a><a href="{% url 'customer_care:order_tracking' %}">پیگیری سفارش</a><a href="{% url 'first:customer_service' 'shipping-returns' %}">ارسال و مرجوعی</a></div>
<div><h4>اطلاعات</h4><a href="{% url 'first:customer_service' 'terms' %}">قوانین</a><a href="{% url 'first:customer_service' 'privacy' %}">حریم خصوصی</a><a href="{% url 'first:customer_service' 'faq' %}">سوالات متداول</a></div>
</div>
<div class="footer-bottom"><span>{{ settings.footer_text|default:"© 2026 VÉLORA" }}</span><span>PERFUMERY · CRAFT · MEMORY</span></div>
</footer>
<script src="{% static 'js/perfume-luxury.js' %}"></script>
{% block extra_js %}{% endblock %}
</body></html>
'''

FILES["first/templates/includes/perfume_product_card.html"] = r'''
{% load custom_filters %}
<article class="product-card reveal">
<a class="product-media" href="{% url 'first:product_detail' product.slug %}">
<div class="badges">{% if product.is_best_seller %}<span>BESTSELLER</span>{% endif %}{% if product.is_new %}<span>NEW</span>{% endif %}{% if product.discount_percent %}<span class="sale">{{ product.discount_percent|format_number }}٪</span>{% endif %}</div>
{% if product.main_image %}<img src="{{ product.main_image.url }}" alt="{{ product.name }}" loading="lazy">{% else %}<div class="placeholder">V</div>{% endif %}
</a>
<div class="product-copy">{% if product.brand %}<small>{{ product.brand.name }}</small>{% endif %}<a href="{% url 'first:product_detail' product.slug %}">{{ product.name }}</a>
<div class="product-foot"><div><strong>{{ product.final_price|price_format }}</strong><span> تومان</span>{% if product.discount_percent %}<del>{{ product.price|price_format }}</del>{% endif %}</div>
{% if product.has_variants %}<a class="bag" href="{% url 'first:product_detail' product.slug %}"><i class="fa-solid fa-arrow-left"></i></a>{% else %}<form method="post" action="{% url 'first:add_to_cart' product.id %}">{% csrf_token %}<button class="bag"><i class="fa-solid fa-bag-shopping"></i></button></form>{% endif %}
</div></div></article>
'''

FILES["first/templates/index.html"] = r'''
{% extends 'perfume_base.html' %}{% load custom_filters %}
{% block title %}{{ settings.site_title|default:"VÉLORA — عطر فراتر از زمان" }}{% endblock %}
{% block content %}
{% firstof featured_products.0 best_sellers.0 new_products.0 as hero_product %}
<section class="hero">
{% for slider in sliders %}{% if forloop.first %}<img class="hero-bg" src="{{ slider.image.url }}" alt="">{% endif %}{% endfor %}
<div class="shade"></div><div class="arch"></div>
<div class="hero-copy"><span class="eyebrow">A HIGHER FORM OF BEAUTY</span><h1><span>رایحه‌ای</span><em>فراتر از زمان</em></h1><p>ترکیب‌هایی ماندگار برای کسانی که عطر را بخشی از هویت خود می‌دانند.</p><div class="hero-buttons"><a class="gold-btn" href="{% url 'first:product_list' %}">کشف کالکشن ←</a><a class="story-btn" href="#signature">◉ داستان رایحه</a></div></div>
<div class="hero-stage"><div class="orbit"></div>{% if hero_product and hero_product.main_image %}<a href="{% url 'first:product_detail' hero_product.slug %}"><img src="{{ hero_product.main_image.url }}" alt="{{ hero_product.name }}"></a>{% else %}<div class="css-bottle"><b>VÉLORA</b><small>EXTRAIT DE PARFUM</small></div>{% endif %}</div>
<div class="hero-features"><div><i class="fa-regular fa-gem"></i><span><b>مواد اولیه ممتاز</b><small>ترکیب‌های منتخب</small></span></div><div><i class="fa-regular fa-clock"></i><span><b>ماندگاری بالا</b><small>حضور طولانی‌تر</small></span></div><div><i class="fa-regular fa-heart"></i><span><b>انتخاب شخصی</b><small>متناسب با شخصیت شما</small></span></div></div>
</section>

<section class="ribbon"><div><i class="fa-solid fa-shield-halved"></i><b>اصالت کالا</b><small>تضمین اصالت</small></div><div><i class="fa-solid fa-truck-fast"></i><b>ارسال مطمئن</b><small>بسته‌بندی حرفه‌ای</small></div><div><i class="fa-solid fa-gift"></i><b>هدیه لوکس</b><small>برای لحظه‌های خاص</small></div><div><i class="fa-solid fa-headset"></i><b>مشاوره انتخاب</b><small>پشتیبانی تخصصی</small></div></section>

<section class="signature" id="signature"><div class="section-intro reveal"><span class="eyebrow">OUR SIGNATURE COLLECTION</span><h2>آیکون‌ها<br>در هر نت</h2><p>از رایحه‌های روشن تا عطرهای گرم، چوبی و عمیق.</p><a href="{% url 'first:product_list' %}">مشاهده همه ←</a></div><div class="signature-grid">{% for product in best_sellers|slice:":4" %}{% include 'includes/perfume_product_card.html' %}{% empty %}{% for product in featured_products|slice:":4" %}{% include 'includes/perfume_product_card.html' %}{% endfor %}{% endfor %}</div></section>

<section class="finder reveal"><div class="finder-art"><div class="face"></div><span>FIND<br>YOUR<br>SIGNATURE</span></div><div class="finder-copy"><span class="eyebrow">PERFUME FINDER</span><h2>رایحه امضای خودت را پیدا کن</h2><p>از حس شروع کن؛ گرم، روشن، چوبی یا گلی.</p><a class="outline-btn" href="{% url 'first:product_list' %}">شروع انتخاب ←</a></div><div class="note-deck"><a href="{% url 'first:search_products' %}?q=خنک">FRESH<b>خنک</b></a><a href="{% url 'first:search_products' %}?q=چوبی">WOODY<b>چوبی</b></a><a href="{% url 'first:search_products' %}?q=گلی">FLORAL<b>گلی</b></a><a href="{% url 'first:search_products' %}?q=گرم">AMBER<b>گرم</b></a></div></section>

<section class="editorial"><a href="{% url 'first:product_list' %}?sort=-created_at"><span>NEW ARRIVALS</span><h3>تازه‌رسیده‌ها</h3><b>کشف کنید ←</b></a><a href="{% url 'first:best_sellers' %}"><span>EXCLUSIVE COLLECTIONS</span><h3>کالکشن‌های خاص</h3><b>مشاهده ←</b></a><a href="{% url 'first:product_list' %}"><span>THE ART OF GIFTING</span><h3>هنر هدیه دادن</h3><b>انتخاب هدیه ←</b></a></section>

<section class="craft"><div class="craft-art"><span>MORE THAN<br>FRAGRANCE</span></div><div><span class="eyebrow">FROM NATURE TO ART</span><h2>از طبیعت،<br>تا یک اثر هنری</h2><p>هر عطر داستانی از ماده، زمان و حافظه است.</p><a class="outline-btn" href="{% url 'first:customer_service' 'shopping-guide' %}">راهنمای انتخاب عطر ←</a></div></section>

{% if new_products %}<section class="collection-section"><header><span class="eyebrow">NEW DISCOVERIES</span><h2>تازه وارد کالکشن</h2></header><div class="product-grid four">{% for product in new_products|slice:":4" %}{% include 'includes/perfume_product_card.html' %}{% endfor %}</div></section>{% endif %}
<section class="quote"><blockquote>«یک عطر عالی، قطعه‌ای از هنر نامرئی است.»</blockquote><span>MAURICE ROUCEL</span></section>
{% endblock %}
'''

FILES["first/templates/products/product_list.html"] = r'''
{% extends 'perfume_base.html' %}{% load custom_filters %}
{% block title %}کالکشن عطرها{% endblock %}
{% block content %}
<section class="page-hero"><span class="eyebrow">DISCOVER THE COLLECTION</span><h1>عطرها</h1><p>رایحه‌های متفاوت برای روز، شب و لحظه‌های خاص.</p></section>
<section class="catalog">
<aside class="filters" data-filters><button class="filter-close" data-filter-close>×</button><h3>فیلتر کالکشن</h3>
<div><span>CATEGORY</span><a href="{% url 'first:product_list' %}">همه عطرها</a>{% for category in categories %}{% if category.slug %}<a href="?category={{ category.slug }}">{{ category.name }}</a>{% endif %}{% endfor %}</div>
<div><span>BRAND</span>{% for brand in brands %}{% if brand.slug %}<a href="?brand={{ brand.slug }}">{{ brand.name }}</a>{% endif %}{% endfor %}</div>
<form method="get"><span>PRICE</span><div class="price-pair"><input name="min_price" value="{{ request.GET.min_price }}" type="number" placeholder="از"><input name="max_price" value="{{ request.GET.max_price }}" type="number" placeholder="تا"></div><button class="outline-btn full">اعمال</button></form></aside>
<div class="catalog-main"><div class="catalog-toolbar"><button data-filter-open>فیلترها</button><span>{{ page_obj.paginator.count }} رایحه</span><select data-sort><option value="-created_at">جدیدترین</option><option value="-sales_count">پرفروش‌ترین</option><option value="-rating">امتیاز</option><option value="price">قیمت کم به زیاد</option><option value="-price">قیمت زیاد به کم</option></select></div><div class="product-grid three">{% for product in page_obj %}{% include 'includes/perfume_product_card.html' %}{% empty %}<div class="empty">محصولی پیدا نشد.</div>{% endfor %}</div></div>
</section>
{% endblock %}
'''

FILES["first/templates/products/product_detail.html"] = r'''
{% extends 'perfume_base.html' %}{% load custom_filters %}
{% block title %}{{ product.name }}{% endblock %}
{% block content %}
<section class="detail-page"><div class="detail-grid">
<div><div class="detail-media">{% if product.main_image %}<img id="detailMainImage" src="{{ product.main_image.url }}" alt="{{ product.name }}">{% else %}<div class="css-bottle"><b>VÉLORA</b></div>{% endif %}</div>{% if product.main_image %}<div class="thumbs"><button data-image="{{ product.main_image.url }}"><img src="{{ product.main_image.url }}" alt=""></button>{% for image in product.images.all %}<button data-image="{{ image.image.url }}"><img src="{{ image.image.url }}" alt=""></button>{% endfor %}</div>{% endif %}</div>
<div class="detail-copy"><span class="eyebrow">{{ product.brand.name|default:"SIGNATURE FRAGRANCE" }}</span><h1>{{ product.name }}</h1><div class="meta"><span>★★★★★</span><b>{{ product.rating|floatformat:1 }}</b><small>{{ reviews.count }} نظر</small></div>{% if product.short_description %}<p>{{ product.short_description }}</p>{% endif %}<div class="price"><strong id="detailPrice">{{ product.final_price|price_format }}</strong><small>تومان</small>{% if product.discount_percent %}<del>{{ product.price|price_format }}</del>{% endif %}</div>
<div class="notes"><div><small>TOP</small><b>نت آغازین</b></div><div><small>HEART</small><b>نت میانی</b></div><div><small>BASE</small><b>نت پایه</b></div></div>
<form method="post" action="{% url 'first:add_to_cart' product.id %}" class="buy-form">{% csrf_token %}<input type="hidden" name="variant" id="variantInput">{% if product.has_variants %}<div class="variants">{% for variant in available_variants %}<button type="button" data-variant="{{ variant.id }}" data-price="{{ variant.final_price }}" data-stock="{{ variant.stock }}" data-vimage="{% if variant.image %}{{ variant.image.url }}{% endif %}">{% if variant.volume_ml %}{{ variant.volume_ml }} ml{% elif variant.size %}{{ variant.size }}{% elif variant.color %}{{ variant.color.name }}{% else %}گزینه {{ forloop.counter }}{% endif %}</button>{% endfor %}</div>{% endif %}<div class="buy-row"><div class="qty"><button type="button" data-minus>−</button><input id="qty" name="qty" value="1" min="1" type="number"><button type="button" data-plus>+</button></div><button class="gold-btn grow" {% if not product.is_in_stock %}disabled{% endif %}>افزودن به سبد</button></div></form>
{% if user.is_authenticated %}<form method="post" action="{% url 'first:add_to_wishlist' product.id %}">{% csrf_token %}<button class="wishlist-btn">♡ افزودن به علاقه‌مندی‌ها</button></form>{% endif %}
<div class="guarantees"><span>◇ اصالت تضمین‌شده</span><span>□ بسته‌بندی لوکس</span><span>◷ ارسال مطمئن</span></div></div>
</div></section>
<section class="detail-story"><div><span class="eyebrow">THE CHARACTER</span><h2>رایحه‌ای که<br>بعد از شما می‌ماند</h2></div><div>{{ product.description|linebreaks }}</div></section>
<section class="reviews"><header><span class="eyebrow">REVIEWS</span><h2>تجربه خریداران</h2></header>{% if user.is_authenticated %}<form class="review-form" method="post" action="{% url 'first:add_review' product.id %}">{% csrf_token %}<select name="rating"><option value="5">★★★★★</option><option value="4">★★★★</option><option value="3">★★★</option></select><textarea name="comment" rows="4" required></textarea><button class="outline-btn">ثبت نظر</button></form>{% endif %}<div class="review-grid">{% for review in reviews %}<article><span>★★★★★</span><p>{{ review.comment }}</p><small>{{ review.user.username }}</small></article>{% empty %}<div class="empty">هنوز نظری ثبت نشده است.</div>{% endfor %}</div></section>
{% if similar_products %}<section class="collection-section"><header><span class="eyebrow">YOU MAY ALSO LIKE</span><h2>انتخاب‌های مشابه</h2></header><div class="product-grid four">{% for product in similar_products %}{% include 'includes/perfume_product_card.html' %}{% endfor %}</div></section>{% endif %}
{% endblock %}
'''

FILES["first/templates/cart/cart.html"] = r'''
{% extends 'perfume_base.html' %}{% load custom_filters %}
{% block title %}سبد خرید{% endblock %}
{% block content %}<section class="page-hero compact"><span class="eyebrow">YOUR SELECTION</span><h1>سبد خرید</h1></section><section class="cart-layout"><div>{% for item in items %}<article class="cart-item"><div class="cart-img">{% if item.product.main_image %}<img src="{{ item.product.main_image.url }}">{% endif %}</div><div><small>{{ item.product.brand.name }}</small><h3>{{ item.product.name }}</h3><strong>{{ item.final_price|price_format }} تومان</strong></div><form class="cart-qty" method="post" action="{% url 'first:update_cart_item' item.id %}">{% csrf_token %}<input name="quantity" type="number" min="0" value="{{ item.quantity }}"><button>ثبت</button></form><form method="post" action="{% url 'first:remove_from_cart' item.id %}">{% csrf_token %}<button class="trash">×</button></form></article>{% empty %}<div class="empty"><h2>سبد خریدت خالی است</h2><a class="gold-btn" href="{% url 'first:product_list' %}">مشاهده عطرها</a></div>{% endfor %}</div>{% if items %}<aside class="summary"><span class="eyebrow">ORDER SUMMARY</span><h2>خلاصه سفارش</h2><div><span>جمع</span><b>{{ total_price|price_format }}</b></div><div><span>تخفیف</span><b>{{ total_discount|price_format }}</b></div><div class="total"><span>نهایی</span><strong>{{ final_price|price_format }} تومان</strong></div><a class="gold-btn full" href="{% url 'first:checkout' %}">ادامه و ثبت سفارش</a></aside>{% endif %}</section>{% endblock %}
'''

FILES["first/templates/cart/checkout.html"] = r'''
{% extends 'perfume_base.html' %}{% load custom_filters %}
{% block title %}تکمیل سفارش{% endblock %}
{% block content %}<section class="page-hero compact"><span class="eyebrow">CHECKOUT</span><h1>تکمیل سفارش</h1></section><section class="checkout-layout"><form method="post" id="checkoutForm" class="lux-form">{% csrf_token %}<h2>اطلاعات تحویل</h2><label>شماره تماس<input name="phone" value="{{ user.phone|default:'' }}" required></label><label>کد پستی<input name="postal_code" required></label><label>آدرس<textarea name="address" rows="4" required>{{ user.address|default:'' }}</textarea></label><label>توضیحات<textarea name="note"></textarea></label><label><input type="radio" name="payment_method" value="cash" checked> پرداخت در محل</label></form><aside class="summary"><span class="eyebrow">YOUR ORDER</span><h2>سفارش شما</h2>{% for item in items %}<div><span>{{ item.product.name }} × {{ item.quantity }}</span><b>{{ item.final_price|price_format }}</b></div>{% endfor %}<div class="total"><span>قابل پرداخت</span><strong>{{ final_price|price_format }} تومان</strong></div><button class="gold-btn full" form="checkoutForm">ثبت نهایی سفارش</button></aside></section>{% endblock %}
'''

FILES["first/templates/products/wishlist.html"] = r'''
{% extends 'perfume_base.html' %}{% block title %}علاقه‌مندی‌ها{% endblock %}{% block content %}<section class="page-hero compact"><span class="eyebrow">SAVED SCENTS</span><h1>علاقه‌مندی‌ها</h1></section><section class="collection-section"><div class="product-grid four">{% for item in wishlist_items %}{% with product=item.product %}{% include 'includes/perfume_product_card.html' %}{% endwith %}{% empty %}<div class="empty">هنوز عطری ذخیره نکردی.</div>{% endfor %}</div></section>{% endblock %}
'''

FILES["first/templates/cart/user_orders.html"] = r'''
{% extends 'perfume_base.html' %}{% load custom_filters %}{% block title %}سفارش‌های من{% endblock %}{% block content %}<section class="page-hero compact"><span class="eyebrow">ORDER HISTORY</span><h1>سفارش‌های من</h1></section><section class="orders"><form class="track" method="get"><input name="order_code" value="{{ order_code|default:'' }}" placeholder="شماره سفارش"><button class="gold-btn">پیگیری</button></form>{% for order in orders %}<a class="order-row" href="{% url 'first:order_detail' order.order_number %}"><span>#{{ order.order_number }}</span><span>{{ order.created_at|date:"Y/m/d" }}</span><span>{{ order.get_status_display }}</span><b>{{ order.total|price_format }} تومان</b></a>{% empty %}<div class="empty">هنوز سفارشی ثبت نکردی.</div>{% endfor %}</section>{% endblock %}
'''

FILES["first/templates/cart/order_success.html"] = r'''
{% extends 'perfume_base.html' %}{% block title %}سفارش ثبت شد{% endblock %}{% block content %}<section class="success"><i class="fa-solid fa-check"></i><span class="eyebrow">ORDER CONFIRMED</span><h1>سفارشت ثبت شد</h1><b>#{{ order.order_number }}</b><div><a class="gold-btn" href="{% url 'first:order_detail' order.order_number %}">جزئیات سفارش</a><a class="outline-btn" href="{% url 'first:product_list' %}">ادامه خرید</a></div></section>{% endblock %}
'''

FILES["first/templates/cart/order_detail.html"] = r'''
{% extends 'perfume_base.html' %}{% load custom_filters %}{% block title %}سفارش #{{ order.order_number }}{% endblock %}{% block content %}<section class="page-hero compact"><span class="eyebrow">ORDER DETAILS</span><h1>#{{ order.order_number }}</h1></section><section class="order-detail"><div><h2>{{ order.get_status_display }}</h2><strong>{{ order.total|price_format }} تومان</strong>{% for item in order.items.all %}<div class="ordered-item"><span>{{ item.product_name }} × {{ item.quantity }}</span><b>{{ item.total|price_format }}</b></div>{% endfor %}<p>{{ order.address }}</p></div><aside><a class="outline-btn full" href="{% url 'customer_care:support_create' %}?order={{ order.order_number }}">پشتیبانی سفارش</a><a class="outline-btn full" href="{% url 'customer_care:return_order_request' order.order_number %}">درخواست مرجوعی</a></aside></section>{% endblock %}
'''

AUTH = r'''
{% extends 'perfume_base.html' %}{% block title %}__TITLE__{% endblock %}{% block content %}<section class="auth-page"><div class="auth-art"><div class="css-bottle"><b>VÉLORA</b><small>PARFUM</small></div></div><div class="auth-panel"><span class="eyebrow">__EYEBROW__</span><h1>__HEADING__</h1><p>__INTRO__</p><form method="post" enctype="multipart/form-data" class="lux-form">{% csrf_token %}{{ form.as_p }}<button class="gold-btn full">__BUTTON__</button></form>__EXTRA__</div></section>{% endblock %}
'''
def auth(title,eye,head,intro,button,extra=""):
    return AUTH.replace("__TITLE__",title).replace("__EYEBROW__",eye).replace("__HEADING__",head).replace("__INTRO__",intro).replace("__BUTTON__",button).replace("__EXTRA__",extra)
FILES["first/templates/login.html"] = auth("ورود","WELCOME BACK","خوش آمدید","به حساب خود وارد شوید.","ورود",'<p><a href="{% url \'first:signup\' %}">ساخت حساب</a></p>')
FILES["first/templates/signup.html"] = auth("ثبت‌نام","JOIN THE HOUSE","ساخت حساب","برای تجربه خرید شخصی‌تر حساب بسازید.","ثبت‌نام",'<p><a href="{% url \'first:login\' %}">ورود</a></p>')
FILES["first/templates/edit_profile.html"] = auth("ویرایش پروفایل","YOUR DETAILS","ویرایش پروفایل","اطلاعات حساب را به‌روزرسانی کنید.","ذخیره","")
FILES["first/templates/forgot_password.html"] = auth("بازیابی رمز","ACCOUNT RECOVERY","بازیابی رمز","ایمیل حساب را وارد کنید.","ارسال کد","")
FILES["first/templates/set_new_password.html"] = auth("رمز جدید","NEW PASSWORD","رمز عبور جدید","رمز جدید را انتخاب کنید.","ذخیره رمز","")

FILES["first/templates/profile.html"] = r'''
{% extends 'perfume_base.html' %}{% block title %}حساب کاربری{% endblock %}{% block content %}<section class="profile-page"><aside><div class="avatar">{% if user.profile_image %}<img src="{{ user.profile_image.url }}">{% else %}{{ user.username|first|upper }}{% endif %}</div><span class="eyebrow">MEMBER PROFILE</span><h1>{{ user.get_full_name|default:user.username }}</h1><p>{{ user.email }}</p><a class="outline-btn full" href="{% url 'first:edit_profile' %}">ویرایش پروفایل</a></aside><div class="profile-links"><a href="{% url 'first:user_orders' %}">سفارش‌های من</a><a href="{% url 'first:wishlist' %}">علاقه‌مندی‌ها</a><a href="{% url 'customer_care:support_home' %}">پشتیبانی</a>{% if user.is_admin %}<a href="{% url 'first:admin_dashboard' %}">پنل مدیریت</a>{% endif %}</div></section>{% endblock %}
'''

FILES["first/templates/customer_service.html"] = r'''
{% extends 'perfume_base.html' %}{% block title %}{{ page.title }}{% endblock %}{% block content %}<section class="page-hero"><span class="eyebrow">{{ page.eyebrow|default:"CLIENT SERVICES" }}</span><h1>{{ page.title }}</h1><p>{{ page.intro }}</p></section><section class="customer-layout"><div>{% for section in page.sections %}<article class="service-card"><span>0{{ forloop.counter }}</span><div><h2>{{ section.title }}</h2>{% if section.body %}<p>{{ section.body }}</p>{% endif %}{% if section.items %}<ul>{% for item in section.items %}<li>{{ item }}</li>{% endfor %}</ul>{% endif %}</div></article>{% endfor %}</div><aside><span class="eyebrow">NEED HELP?</span><h3>پشتیبانی شخصی</h3><p>اگر پاسخ سوالت را پیدا نکردی با پشتیبانی در ارتباط باش.</p><a class="gold-btn full" href="{% url 'customer_care:support_create' %}">ثبت تیکت</a></aside></section>{% endblock %}
'''

GEN = r'''{% extends 'perfume_base.html' %}{% block title %}__TITLE__{% endblock %}{% block content %}<section class="page-hero compact"><span class="eyebrow">__EYE__</span><h1>__TITLE__</h1><p>__DESC__</p></section><section class="collection-section"><div class="product-grid four">{% for product in page_obj %}{% include 'includes/perfume_product_card.html' %}{% empty %}<div class="empty">محصولی وجود ندارد.</div>{% endfor %}</div></section>{% endblock %}'''
FILES["first/templates/products/best_sellers.html"] = GEN.replace("__TITLE__","پرفروش‌ترین‌ها").replace("__EYE__","MOST LOVED").replace("__DESC__","رایحه‌هایی که بیشتر از همه انتخاب شده‌اند.")
FILES["first/templates/products/discounts.html"] = GEN.replace("__TITLE__","پیشنهادهای ویژه").replace("__EYE__","PRIVATE OFFERS").replace("__DESC__","فرصت‌های محدود برای انتخاب رایحه‌های خاص.")

FILES["static/css/perfume-luxury.css"] = r'''
:root{--bg:#090806;--panel:#15130f;--panel2:#1b1813;--text:#f4eee5;--muted:#a99f91;--gold:#d6b475;--gold2:#a77a3a;--goldp:#efd5a0;--line:rgba(215,181,122,.20);--strong:rgba(215,181,122,.45);--serif:Georgia,"Times New Roman",serif;--shadow:0 28px 80px rgba(0,0,0,.35)}
html[data-perfume-theme="day"]{--bg:#f4eee5;--panel:#fffaf3;--panel2:#e9ddcf;--text:#17130f;--muted:#6c6257;--gold:#9c7031;--gold2:#c29859;--goldp:#896028;--line:rgba(112,84,48,.18);--strong:rgba(145,104,48,.42);--shadow:0 28px 80px rgba(78,54,27,.12)}
*{box-sizing:border-box}html{background:var(--bg);scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font-family:Vazir,Tahoma,Arial,sans-serif;line-height:1.85;transition:.3s;overflow-x:hidden}a{color:inherit;text-decoration:none}img{display:block;max-width:100%}button,input,textarea,select{font:inherit;color:inherit}.eyebrow{font-size:8px;letter-spacing:.28em;color:var(--gold);font-weight:700;direction:ltr}.full{width:100%}
.lux-header{position:fixed;z-index:100;top:0;left:0;right:0;height:92px;padding:0 4.5vw;display:grid;grid-template-columns:240px 1fr 240px;align-items:center;background:linear-gradient(to bottom,rgba(5,4,3,.74),transparent);transition:.3s}.lux-header.scrolled{height:74px;background:color-mix(in srgb,var(--bg) 91%,transparent);backdrop-filter:blur(20px);border-bottom:1px solid var(--line)}html[data-perfume-theme="day"] .lux-header{background:linear-gradient(to bottom,rgba(255,250,243,.92),transparent)}.brand{display:flex;flex-direction:column;width:max-content;direction:ltr}.brand b{font-family:var(--serif);font-size:23px;letter-spacing:.30em;color:var(--goldp);font-weight:400}.brand small{font-size:6px;letter-spacing:.4em;color:var(--muted)}.lux-header>nav{display:flex;justify-content:center;gap:28px}.lux-header>nav a{font-size:11px}.actions{display:flex;justify-content:flex-end;gap:3px;direction:ltr}.actions>*{width:39px;height:39px;border:0;background:none;display:grid;place-items:center}.dicon{display:none}html[data-perfume-theme="day"] .nicon{display:none}html[data-perfume-theme="day"] .dicon{display:block}.hamb{display:none!important}.hamb span{width:18px;height:1px;background:currentColor;display:block;margin:2px}
.mobile-menu{position:fixed;z-index:170;inset:0;background:#090806;color:#f4eee5;padding:30px 8vw;transform:translateX(105%);transition:.35s}.mobile-menu.open{transform:none}.mobile-menu .close{position:absolute;left:25px;top:20px;background:none;border:0;font-size:40px}.menu-brand{font-family:var(--serif);font-size:25px;letter-spacing:.25em;color:#d6b475}.mobile-menu nav{display:grid;margin-top:60px}.mobile-menu nav a{font-family:var(--serif);font-size:34px;padding:12px 0;border-bottom:1px solid rgba(215,181,122,.18)}
.search-overlay{position:fixed;z-index:180;inset:0;background:rgba(8,7,5,.97);color:#f4eee5;display:flex;align-items:flex-start;justify-content:center;padding-top:20vh;opacity:0;visibility:hidden;transition:.25s}.search-overlay.open{opacity:1;visibility:visible}.search-overlay>button{position:absolute;left:5vw;top:4vh;background:none;border:0;color:white;font-size:40px}.search-overlay form{width:min(820px,88vw)}.search-overlay label{font-family:var(--serif);font-size:clamp(36px,6vw,70px);display:block;margin:12px 0}.search-overlay form>div{display:flex;border-bottom:1px solid rgba(215,181,122,.35)}.search-overlay input{flex:1;background:none;border:0;color:white;padding:16px 0;outline:none}.search-overlay form button{width:55px;border:0;background:none;color:#d6b475}
.toasts{position:fixed;z-index:210;top:95px;right:20px;width:min(420px,calc(100vw - 40px));display:grid;gap:7px}.toasts>div{padding:12px 14px;background:var(--panel);border:1px solid var(--line);box-shadow:var(--shadow);display:flex;justify-content:space-between;font-size:10px}.toasts button{border:0;background:none}
.gold-btn,.outline-btn{min-height:48px;padding:0 24px;display:inline-flex;align-items:center;justify-content:center;gap:14px;border:1px solid transparent;background:none;cursor:pointer;font-size:10px}.gold-btn{background:linear-gradient(120deg,var(--goldp),var(--gold2));color:#171008}.outline-btn{border-color:var(--strong);color:var(--text)}
.hero{min-height:790px;height:min(900px,100vh);position:relative;display:grid;grid-template-columns:1fr 1.12fr .70fr;align-items:center;padding:135px 4.5vw 55px;overflow:hidden}.hero-bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:-4;opacity:.5}.shade{position:absolute;z-index:-3;inset:0;background:linear-gradient(90deg,rgba(4,3,2,.95),rgba(4,3,2,.55),rgba(4,3,2,.12),rgba(4,3,2,.82))}html[data-perfume-theme="day"] .shade{background:linear-gradient(90deg,rgba(250,245,238,.98),rgba(250,245,238,.75),rgba(250,245,238,.25),rgba(250,245,238,.92))}.arch{position:absolute;z-index:-2;width:40%;height:78%;left:31%;top:8%;border:1px solid var(--line);border-radius:50% 50% 0 0/34% 34% 0 0}.hero-copy h1{font-family:var(--serif);font-weight:400;line-height:.93}.hero-copy h1 span,.hero-copy h1 em{display:block}.hero-copy h1 span{font-size:clamp(55px,6vw,96px)}.hero-copy h1 em{font-size:clamp(44px,5vw,80px);font-style:normal;color:var(--goldp)}.hero-copy p{color:var(--muted);max-width:520px}.hero-buttons{display:flex;gap:12px;margin-top:28px}.story-btn{display:flex;align-items:center;gap:8px}.hero-stage{height:620px;display:grid;place-items:center;position:relative}.orbit{position:absolute;width:72%;height:36%;border:2px solid rgba(226,165,75,.5);border-radius:50%;transform:rotate(-18deg)}.hero-stage>a{z-index:2;width:72%;height:520px}.hero-stage img{width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 45px 34px rgba(0,0,0,.6))}.css-bottle{width:230px;height:350px;border:2px solid var(--gold);border-radius:25px;background:linear-gradient(90deg,#0d0a08,#6b401d,#0d0907);display:flex;flex-direction:column;align-items:center;justify-content:center;color:#d6aa65;position:relative;z-index:2}.css-bottle:before{content:"";position:absolute;top:-80px;width:120px;height:73px;border:1px solid var(--gold);background:#17110d;border-radius:13px}.hero-features{display:grid;gap:28px}.hero-features>div{display:flex;gap:12px}.hero-features i{width:42px;height:42px;border:1px solid var(--strong);border-radius:50%;display:grid;place-items:center;color:var(--gold)}.hero-features b{display:block;font-size:10px}.hero-features small{color:var(--muted);font-size:8px}
.ribbon{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:0 4vw}.ribbon>div{padding:20px 3vw;border-left:1px solid var(--line);display:grid;grid-template-columns:35px 1fr;grid-template-rows:auto auto}.ribbon i{grid-row:1/3;color:var(--gold)}.ribbon b{font-size:10px}.ribbon small{font-size:7px;color:var(--muted)}
.signature{max-width:1600px;margin:auto;padding:80px 4.5vw;display:grid;grid-template-columns:270px 1fr;gap:40px}.section-intro h2,.finder-copy h2,.craft h2,.collection-section h2,.reviews h2,.summary h2,.service-card h2{font-family:var(--serif);font-weight:400;font-size:clamp(36px,4vw,58px);line-height:1.05}.section-intro p,.finder-copy p,.craft p{color:var(--muted)}.signature-grid,.product-grid{display:grid;gap:11px}.signature-grid{grid-template-columns:repeat(4,1fr)}.product-grid.four{grid-template-columns:repeat(4,1fr)}.product-grid.three{grid-template-columns:repeat(3,1fr)}
.product-card{border:1px solid var(--line);background:linear-gradient(145deg,var(--panel),var(--panel2));transition:.25s;overflow:hidden}.product-card:hover{transform:translateY(-4px);box-shadow:var(--shadow)}.product-media{height:330px;display:grid;place-items:center;position:relative}.product-media img{width:100%;height:100%;object-fit:contain;padding:25px}.badges{position:absolute;z-index:2;top:10px;right:10px;display:flex;gap:4px}.badges span{font-size:6px;padding:3px 6px;background:var(--goldp);color:#171008}.badges .sale{background:#7d302d;color:#fff}.placeholder{width:74px;height:140px;border:1px solid var(--gold);display:grid;place-items:center}.product-copy{padding:13px}.product-copy>small{font-size:7px;color:var(--muted)}.product-copy>a{font-family:var(--serif);font-size:17px;display:block}.product-foot{display:flex;justify-content:space-between;align-items:end;margin-top:13px}.product-foot strong{font-size:11px}.product-foot span,.product-foot del{font-size:7px;color:var(--muted)}.product-foot del{display:block}.bag{width:33px;height:33px;border:1px solid var(--line);display:grid;place-items:center;background:none}
.finder{min-height:430px;display:grid;grid-template-columns:.8fr 1fr 1.1fr;border-top:1px solid var(--line);border-bottom:1px solid var(--line);background:linear-gradient(115deg,#0a0706,#1d1712,#090706);color:#f4eee5}.finder-art{position:relative;display:grid;place-items:center}.face{position:absolute;width:45%;height:76%;border-radius:50%;background:radial-gradient(ellipse at 55% 25%,#8d6049,#4d3025 35%,#160f0b 65%,transparent 66%)}.finder-art>span{position:relative;font-family:var(--serif);font-size:24px;color:#d7b47c}.finder-copy{padding:65px 45px;display:flex;justify-content:center;flex-direction:column}.note-deck{display:flex;align-items:center;justify-content:center;direction:ltr}.note-deck a{width:115px;height:235px;margin-left:-13px;padding:13px;display:flex;flex-direction:column;justify-content:flex-end;border:1px solid rgba(220,185,128,.15)}.note-deck a b{font-family:var(--serif)}.note-deck a:nth-child(1){transform:rotate(-8deg);background:#39433b}.note-deck a:nth-child(2){transform:rotate(-3deg);background:#3b291f}.note-deck a:nth-child(3){transform:rotate(4deg);background:#66545a}.note-deck a:nth-child(4){transform:rotate(9deg);background:#69402a}
.editorial{display:grid;grid-template-columns:repeat(3,1fr)}.editorial>a{min-height:300px;padding:45px 4vw;display:flex;flex-direction:column;justify-content:flex-end;color:#f4eee5}.editorial>a:nth-child(1){background:radial-gradient(circle at 70% 30%,#8a5d35,transparent 16%),#1e130e}.editorial>a:nth-child(2){background:#15130f}.editorial>a:nth-child(3){background:#5b3e25}.editorial span{font-size:7px;color:#d7b477}.editorial h3{font-family:var(--serif);font-weight:400;font-size:31px}.editorial b{font-size:8px;color:#d7b477}.craft{display:grid;grid-template-columns:1fr 1fr;min-height:470px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.craft-art{background:radial-gradient(circle at 40% 45%,#dfcfb4 0 8%,#a6825b 12%,#433021 35%,#090706 70%);display:flex;align-items:flex-end;padding:35px;color:#ddc29b;font-family:var(--serif);font-size:23px}.craft>div:last-child{padding:65px 8vw}.collection-section,.reviews{max-width:1500px;margin:auto;padding:70px 4.5vw}.quote{max-width:1500px;margin:auto;padding:55px 5vw;display:flex;justify-content:space-between}.quote blockquote{font-family:var(--serif);font-size:26px}
.page-hero{padding:155px 4.5vw 55px;max-width:1500px;margin:auto;border-bottom:1px solid var(--line)}.page-hero.compact{padding-bottom:35px}.page-hero h1{font-family:var(--serif);font-weight:400;font-size:clamp(50px,7vw,88px);margin:10px 0}.page-hero p{color:var(--muted)}.catalog{max-width:1500px;margin:auto;padding:45px 4.5vw 85px;display:grid;grid-template-columns:250px 1fr;gap:38px}.filters{border-left:1px solid var(--line);padding-left:22px}.filters>div,.filters>form{display:grid;gap:6px;padding-bottom:20px;margin-bottom:20px;border-bottom:1px solid var(--line)}.filters span{font-size:7px;color:var(--gold)}.filters a{font-size:9px;color:var(--muted)}.filters input,.catalog-toolbar select,.lux-form input,.lux-form textarea,.lux-form select{width:100%;background:var(--panel);border:1px solid var(--line);padding:10px;outline:none}.filter-close{display:none}.price-pair{display:grid;grid-template-columns:1fr 1fr;gap:6px}.catalog-toolbar{display:flex;justify-content:space-between;margin-bottom:18px}.catalog-toolbar>button{display:none}.empty{grid-column:1/-1;border:1px solid var(--line);padding:50px;text-align:center;color:var(--muted)}
.detail-page{max-width:1500px;margin:auto;padding:130px 4.5vw 65px}.detail-grid{display:grid;grid-template-columns:1.05fr .95fr;gap:55px}.detail-media{height:650px;border:1px solid var(--line);display:grid;place-items:center;background:var(--panel)}.detail-media>img{width:100%;height:100%;object-fit:contain;padding:45px}.thumbs{display:flex;gap:7px;margin-top:8px}.thumbs button{width:70px;height:70px;background:var(--panel);border:1px solid var(--line)}.thumbs img{width:100%;height:100%;object-fit:contain}.detail-copy h1{font-family:var(--serif);font-weight:400;font-size:clamp(48px,5.5vw,76px)}.meta{display:flex;gap:9px;color:var(--muted);font-size:8px}.meta span{color:var(--gold)}.detail-copy>p{color:var(--muted)}.price{display:flex;gap:8px;align-items:baseline}.price strong{font-family:var(--serif);font-size:29px}.price small,.price del{font-size:8px;color:var(--muted)}.notes{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--line);border-bottom:1px solid var(--line);margin:22px 0}.notes>div{padding:15px;border-left:1px solid var(--line)}.notes small{color:var(--gold);font-size:6px}.notes b{display:block;font-family:var(--serif)}.variants{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:13px}.variants button{border:1px solid var(--line);background:none;padding:8px}.variants button.selected{border-color:var(--gold)}.buy-row{display:flex;gap:8px}.qty{height:48px;border:1px solid var(--line);display:flex}.qty button{width:35px;border:0;background:none}.qty input{width:42px;border:0;background:none;text-align:center}.grow{flex:1}.wishlist-btn{width:100%;border:0;background:none;color:var(--muted);padding:10px}.guarantees{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--line);margin-top:18px}.guarantees span{padding:13px;font-size:7px}.detail-story{display:grid;grid-template-columns:.8fr 1.2fr;gap:7vw;padding:60px 8vw;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.detail-story h2{font-family:var(--serif);font-weight:400;font-size:45px}.detail-story>div:last-child{color:var(--muted)}.review-form{display:grid;gap:8px;border:1px solid var(--line);padding:18px}.review-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:15px}.review-grid article{border:1px solid var(--line);padding:18px}.review-grid article>span{color:var(--gold)}
.cart-layout,.checkout-layout,.orders,.order-detail,.profile-page,.customer-layout,.care,.form-page,.conversation{max-width:1400px;margin:auto;padding:45px 4.5vw 85px}.cart-layout{display:grid;grid-template-columns:1fr 350px;gap:45px}.cart-item{display:grid;grid-template-columns:105px 1fr auto 35px;gap:15px;align-items:center;border-bottom:1px solid var(--line);padding:14px 0}.cart-img{height:115px;background:var(--panel)}.cart-img img{width:100%;height:100%;object-fit:contain}.cart-item h3{font-family:var(--serif);font-weight:400}.cart-item small{color:var(--muted)}.cart-item strong{display:block}.cart-qty{display:flex;gap:5px}.cart-qty input{width:55px;background:var(--panel);border:1px solid var(--line);padding:7px}.cart-qty button,.trash{border:0;background:none}.summary{border:1px solid var(--line);background:var(--panel);padding:25px;height:max-content}.summary h2{font-size:32px}.summary>div{display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid var(--line)}.summary .total strong{font-family:var(--serif);color:var(--gold)}.checkout-layout{display:grid;grid-template-columns:1fr 370px;gap:50px}.lux-form{display:grid;gap:13px}.lux-form label,.lux-form p{display:grid;gap:5px;color:var(--muted);font-size:9px}.track{display:flex;gap:7px}.track input{flex:1;background:var(--panel);border:1px solid var(--line);padding:0 10px}.order-row{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;border:1px solid var(--line);padding:15px;margin-top:7px}.order-detail{display:grid;grid-template-columns:1fr 300px;gap:25px}.order-detail>div{border:1px solid var(--line);padding:22px}.ordered-item{display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid var(--line)}.order-detail>aside{display:grid;gap:7px;height:max-content}.success{min-height:75vh;padding:145px 5vw 70px;display:flex;flex-direction:column;align-items:center;justify-content:center}.success>i{width:75px;height:75px;border:1px solid var(--gold);border-radius:50%;display:grid;place-items:center;color:var(--gold)}.success h1{font-family:var(--serif);font-weight:400;font-size:54px}.success>div{display:flex;gap:7px}
.auth-page{min-height:100vh;display:grid;grid-template-columns:1fr 1fr}.auth-art{background:radial-gradient(circle at 50% 45%,rgba(181,112,45,.4),transparent 25%),#0b0806;display:grid;place-items:center}.auth-panel{padding:120px 8vw 70px;display:flex;justify-content:center;flex-direction:column}.auth-panel h1{font-family:var(--serif);font-weight:400;font-size:52px}.auth-panel>p{color:var(--muted)}.profile-page{padding-top:140px;display:grid;grid-template-columns:310px 1fr;gap:25px}.profile-page>aside{border:1px solid var(--line);padding:28px;text-align:center}.avatar{width:90px;height:90px;border-radius:50%;margin:auto;border:1px solid var(--gold);display:grid;place-items:center;overflow:hidden}.avatar img{width:100%;height:100%;object-fit:cover}.profile-links{display:grid;grid-template-columns:1fr 1fr;gap:8px}.profile-links a{border:1px solid var(--line);padding:25px}.customer-layout{display:grid;grid-template-columns:1fr 300px;gap:30px}.service-card{display:grid;grid-template-columns:45px 1fr;gap:15px;border-bottom:1px solid var(--line);padding:20px 0}.service-card>span{font-family:var(--serif);font-size:25px;color:var(--gold)}.service-card p,.service-card li{color:var(--muted)}.customer-layout>aside{border:1px solid var(--line);padding:20px;height:max-content}.care-row{display:grid;grid-template-columns:130px 1fr 100px;border:1px solid var(--line);padding:15px;margin:6px 0}.form-page{max-width:950px;display:grid;grid-template-columns:.8fr 1.2fr;gap:40px;padding-top:140px}.form-page.centered{grid-template-columns:1fr;max-width:650px}.form-page h1{font-family:var(--serif);font-weight:400;font-size:45px}.conversation{max-width:800px;padding-top:120px}.conversation article{border:1px solid var(--line);padding:15px;margin-bottom:7px}
footer{border-top:1px solid var(--line);padding:50px 4.5vw 18px;background:var(--panel)}.footer-grid{max-width:1500px;margin:auto;display:grid;grid-template-columns:1.4fr repeat(3,.7fr);gap:35px}.footer-grid>div:not(:first-child){display:flex;flex-direction:column;gap:6px}.footer-grid h4{font-family:var(--serif);font-weight:400}.footer-grid p,.footer-grid a{color:var(--muted);font-size:9px}.footer-bottom{max-width:1500px;margin:35px auto 0;border-top:1px solid var(--line);padding-top:15px;display:flex;justify-content:space-between;color:var(--muted);font-size:7px}
@media(max-width:1100px){.lux-header{grid-template-columns:200px 1fr 180px}.lux-header>nav{gap:16px}.hero{grid-template-columns:1fr 1.1fr}.hero-features{display:none}.signature{grid-template-columns:220px 1fr}.signature-grid{grid-template-columns:repeat(3,1fr)}.signature-grid>*:nth-child(4){display:none}.finder{grid-template-columns:.8fr 1fr}.note-deck{display:none}.footer-grid{grid-template-columns:1.3fr repeat(3,.7fr)}}
@media(max-width:850px){.lux-header{height:74px;grid-template-columns:1fr auto;padding:0 20px}.lux-header>nav{display:none}.hamb{display:grid!important}.hero{height:auto;min-height:830px;padding:100px 20px 40px;display:flex;flex-direction:column}.hero-stage{order:0;width:100%;height:400px}.hero-copy{order:1}.ribbon{grid-template-columns:1fr 1fr}.signature{grid-template-columns:1fr;padding:50px 20px}.signature-grid{grid-template-columns:1fr 1fr}.finder{grid-template-columns:1fr}.finder-art{height:240px}.finder-copy{padding:40px 20px}.editorial{grid-template-columns:1fr}.craft{grid-template-columns:1fr}.craft-art{height:280px}.collection-section,.reviews{padding:50px 20px}.product-grid.four,.product-grid.three{grid-template-columns:1fr 1fr}.page-hero{padding:115px 20px 40px}.catalog{display:block;padding:25px 20px 55px}.filters{position:fixed;z-index:160;top:0;bottom:0;right:0;width:min(340px,90vw);background:var(--panel);padding:65px 20px;transform:translateX(105%);transition:.3s;overflow:auto}.filters.open{transform:none}.filter-close{display:block;position:absolute;left:15px;top:15px;background:none;border:0;font-size:30px}.catalog-toolbar>button{display:block}.detail-page{padding:100px 20px 50px}.detail-grid{grid-template-columns:1fr}.detail-media{height:500px}.detail-story{grid-template-columns:1fr;padding:45px 20px}.review-grid{grid-template-columns:1fr}.cart-layout,.checkout-layout,.order-detail,.profile-page,.customer-layout,.form-page{display:block;padding:30px 20px 55px}.summary{margin-top:25px}.auth-page{grid-template-columns:1fr;padding-top:74px}.auth-art{display:none}.auth-panel{min-height:calc(100vh - 74px);padding:50px 20px}.profile-page{padding-top:105px}.profile-links{margin-top:20px}.footer-grid{grid-template-columns:1fr 1fr}.footer-grid>div:first-child{grid-column:1/-1}}
@media(max-width:520px){.hero-copy h1 span{font-size:48px}.hero-copy h1 em{font-size:40px}.ribbon{grid-template-columns:1fr}.signature-grid,.product-grid.four,.product-grid.three{grid-template-columns:1fr}.product-media{height:380px}.notes{grid-template-columns:1fr}.buy-row{flex-direction:column}.guarantees{grid-template-columns:1fr}.cart-item{grid-template-columns:80px 1fr}.order-row{grid-template-columns:1fr}.profile-links{grid-template-columns:1fr}.footer-grid{grid-template-columns:1fr}.footer-grid>div:first-child{grid-column:auto}}
'''

FILES["static/js/perfume-luxury.js"] = r'''
(() => {
 const root=document.documentElement;
 const setTheme=t=>{root.dataset.perfumeTheme=t;try{localStorage.setItem("perfume-luxury-theme",t)}catch(e){}};
 document.addEventListener("click",e=>{
  if(e.target.closest("[data-theme-toggle]")){setTheme(root.dataset.perfumeTheme==="night"?"day":"night");return}
  if(e.target.closest("[data-menu-open]")){document.querySelector("[data-menu]")?.classList.add("open");document.body.style.overflow="hidden";return}
  if(e.target.closest("[data-menu-close]")){document.querySelector("[data-menu]")?.classList.remove("open");document.body.style.overflow="";return}
  if(e.target.closest("[data-search-open]")){document.querySelector("[data-search]")?.classList.add("open");document.body.style.overflow="hidden";return}
  if(e.target.closest("[data-search-close]")){document.querySelector("[data-search]")?.classList.remove("open");document.body.style.overflow="";return}
  if(e.target.closest("[data-filter-open]")){document.querySelector("[data-filters]")?.classList.add("open");return}
  if(e.target.closest("[data-filter-close]")){document.querySelector("[data-filters]")?.classList.remove("open");return}
  if(e.target.closest("[data-toast-close]")){e.target.closest(".toasts>div")?.remove();return}
  const th=e.target.closest("[data-image]");if(th){const m=document.getElementById("detailMainImage");if(m)m.src=th.dataset.image;return}
  const v=e.target.closest("[data-variant]");if(v){document.querySelectorAll("[data-variant]").forEach(x=>x.classList.remove("selected"));v.classList.add("selected");const i=document.getElementById("variantInput"),p=document.getElementById("detailPrice"),m=document.getElementById("detailMainImage"),q=document.getElementById("qty");if(i)i.value=v.dataset.variant||"";if(p)p.textContent=new Intl.NumberFormat("fa-IR").format(Number(v.dataset.price||0));if(m&&v.dataset.vimage)m.src=v.dataset.vimage;if(q)q.max=Math.max(1,Number(v.dataset.stock||1));return}
  if(e.target.closest("[data-minus]")){const q=document.getElementById("qty");if(q)q.value=Math.max(1,Number(q.value||1)-1);return}
  if(e.target.closest("[data-plus]")){const q=document.getElementById("qty");if(q)q.value=Math.min(Number(q.max||9999),Number(q.value||1)+1)}
 });
 document.addEventListener("change",e=>{const s=e.target.closest("[data-sort]");if(!s)return;const u=new URL(location.href);u.searchParams.set("sort",s.value);u.searchParams.delete("page");location.href=u});
 document.addEventListener("keydown",e=>{if(e.key!=="Escape")return;document.querySelector("[data-menu]")?.classList.remove("open");document.querySelector("[data-search]")?.classList.remove("open");document.querySelector("[data-filters]")?.classList.remove("open");document.body.style.overflow=""});
 const h=document.querySelector("[data-header]");const sh=()=>h?.classList.toggle("scrolled",scrollY>18);sh();addEventListener("scroll",sh,{passive:true});
 document.querySelector("[data-variant]")?.click();
 if("IntersectionObserver" in window){const els=document.querySelectorAll(".reveal");els.forEach(x=>{x.style.opacity="0";x.style.transform="translateY(16px)";x.style.transition="opacity .55s, transform .55s"});const io=new IntersectionObserver(es=>es.forEach(en=>{if(en.isIntersecting){en.target.style.opacity="1";en.target.style.transform="translateY(0)";io.unobserve(en.target)}}),{threshold:.08});els.forEach(x=>io.observe(x))}
})();
'''

def main():
    print("="*70)
    print(" PERFUME SHOP — COMPLETE LUXURY FRONTEND REBUILD")
    print("="*70)

    if not (ROOT/"manage.py").exists():
        raise SystemExit("Put this file beside manage.py inside perfume-shop.")

    backend = [
        "first/views.py","first/models.py","first/urls.py","first/forms.py",
        "first/context_processors.py","customer_care/views.py",
        "customer_care/models.py","customer_care/urls.py",
    ]
    snap = {p:(ROOT/p).read_bytes() for p in backend if (ROOT/p).exists()}

    if BACKUP.exists():
        raise SystemExit(f"Backup already exists: {BACKUP}\nRename/delete it only if you intentionally want to rerun.")

    BACKUP.mkdir()
    written=[]
    try:
        for rel,content in FILES.items():
            write(rel,content);written.append(rel)

        for rel,data in snap.items():
            if (ROOT/rel).read_bytes()!=data:
                raise RuntimeError("Backend changed unexpectedly: "+rel)

        run([sys.executable,"manage.py","check"])
        run([sys.executable,"manage.py","makemigrations","--check","--dry-run"])
        run([sys.executable,"manage.py","test"])
    except Exception as exc:
        print("\n[ROLLBACK]",exc)
        for rel in written:
            dst=ROOT/rel
            src=BACKUP/rel
            if src.exists():
                dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
            elif dst.exists():
                dst.unlink()
        raise

    print("\n"+"="*70)
    print(" PERFUME FRONTEND REBUILD COMPLETE")
    print("="*70)
    print("Frontend changed. Backend verified byte-for-byte unchanged.")
    print("Run: python manage.py runserver")
    print("Do not commit until browser smoke is OK.")

if __name__=="__main__":
    main()
