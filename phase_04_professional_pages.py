#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / '.perfume_frontend_phase04_backup'

BASE = ROOT / 'first/templates/perfume_base.html'
CARD = ROOT / 'first/templates/includes/p4_product_card.html'
CSS = ROOT / 'static/css/perfume-phase04.css'
JS = ROOT / 'static/js/perfume-phase04.js'

BACKEND = [
    'first/views.py','first/models.py','first/urls.py','first/forms.py',
    'first/context_processors.py','customer_care/views.py',
    'customer_care/models.py','customer_care/urls.py',
]


def run(*args):
    print('\n> ' + ' '.join(map(str, args)))
    p = subprocess.run(list(args), cwd=ROOT, text=True)
    if p.returncode:
        raise RuntimeError('Command failed: ' + ' '.join(map(str, args)))


def backup(path: Path):
    if not path.exists():
        return
    dst = BACKUP / path.relative_to(ROOT)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)


def write(path: Path, content: str):
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding='utf-8')
    print('[WRITE]', path.relative_to(ROOT).as_posix())


def discover(view_name: str, candidates: list[str], needles: list[str]) -> Path | None:
    views = ROOT / 'first/views.py'
    if views.exists():
        src = views.read_text(encoding='utf-8', errors='ignore')
        m = re.search(rf'(?ms)^def\s+{re.escape(view_name)}\s*\([^)]*\)\s*:.*?(?=^def\s+\w+\s*\(|\Z)', src)
        if m:
            r = re.search(r'''render\s*\(\s*request\s*,\s*['\"]([^'\"]+\.html)['\"]''', m.group(0))
            if r:
                p = ROOT / 'first/templates' / r.group(1)
                if p.exists():
                    return p
    for rel in candidates:
        p = ROOT / rel
        if p.exists():
            return p
    root = ROOT / 'first/templates'
    if root.exists():
        for p in root.rglob('*.html'):
            try:
                txt = p.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            if any(n in txt for n in needles):
                return p
    return None


BASE_TEMPLATE = r'''
{% load static %}
<!doctype html>
<html lang="fa" dir="rtl" data-perfume-theme="night">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#090706">
<title>{% block title %}{{ settings.site_title|default:'فروشگاه عطر' }}{% endblock %}</title>
{% if settings.favicon %}<link rel="icon" href="{{ settings.favicon.url }}">{% endif %}
<script>
try{const t=localStorage.getItem('velora-theme');document.documentElement.dataset.perfumeTheme=(t==='day'||t==='night')?t:'night'}catch(e){}
</script>
<link rel="stylesheet" href="{% static 'vendor/vazir/font-face.css' %}">
<link rel="stylesheet" href="{% static 'vendor/fontawesome/css/all.min.css' %}">
<link rel="stylesheet" href="{% static 'css/perfume-phase01.css' %}">
<link rel="stylesheet" href="{% static 'css/perfume-global-compat.css' %}">
<link rel="stylesheet" href="{% static 'css/perfume-phase03-final.css' %}">
<link rel="stylesheet" href="{% static 'css/perfume-phase04.css' %}">
{% block extra_css %}{% endblock %}
</head>
<body class="velora-body">
<div class="p4-progress" data-p4-progress></div>

<div class="p4-top-strip">
  <div class="p4-wrap p4-top-strip-inner">
    <span><i class="fa-solid fa-truck-fast"></i> ارسال مطمئن و بسته‌بندی حرفه‌ای</span>
    <span><i class="fa-solid fa-shield-halved"></i> تضمین اصالت کالا</span>
    <span><i class="fa-regular fa-gem"></i> مشاوره انتخاب رایحه</span>
  </div>
</div>

<header class="p4-header">
  <div class="p4-wrap">
    <div class="p4-mainbar">
      <a class="p4-brand" href="{% url 'first:home' %}">
        <span class="p4-brand-mark">{% if settings.logo %}<img src="{{ settings.logo.url }}" alt="{{ settings.site_name }}">{% else %}V{% endif %}</span>
        <span class="p4-brand-copy"><strong>{{ settings.site_name|default:'فروشگاه عطر' }}</strong><small>MAISON DE PARFUM</small></span>
      </a>

      <form class="p4-search" method="get" action="{% url 'first:search_products' %}">
        <button type="submit" aria-label="جستجو"><i class="fa-solid fa-magnifying-glass"></i></button>
        <input type="search" name="q" value="{{ request.GET.q|default:'' }}" placeholder="نام عطر، برند، رایحه یا نت موردنظر را جستجو کنید..." autocomplete="off">
        <span>SEARCH</span>
      </form>

      <div class="p4-actions">
        <button type="button" class="p4-icon" data-theme-toggle title="حالت روز و شب"><i class="fa-regular fa-moon night-i"></i><i class="fa-regular fa-sun day-i"></i></button>
        {% if user.is_authenticated %}<a class="p4-icon" href="{% url 'first:profile' %}" title="حساب"><i class="fa-regular fa-user"></i></a>{% else %}<a class="p4-icon" href="{% url 'first:login' %}" title="ورود"><i class="fa-regular fa-user"></i></a>{% endif %}
        <a class="p4-icon" href="{% url 'first:wishlist' %}" title="علاقه‌مندی‌ها"><i class="fa-regular fa-heart"></i></a>
        <a class="p4-cart" href="{% url 'first:cart' %}"><i class="fa-solid fa-bag-shopping"></i><span>سبد خرید</span></a>
        <button type="button" class="p4-menu-button" data-p4-menu-open><span></span><span></span></button>
      </div>
    </div>

    <div class="p4-navrow">
      <nav class="p4-nav">
        <a href="{% url 'first:home' %}">خانه</a>
        <a href="{% url 'first:product_list' %}">همه عطرها</a>
        <a href="{% url 'first:best_sellers' %}">پرفروش‌ترین‌ها</a>
        <a href="{% url 'first:discounts' %}">تخفیف‌های ویژه</a>
        <a href="{% url 'first:customer_service' 'shopping-guide' %}">راهنمای خرید</a>
        <a href="{% url 'customer_care:order_tracking' %}">پیگیری سفارش</a>
      </nav>
      <a class="p4-support" href="{% url 'customer_care:support_home' %}"><i class="fa-solid fa-headset"></i><span>پشتیبانی</span></a>
    </div>
  </div>
</header>

<aside class="p4-drawer" data-p4-menu>
  <div class="p4-drawer-head"><div><strong>{{ settings.site_name|default:'فروشگاه عطر' }}</strong><small>MAISON DE PARFUM</small></div><button type="button" data-p4-menu-close>×</button></div>
  <nav>
    <a href="{% url 'first:home' %}"><span>01</span>خانه</a>
    <a href="{% url 'first:product_list' %}"><span>02</span>همه عطرها</a>
    <a href="{% url 'first:best_sellers' %}"><span>03</span>پرفروش‌ترین‌ها</a>
    <a href="{% url 'first:discounts' %}"><span>04</span>تخفیف‌ها</a>
    <a href="{% url 'first:customer_service' 'shopping-guide' %}"><span>05</span>راهنمای خرید</a>
    <a href="{% url 'customer_care:order_tracking' %}"><span>06</span>پیگیری سفارش</a>
    {% if user.is_authenticated %}<a href="{% url 'first:profile' %}"><span>07</span>حساب کاربری</a>{% else %}<a href="{% url 'first:login' %}"><span>07</span>ورود / ثبت‌نام</a>{% endif %}
  </nav>
</aside>

{% if messages %}<div class="p4-toasts">{% for message in messages %}<div class="p4-toast"><span>{{ message }}</span><button type="button" data-p4-toast-close>×</button></div>{% endfor %}</div>{% endif %}

<main class="phase-main">{% block content %}{% endblock %}</main>

<footer class="p4-footer">
  <div class="p4-wrap p4-footer-grid">
    <div class="p4-footer-brand"><span>A HOUSE OF SCENT</span><h2>{{ settings.site_name|default:'فروشگاه عطر' }}</h2><p>رایحه‌ای که فقط انتخاب نمی‌شود؛ بخشی از هویت شما می‌شود.</p></div>
    <div class="p4-footer-links"><span>DISCOVER</span><a href="{% url 'first:product_list' %}">همه عطرها</a><a href="{% url 'first:best_sellers' %}">پرفروش‌ها</a><a href="{% url 'first:discounts' %}">تخفیف‌ها</a></div>
    <div class="p4-footer-links"><span>SERVICE</span><a href="{% url 'customer_care:support_home' %}">پشتیبانی</a><a href="{% url 'customer_care:order_tracking' %}">پیگیری سفارش</a><a href="{% url 'first:customer_service' 'shipping-returns' %}">ارسال و مرجوعی</a></div>
    <div class="p4-footer-note"><span>PRIVATE NOTES</span><p>خبر کالکشن‌های تازه و پیشنهادهای محدود.</p><div><input type="email" placeholder="ایمیل شما"><button type="button">←</button></div></div>
  </div>
  <div class="p4-wrap p4-footer-bottom"><span>{{ settings.footer_text|default:'© 2026 PERFUME HOUSE' }}</span><span>SCENT / MEMORY / IDENTITY</span></div>
</footer>

<script src="{% static 'js/perfume-phase01.js' %}"></script>
<script src="{% static 'js/perfume-phase03-final.js' %}"></script>
<script src="{% static 'js/perfume-phase04.js' %}"></script>
{% block extra_js %}{% endblock %}
</body>
</html>
'''

CARD_TEMPLATE = r'''
{% load custom_filters %}
<article class="p4-product-card">
  <a class="p4-product-media" href="{% url 'first:product_detail' product.slug %}">
    <div class="p4-product-badges">{% if product.is_new %}<span>NEW</span>{% endif %}{% if product.is_best_seller %}<span>ICON</span>{% endif %}{% if product.discount_percent %}<span class="sale">-{{ product.discount_percent|format_number }}%</span>{% endif %}</div>
    {% if product.main_image %}<img src="{{ product.main_image.url }}" alt="{{ product.name }}" loading="lazy">{% else %}<div class="p4-empty-bottle">V</div>{% endif %}
  </a>
  <div class="p4-product-info">
    <small>{{ product.brand.name|default:'PERFUME HOUSE' }}</small>
    <a class="p4-product-title" href="{% url 'first:product_detail' product.slug %}">{{ product.name }}</a>
    <div class="p4-product-bottom">
      <div class="p4-price"><strong>{{ product.final_price|price_format }}</strong><span>تومان</span>{% if product.discount_percent %}<del>{{ product.price|price_format }}</del>{% endif %}</div>
      {% if product.has_variants %}<a class="p4-round" href="{% url 'first:product_detail' product.slug %}"><i class="fa-solid fa-arrow-left"></i></a>{% else %}<form method="post" action="{% url 'first:add_to_cart' product.id %}">{% csrf_token %}<button class="p4-round" type="submit"><i class="fa-solid fa-bag-shopping"></i></button></form>{% endif %}
    </div>
  </div>
</article>
'''

PRODUCT_LIST = r'''
{% extends 'perfume_base.html' %}{% load custom_filters %}
{% block title %}کالکشن عطرها | {{ settings.site_name|default:'فروشگاه عطر' }}{% endblock %}
{% block content %}
<section class="p4-page-hero"><div class="p4-wrap p4-page-hero-grid"><div><span class="p4-kicker">THE PERFUME ARCHIVE</span><h1>کالکشن<br><em>عطرها</em></h1><p>رایحه‌های موجود را بر اساس دسته‌بندی، برند، قیمت و سبک انتخاب کنید.</p></div><div class="p4-stat"><span>AVAILABLE</span><strong>{{ page_obj.paginator.count|default:total_products|default:'0' }}</strong><small>محصول در آرشیو</small></div></div></section>

<section class="p4-wrap p4-shop-layout">
  <aside class="p4-filter" data-p4-filter>
    <div class="p4-filter-mobile-head"><strong>فیلتر محصولات</strong><button type="button" data-p4-filter-close>×</button></div>
    <div class="p4-filter-section"><span>دسته‌بندی</span><a href="{% url 'first:product_list' %}">همه محصولات</a>{% for category in categories %}{% if category.slug %}<a href="?category={{ category.slug }}">{{ category.name }}</a>{% endif %}{% endfor %}</div>
    <div class="p4-filter-section"><span>برند</span><a href="{% url 'first:product_list' %}">همه برندها</a>{% for brand in brands %}{% if brand.slug %}<a href="?brand={{ brand.slug }}">{{ brand.name }}</a>{% endif %}{% endfor %}</div>
    <form method="get" class="p4-filter-section"><span>محدوده قیمت</span>{% if request.GET.category %}<input type="hidden" name="category" value="{{ request.GET.category }}">{% endif %}{% if request.GET.brand %}<input type="hidden" name="brand" value="{{ request.GET.brand }}">{% endif %}<label>از<input type="number" name="min_price" value="{{ request.GET.min_price }}" placeholder="حداقل"></label><label>تا<input type="number" name="max_price" value="{{ request.GET.max_price }}" placeholder="حداکثر"></label><button type="submit">اعمال فیلتر <i class="fa-solid fa-sliders"></i></button></form>
  </aside>

  <div class="p4-products-area">
    <div class="p4-toolbar"><div><button class="p4-filter-open" type="button" data-p4-filter-open><i class="fa-solid fa-sliders"></i> فیلتر</button><span>{{ page_obj.paginator.count|default:total_products|default:'0' }} محصول</span></div><label>مرتب‌سازی<select data-p4-sort><option value="-created_at" {% if current_sort == '-created_at' %}selected{% endif %}>جدیدترین</option><option value="-sales_count" {% if current_sort == '-sales_count' %}selected{% endif %}>پرفروش‌ترین</option><option value="-rating" {% if current_sort == '-rating' %}selected{% endif %}>بالاترین امتیاز</option><option value="price" {% if current_sort == 'price' %}selected{% endif %}>قیمت کم به زیاد</option><option value="-price" {% if current_sort == '-price' %}selected{% endif %}>قیمت زیاد به کم</option></select></label></div>
    <div class="p4-grid">{% for product in page_obj %}{% include 'includes/p4_product_card.html' %}{% empty %}<div class="p4-empty"><div class="p4-empty-icon"><i class="fa-solid fa-spray-can-sparkles"></i></div><span>NO PRODUCTS FOUND</span><h2>هنوز محصولی در این بخش نیست.</h2><p>فیلترها را تغییر دهید یا همه عطرها را مشاهده کنید.</p><a href="{% url 'first:product_list' %}">پاک کردن فیلترها</a></div>{% endfor %}</div>
  </div>
</section>
{% endblock %}
'''

BEST = r'''
{% extends 'perfume_base.html' %}{% load custom_filters %}
{% block title %}پرفروش‌ترین عطرها | {{ settings.site_name|default:'فروشگاه عطر' }}{% endblock %}
{% block content %}
<section class="p4-feature-hero"><div class="p4-wrap p4-feature-inner"><div><span class="p4-kicker">MOST WANTED</span><h1>پرفروش‌ترین<br><em>عطرها</em></h1><p>انتخاب‌هایی که بیشترین استقبال را از طرف خریداران داشته‌اند.</p><a class="p4-outline" href="{% url 'first:product_list' %}">مشاهده همه کالکشن <i class="fa-solid fa-arrow-left"></i></a></div><div class="p4-feature-circle"><i class="fa-solid fa-crown"></i><b>BEST<br>SELLERS</b></div></div></section>
<section class="p4-wrap p4-listing"><div class="p4-listing-head"><div><span class="p4-kicker">CUSTOMER FAVORITES</span><h2>محبوب‌ترین انتخاب‌ها</h2></div><a href="{% url 'first:product_list' %}">همه محصولات ←</a></div><div class="p4-grid p4-grid-4">{% firstof products best_sellers page_obj as listing %}{% for product in listing %}{% include 'includes/p4_product_card.html' %}{% empty %}<div class="p4-empty"><div class="p4-empty-icon"><i class="fa-solid fa-crown"></i></div><span>BEST SELLERS</span><h2>هنوز محصول پرفروشی ثبت نشده.</h2><p>با ثبت سفارش‌ها، محبوب‌ترین محصولات اینجا نمایش داده می‌شوند.</p><a href="{% url 'first:product_list' %}">مشاهده همه عطرها</a></div>{% endfor %}</div></section>
{% endblock %}
'''

DISCOUNTS = r'''
{% extends 'perfume_base.html' %}{% load custom_filters %}
{% block title %}تخفیف‌های ویژه | {{ settings.site_name|default:'فروشگاه عطر' }}{% endblock %}
{% block content %}
<section class="p4-feature-hero"><div class="p4-wrap p4-feature-inner"><div><span class="p4-kicker">PRIVATE OFFERS</span><h1>تخفیف‌های<br><em>ویژه</em></h1><p>پیشنهادهای محدود و قیمت‌های ویژه برای عطرهای منتخب فروشگاه.</p><a class="p4-outline" href="{% url 'first:product_list' %}">مشاهده همه محصولات <i class="fa-solid fa-arrow-left"></i></a></div><div class="p4-feature-circle"><i class="fa-solid fa-tags"></i><b>PRIVATE<br>SALE</b></div></div></section>
<section class="p4-wrap p4-listing"><div class="p4-listing-head"><div><span class="p4-kicker">LIMITED EDIT</span><h2>پیشنهادهای امروز</h2></div><a href="{% url 'first:product_list' %}">همه محصولات ←</a></div><div class="p4-grid p4-grid-4">{% firstof products discounted_products page_obj as listing %}{% for product in listing %}{% include 'includes/p4_product_card.html' %}{% empty %}<div class="p4-empty"><div class="p4-empty-icon"><i class="fa-solid fa-tags"></i></div><span>NO ACTIVE OFFERS</span><h2>فعلاً تخفیف فعالی وجود ندارد.</h2><p>پیشنهادهای تازه در همین صفحه نمایش داده خواهند شد.</p><a href="{% url 'first:product_list' %}">مشاهده همه عطرها</a></div>{% endfor %}</div></section>
{% endblock %}
'''

SERVICE = r'''
{% extends 'perfume_base.html' %}
{% block title %}خدمات مشتریان | {{ settings.site_name|default:'فروشگاه عطر' }}{% endblock %}
{% block content %}
<section class="p4-service-hero"><div class="p4-wrap p4-page-hero-grid"><div><span class="p4-kicker">CLIENT SERVICE</span>{% if 'shopping-guide' in request.path %}<h1>راهنمای<br><em>خرید عطر</em></h1><p>از انتخاب محصول تا ثبت سفارش؛ مسیر خرید را ساده و شفاف کرده‌ایم.</p>{% elif 'shipping-returns' in request.path %}<h1>ارسال و<br><em>مرجوعی</em></h1><p>اطلاعات مربوط به ارسال، تحویل و شرایط بازگشت سفارش.</p>{% elif 'privacy' in request.path %}<h1>حریم<br><em>خصوصی</em></h1><p>نحوه نگهداری و استفاده از اطلاعات شما در فروشگاه.</p>{% elif 'terms' in request.path %}<h1>قوانین و<br><em>مقررات</em></h1><p>شرایط استفاده از فروشگاه و ثبت سفارش.</p>{% else %}<h1>خدمات<br><em>مشتریان</em></h1><p>پاسخ‌های واضح برای خریدی مطمئن‌تر و ساده‌تر.</p>{% endif %}</div><div class="p4-service-orbit"><div></div><i class="fa-regular fa-gem"></i></div></div></section>

<section class="p4-wrap p4-service-layout">
  <aside class="p4-service-menu"><span>SERVICE MENU</span><a href="{% url 'first:customer_service' 'shopping-guide' %}"><i class="fa-solid fa-bag-shopping"></i>راهنمای خرید</a><a href="{% url 'customer_care:order_tracking' %}"><i class="fa-solid fa-location-dot"></i>پیگیری سفارش</a><a href="{% url 'first:customer_service' 'shipping-returns' %}"><i class="fa-solid fa-truck-fast"></i>ارسال و مرجوعی</a><a href="{% url 'first:customer_service' 'terms' %}"><i class="fa-solid fa-file-signature"></i>قوانین و مقررات</a><a href="{% url 'first:customer_service' 'privacy' %}"><i class="fa-solid fa-shield-halved"></i>حریم خصوصی</a><a href="{% url 'customer_care:support_home' %}"><i class="fa-solid fa-headset"></i>پشتیبانی</a></aside>
  <article class="p4-service-content">
    {% if 'shopping-guide' in request.path %}<span class="p4-service-index">01</span><h2>چطور خرید کنیم؟</h2><p class="lead">خرید عطر در چهار مرحله انجام می‌شود.</p><div class="p4-steps"><section><b>01</b><div><h3>انتخاب محصول</h3><p>عطر موردنظر را از کالکشن، دسته‌بندی‌ها یا جستجو پیدا کنید و مشخصات آن را بررسی کنید.</p></div></section><section><b>02</b><div><h3>انتخاب تنوع</h3><p>اگر محصول حجم یا تنوع مختلف دارد، گزینه مناسب را در صفحه محصول انتخاب کنید.</p></div></section><section><b>03</b><div><h3>افزودن به سبد</h3><p>تعداد، قیمت و جزئیات را بررسی و محصول را به سبد خرید اضافه کنید.</p></div></section><section><b>04</b><div><h3>ثبت سفارش</h3><p>اطلاعات تحویل را تکمیل کنید و سفارش را نهایی کنید.</p></div></section></div>
    {% elif 'shipping-returns' in request.path %}<span class="p4-service-index">02</span><h2>ارسال و مرجوعی</h2><p class="lead">اطلاعات ارسال هر سفارش در زمان ثبت سفارش و صفحه پیگیری نمایش داده می‌شود.</p><div class="p4-info"><section><i class="fa-solid fa-box"></i><h3>بسته‌بندی امن</h3><p>محصولات عطر با بسته‌بندی مناسب برای حمل ارسال می‌شوند.</p></section><section><i class="fa-solid fa-truck-fast"></i><h3>پیگیری سفارش</h3><p>وضعیت سفارش را از بخش پیگیری سفارش مشاهده کنید.</p></section><section><i class="fa-solid fa-rotate-left"></i><h3>مرجوعی</h3><p>در صورت وجود شرایط قابل‌قبول برای بازگشت، با پشتیبانی هماهنگ کنید.</p></section></div>
    {% elif 'privacy' in request.path %}<span class="p4-service-index">03</span><h2>حریم خصوصی</h2><p class="lead">اطلاعات شما فقط برای ارائه خدمات فروشگاه و تکمیل فرایند سفارش استفاده می‌شود.</p><div class="p4-prose"><h3>اطلاعات حساب</h3><p>اطلاعات حساب برای مدیریت ورود، سفارش‌ها و ارتباطات مرتبط با خرید استفاده می‌شود.</p><h3>اطلاعات سفارش</h3><p>اطلاعات ضروری سفارش برای پردازش، تحویل و پشتیبانی نگهداری می‌شود.</p></div>
    {% elif 'terms' in request.path %}<span class="p4-service-index">04</span><h2>قوانین و مقررات</h2><p class="lead">ثبت سفارش به معنای پذیرش قوانین فروشگاه و اطلاعات نمایش‌داده‌شده در فرایند خرید است.</p><div class="p4-prose"><h3>ثبت سفارش</h3><p>کاربر مسئول صحت اطلاعات واردشده هنگام ثبت سفارش است.</p><h3>قیمت و موجودی</h3><p>قیمت و موجودی معتبر، اطلاعات نمایش‌داده‌شده در زمان نهایی‌سازی سفارش است.</p></div>
    {% else %}<span class="p4-service-index">00</span><h2>خدمات مشتریان</h2><p class="lead">برای راهنمای خرید، ارسال، پیگیری سفارش یا ارتباط با پشتیبانی از منوی کنار صفحه استفاده کنید.</p>{% endif %}
  </article>
</section>
{% endblock %}
'''

CSS_TEXT = r'''
:root{--p4-max:1560px}
*{box-sizing:border-box}html,body{margin:0;background:var(--p-bg)}body{color:var(--p-text);font-family:Vazir,Tahoma,Arial,sans-serif!important}a{color:inherit!important;text-decoration:none!important}button,input,textarea,select{font:inherit}.p4-wrap{width:min(var(--p4-max),calc(100% - 64px));margin:auto}.p4-progress{position:fixed;z-index:1000;top:0;left:0;width:0;height:2px;background:linear-gradient(90deg,var(--p-gold-deep),var(--p-gold-pale))}
.p4-top-strip{min-height:42px;display:flex;align-items:center;background:#090706;color:#e7d8c2;border-bottom:1px solid rgba(216,179,109,.16)}.p4-top-strip-inner{display:flex;justify-content:center;gap:54px}.p4-top-strip span{display:flex;align-items:center;gap:9px;font-size:11px}.p4-top-strip i{color:#d6aa61}
.p4-header{position:sticky;z-index:150;top:0;background:color-mix(in srgb,var(--p-bg) 94%,transparent);backdrop-filter:blur(24px);border-bottom:1px solid var(--p-line);box-shadow:0 16px 45px rgba(0,0,0,.05)}.p4-mainbar{min-height:112px;display:grid;grid-template-columns:310px minmax(380px,1fr) auto;gap:32px;align-items:center}.p4-brand{display:flex;align-items:center;gap:16px;width:max-content}.p4-brand-mark{width:68px;height:68px;display:grid;place-items:center;border:1px solid var(--p-line-strong);background:linear-gradient(145deg,var(--p-surface-2),var(--p-bg));color:var(--p-gold-pale);font-family:Georgia,serif!important;font-size:34px;overflow:hidden}.p4-brand-mark img{width:100%;height:100%;object-fit:contain;padding:6px}.p4-brand-copy{display:flex;flex-direction:column;line-height:1.2}.p4-brand-copy strong{font-size:25px;color:var(--p-gold-pale)}.p4-brand-copy small{margin-top:7px;direction:ltr;letter-spacing:.22em;color:var(--p-muted);font-size:8px}.p4-search{height:64px;display:grid;grid-template-columns:64px 1fr auto;align-items:center;border:1px solid var(--p-line);background:var(--p-surface)}.p4-search:focus-within{border-color:var(--p-line-strong);box-shadow:0 0 0 4px rgba(216,179,109,.05)}.p4-search button{width:64px;height:62px;border:0;border-left:1px solid var(--p-line);background:none;color:var(--p-gold);font-size:18px;cursor:pointer}.p4-search input{width:100%;height:62px;padding:0 18px;border:0!important;outline:none!important;background:transparent!important;color:var(--p-text)!important;box-shadow:none!important;font-size:14px}.p4-search>span{padding:0 18px;direction:ltr;color:var(--p-muted);letter-spacing:.18em;font-size:8px}.p4-actions{display:flex;align-items:center;gap:7px;direction:ltr}.p4-icon{width:50px;height:50px;display:grid;place-items:center;border:1px solid transparent;background:none;color:var(--p-text);font-size:19px;cursor:pointer}.p4-icon:hover{color:var(--p-gold);border-color:var(--p-line);background:var(--p-surface)}.p4-cart{height:50px;padding:0 18px;display:flex;align-items:center;gap:10px;border:1px solid var(--p-line-strong);font-size:12px}.p4-cart i{color:var(--p-gold)}.day-i{display:none}html[data-perfume-theme=day] .night-i{display:none}html[data-perfume-theme=day] .day-i{display:block}.p4-navrow{min-height:62px;display:flex;align-items:center;justify-content:space-between;gap:30px;border-top:1px solid var(--p-line)}.p4-nav{display:flex;align-items:center;gap:36px}.p4-nav a{position:relative;padding:20px 0;color:var(--p-muted)!important;font-size:13px;font-weight:500}.p4-nav a:hover{color:var(--p-gold)!important}.p4-support{display:flex;align-items:center;gap:9px;color:var(--p-muted)!important;font-size:12px}.p4-support i{color:var(--p-gold)}.p4-menu-button{display:none}
.p4-drawer{position:fixed;z-index:500;inset:0;padding:28px 7vw;background:#080605;color:#f6efe7;transform:translateX(105%);transition:.42s}.p4-drawer.open{transform:none}.p4-drawer-head{display:flex;justify-content:space-between}.p4-drawer-head strong{display:block;font-size:26px;color:#e1b96f}.p4-drawer-head small{color:#9f9486;letter-spacing:.2em}.p4-drawer-head button{border:0;background:none;color:#fff;font-size:42px}.p4-drawer nav{display:grid;margin-top:50px}.p4-drawer nav a{padding:14px 0;display:grid;grid-template-columns:45px 1fr;border-bottom:1px solid rgba(216,179,109,.18);color:#f7f0e7!important;font-size:28px}.p4-drawer nav span{color:#d8b36d;font-size:10px}.p4-toasts{position:fixed;z-index:550;top:230px;right:28px}.p4-toast{padding:14px 16px;border:1px solid var(--p-line);background:var(--p-surface);display:flex;gap:15px}.p4-toast button{border:0;background:none;color:var(--p-muted)}
.p4-page-hero,.p4-feature-hero,.p4-service-hero{border-bottom:1px solid var(--p-line);background:radial-gradient(circle at 76% 20%,rgba(180,119,52,.09),transparent 23%),var(--p-bg)}.p4-page-hero-grid{min-height:350px;padding:72px 0;display:grid;grid-template-columns:1fr 330px;gap:50px;align-items:end}.p4-kicker{display:block;direction:ltr;color:var(--p-gold);letter-spacing:.24em;font-size:10px;font-weight:700}.p4-page-hero h1,.p4-feature-hero h1,.p4-service-hero h1{margin:16px 0 18px!important;font-size:clamp(54px,6vw,96px)!important;line-height:.95!important;font-weight:700!important;letter-spacing:-.035em}.p4-page-hero h1 em,.p4-feature-hero h1 em,.p4-service-hero h1 em{color:var(--p-gold-pale);font-style:normal}.p4-page-hero p,.p4-feature-hero p,.p4-service-hero p{max-width:620px;color:var(--p-muted)!important;font-size:16px;line-height:2}.p4-stat{min-height:210px;padding:28px;border:1px solid var(--p-line);background:linear-gradient(145deg,var(--p-surface),var(--p-surface-2));display:flex;flex-direction:column;justify-content:flex-end}.p4-stat span{color:var(--p-gold);font-size:10px;letter-spacing:.18em}.p4-stat strong{margin:7px 0;font-size:72px;line-height:1}.p4-stat small{color:var(--p-muted)!important}
.p4-shop-layout{padding:46px 0 90px;display:grid;grid-template-columns:285px 1fr;gap:38px}.p4-filter{position:sticky;top:205px;align-self:start;padding:24px;border:1px solid var(--p-line);background:linear-gradient(145deg,var(--p-surface),var(--p-surface-2))}.p4-filter-mobile-head{display:none}.p4-filter-section{display:grid;gap:9px;padding-bottom:23px;margin-bottom:23px;border-bottom:1px solid var(--p-line)}.p4-filter-section:last-child{border-bottom:0;margin-bottom:0}.p4-filter-section>span{color:var(--p-gold);font-size:11px;font-weight:700}.p4-filter-section>a{padding:9px 11px;color:var(--p-muted)!important;border:1px solid transparent;font-size:12px}.p4-filter-section>a:hover{color:var(--p-text)!important;border-color:var(--p-line);background:rgba(216,179,109,.035)}.p4-filter-section label{display:grid;grid-template-columns:28px 1fr;align-items:center;gap:8px;color:var(--p-muted);font-size:11px}.p4-filter-section input{height:44px;padding:0 10px;border:1px solid var(--p-line)!important;background:var(--p-bg)!important;color:var(--p-text)!important}.p4-filter-section button{min-height:46px;margin-top:5px;padding:0 15px;border:0;display:flex;align-items:center;justify-content:space-between;background:linear-gradient(120deg,var(--p-gold-pale),var(--p-gold-deep));color:#171008}.p4-toolbar{min-height:60px;margin-bottom:18px;padding:0 16px;display:flex;justify-content:space-between;align-items:center;border:1px solid var(--p-line);background:var(--p-surface)}.p4-toolbar>div{display:flex;align-items:center;gap:14px;color:var(--p-muted);font-size:12px}.p4-filter-open{display:none}.p4-toolbar label{display:flex;align-items:center;gap:12px;color:var(--p-muted);font-size:12px}.p4-toolbar select{min-width:175px;height:40px;padding:0 10px;border:1px solid var(--p-line);background:var(--p-bg);color:var(--p-text)}
.p4-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.p4-grid-4{grid-template-columns:repeat(4,1fr)}.p4-product-card{overflow:hidden;border:1px solid var(--p-line);background:linear-gradient(145deg,var(--p-surface),var(--p-surface-2));transition:.3s}.p4-product-card:hover{transform:translateY(-6px);border-color:var(--p-line-strong);box-shadow:0 25px 70px rgba(0,0,0,.15)}.p4-product-media{height:360px;position:relative;display:grid;place-items:center;overflow:hidden;background:radial-gradient(circle at 50% 74%,rgba(157,91,34,.17),transparent 42%)}.p4-product-media img{width:100%;height:100%;object-fit:contain;padding:28px;transition:.4s}.p4-product-card:hover img{transform:scale(1.045) translateY(-4px)}.p4-product-badges{position:absolute;z-index:3;top:12px;right:12px;display:flex;gap:5px}.p4-product-badges span{padding:4px 8px;background:var(--p-gold-pale);color:#171008;font-size:8px}.p4-product-badges .sale{background:#7e312b;color:#fff}.p4-empty-bottle{width:82px;height:150px;border:1px solid var(--p-gold);display:grid;place-items:center;color:var(--p-gold);font-family:Georgia,serif!important;font-size:28px}.p4-product-info{padding:17px}.p4-product-info>small{display:block;color:var(--p-gold)!important;font-size:9px}.p4-product-title{display:block;margin-top:3px;color:var(--p-text)!important;font-size:16px;font-weight:600}.p4-product-bottom{margin-top:18px;display:flex;justify-content:space-between;align-items:end;gap:12px}.p4-price strong{display:block;font-size:13px}.p4-price span,.p4-price del{color:var(--p-muted);font-size:9px}.p4-price del{display:block}.p4-round{width:42px;height:42px;border:1px solid var(--p-line);border-radius:50%;background:none;color:var(--p-text);display:grid;place-items:center}.p4-empty{grid-column:1/-1;min-height:440px;padding:70px 30px;border:1px solid var(--p-line);background:linear-gradient(145deg,var(--p-surface),var(--p-surface-2));display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}.p4-empty-icon{width:76px;height:76px;margin-bottom:18px;border:1px solid var(--p-line-strong);border-radius:50%;display:grid;place-items:center;color:var(--p-gold);font-size:26px}.p4-empty>span{color:var(--p-gold);letter-spacing:.18em;font-size:9px}.p4-empty h2{margin:10px 0 7px!important;font-size:30px!important}.p4-empty p{color:var(--p-muted)!important}.p4-empty a{min-height:46px;margin-top:17px;padding:0 20px;border:1px solid var(--p-line-strong);display:inline-flex;align-items:center}
.p4-feature-inner{min-height:420px;padding:72px 0;display:grid;grid-template-columns:1fr 340px;align-items:center;gap:50px}.p4-outline{min-height:50px;margin-top:15px;padding:0 22px;display:inline-flex;align-items:center;gap:10px;border:1px solid var(--p-line-strong)}.p4-feature-circle{aspect-ratio:1;border:1px solid var(--p-line);border-radius:50%;display:grid;place-items:center;text-align:center;background:radial-gradient(circle,rgba(216,179,109,.11),transparent 64%)}.p4-feature-circle i{display:block;margin-bottom:12px;color:var(--p-gold);font-size:42px}.p4-feature-circle b{color:var(--p-gold-pale);font-size:24px;letter-spacing:.06em}.p4-listing{padding:74px 0 95px}.p4-listing-head{margin-bottom:30px;display:flex;justify-content:space-between;align-items:end;gap:30px}.p4-listing-head h2{margin:8px 0 0!important;font-size:44px!important}.p4-listing-head>a{color:var(--p-gold)!important;font-size:12px}
.p4-service-orbit{height:250px;position:relative;display:grid;place-items:center}.p4-service-orbit>div{position:absolute;width:230px;height:100px;border:1px solid var(--p-line-strong);border-radius:50%;transform:rotate(-18deg)}.p4-service-orbit:before{content:"";position:absolute;width:110px;height:200px;border:1px solid var(--p-line);border-radius:50%;transform:rotate(34deg)}.p4-service-orbit i{position:relative;z-index:2;width:80px;height:80px;border:1px solid var(--p-line-strong);border-radius:50%;background:var(--p-surface);display:grid;place-items:center;color:var(--p-gold);font-size:27px}.p4-service-layout{padding:50px 0 95px;display:grid;grid-template-columns:280px 1fr;gap:38px}.p4-service-menu{position:sticky;top:205px;align-self:start;padding:20px;border:1px solid var(--p-line);background:var(--p-surface);display:grid;gap:7px}.p4-service-menu>span{padding:0 10px 10px;color:var(--p-gold);letter-spacing:.18em;font-size:9px}.p4-service-menu a{min-height:48px;padding:0 12px;display:flex;align-items:center;gap:11px;border:1px solid transparent;color:var(--p-muted)!important;font-size:12px}.p4-service-menu a:hover{color:var(--p-text)!important;border-color:var(--p-line);background:rgba(216,179,109,.035)}.p4-service-menu i{color:var(--p-gold)}.p4-service-content{min-height:650px;padding:50px;border:1px solid var(--p-line);background:linear-gradient(145deg,var(--p-surface),var(--p-surface-2))}.p4-service-index{display:block;color:var(--p-gold);font-size:12px}.p4-service-content>h2{margin:12px 0 10px!important;font-size:46px!important}.p4-service-content .lead{color:var(--p-muted)!important;font-size:16px}.p4-steps{margin-top:35px;display:grid;gap:11px}.p4-steps section{padding:22px;display:grid;grid-template-columns:65px 1fr;gap:18px;border:1px solid var(--p-line)}.p4-steps section>b{color:var(--p-gold);font-size:24px}.p4-steps h3,.p4-info h3,.p4-prose h3{margin:0 0 6px!important;font-size:20px!important}.p4-steps p,.p4-info p,.p4-prose p{margin:0;color:var(--p-muted)!important;line-height:2}.p4-info{margin-top:32px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.p4-info section{padding:26px;border:1px solid var(--p-line)}.p4-info i{margin-bottom:18px;color:var(--p-gold);font-size:25px}.p4-prose{margin-top:30px;display:grid;gap:22px}
.p4-footer{border-top:1px solid var(--p-line);background:var(--p-surface);padding:68px 0 20px}.p4-footer-grid{display:grid;grid-template-columns:1.35fr .7fr .7fr 1.1fr;gap:48px}.p4-footer-brand>span,.p4-footer-links>span,.p4-footer-note>span{color:var(--p-gold);letter-spacing:.18em;font-size:9px}.p4-footer-brand h2{margin:8px 0!important;font-size:45px!important}.p4-footer-brand p,.p4-footer-note p{color:var(--p-muted)!important}.p4-footer-links{display:flex;flex-direction:column;gap:10px}.p4-footer-links a{color:var(--p-muted)!important;font-size:12px}.p4-footer-note>div{height:48px;margin-top:14px;display:flex;border:1px solid var(--p-line)}.p4-footer-note input{flex:1;min-width:0;border:0!important;background:none!important;color:var(--p-text)!important;padding:0 12px}.p4-footer-note button{width:50px;border:0;border-right:1px solid var(--p-line);background:none;color:var(--p-gold)}.p4-footer-bottom{margin-top:42px;padding-top:17px;border-top:1px solid var(--p-line);display:flex;justify-content:space-between;color:var(--p-muted);font-size:9px}
@media(max-width:1250px){.p4-mainbar{grid-template-columns:260px minmax(280px,1fr) auto;gap:20px}.p4-nav{gap:22px}.p4-grid-4{grid-template-columns:repeat(3,1fr)}}
@media(max-width:980px){.p4-wrap{width:min(100% - 36px,var(--p4-max))}.p4-mainbar{grid-template-columns:1fr auto;min-height:86px}.p4-search{grid-column:1/-1;grid-row:2;margin-bottom:16px}.p4-actions{grid-column:2;grid-row:1}.p4-navrow{display:none}.p4-menu-button{width:46px;height:46px;border:0;background:none;display:grid;place-items:center;color:var(--p-text)}.p4-menu-button span{width:21px;height:1px;margin:2px 0;background:currentColor}.p4-top-strip-inner{gap:22px}.p4-page-hero-grid,.p4-feature-inner{grid-template-columns:1fr}.p4-stat,.p4-feature-circle,.p4-service-orbit{display:none}.p4-shop-layout,.p4-service-layout{grid-template-columns:1fr}.p4-filter{position:fixed;z-index:400;top:0;right:0;bottom:0;width:min(360px,92vw);overflow:auto;transform:translateX(105%);transition:.3s}.p4-filter.open{transform:none}.p4-filter-mobile-head{display:flex;justify-content:space-between}.p4-filter-open{display:flex;align-items:center;gap:8px;border:1px solid var(--p-line);background:none;color:var(--p-text);padding:8px 12px}.p4-grid,.p4-grid-4{grid-template-columns:repeat(2,1fr)}.p4-info{grid-template-columns:1fr}.p4-footer-grid{grid-template-columns:1fr 1fr}.p4-footer-brand{grid-column:1/-1}.p4-service-menu{position:static}}
@media(max-width:650px){.p4-top-strip{display:none}.p4-wrap{width:min(100% - 28px,var(--p4-max))}.p4-brand-mark{width:52px;height:52px}.p4-brand-copy strong{font-size:19px}.p4-brand-copy small{font-size:6px}.p4-cart span{display:none}.p4-cart{width:48px;padding:0;justify-content:center}.p4-search>span{display:none}.p4-page-hero-grid,.p4-feature-inner{min-height:auto;padding:48px 0}.p4-page-hero h1,.p4-feature-hero h1,.p4-service-hero h1{font-size:52px!important}.p4-toolbar{align-items:flex-start;flex-direction:column;padding:12px}.p4-toolbar label{width:100%;justify-content:space-between}.p4-grid,.p4-grid-4{grid-template-columns:1fr}.p4-product-media{height:410px}.p4-service-content{padding:28px 20px}.p4-steps section{grid-template-columns:45px 1fr;padding:18px}.p4-footer-grid{grid-template-columns:1fr}.p4-footer-brand{grid-column:auto}.p4-footer-bottom{flex-direction:column;gap:7px}}
'''

JS_TEXT = r'''
(() => {
  const $=(s,r=document)=>r.querySelector(s);
  document.addEventListener('click',e=>{
    if(e.target.closest('[data-p4-menu-open]')){$('[data-p4-menu]')?.classList.add('open');document.body.style.overflow='hidden';return}
    if(e.target.closest('[data-p4-menu-close]')){$('[data-p4-menu]')?.classList.remove('open');document.body.style.overflow='';return}
    if(e.target.closest('[data-p4-filter-open]')){$('[data-p4-filter]')?.classList.add('open');return}
    if(e.target.closest('[data-p4-filter-close]')){$('[data-p4-filter]')?.classList.remove('open');return}
    const t=e.target.closest('[data-p4-toast-close]');if(t)t.closest('.p4-toast')?.remove();
  });
  document.addEventListener('change',e=>{const s=e.target.closest('[data-p4-sort]');if(!s)return;const u=new URL(location.href);u.searchParams.set('sort',s.value);u.searchParams.delete('page');location.href=u});
  document.addEventListener('keydown',e=>{if(e.key!=='Escape')return;$('[data-p4-menu]')?.classList.remove('open');$('[data-p4-filter]')?.classList.remove('open');document.body.style.overflow=''});
  const p=$('[data-p4-progress]');function sync(){if(!p)return;const m=document.documentElement.scrollHeight-innerHeight;p.style.width=(m>0?(scrollY/m)*100:0)+'%'}sync();addEventListener('scroll',sync,{passive:true});
})();
'''


def main():
    print('='*80)
    print(' PHASE 04 — PROFESSIONAL STORE PAGES + HEADER FIX')
    print('='*80)

    if not (ROOT/'manage.py').exists():
        raise SystemExit('Put this script beside manage.py.')
    if not BASE.exists():
        raise SystemExit('perfume_base.html not found.')
    if BACKUP.exists():
        raise SystemExit(f'Backup already exists: {BACKUP}')

    BACKUP.mkdir(parents=True)
    snapshot = {rel:(ROOT/rel).read_bytes() for rel in BACKEND if (ROOT/rel).exists()}

    product = discover('product_list',['first/templates/products/product_list.html','first/templates/product_list.html'],['محصولات آرایشی','محدوده قیمت'])
    best = discover('best_sellers',['first/templates/products/best_sellers.html','first/templates/best_sellers.html'],['پرفروش‌ترین محصولات'])
    discounts = discover('discounts',['first/templates/products/discounts.html','first/templates/discounts.html'],['تخفیف‌های ویژه'])
    service = discover('customer_service',['first/templates/customer_service.html','first/templates/customer_service/customer_service.html'],['راهنمای خرید','خدمات مشتریان'])

    print('Templates:')
    print(' product  :', product)
    print(' best     :', best)
    print(' discounts:', discounts)
    print(' service  :', service)

    write(BASE, BASE_TEMPLATE)
    write(CARD, CARD_TEMPLATE)
    write(CSS, CSS_TEXT)
    write(JS, JS_TEXT)

    if product: write(product, PRODUCT_LIST)
    else: print('[WARN] product_list template not found')
    if best: write(best, BEST)
    else: print('[WARN] best_sellers template not found')
    if discounts: write(discounts, DISCOUNTS)
    else: print('[WARN] discounts template not found')
    if service: write(service, SERVICE)
    else: print('[WARN] customer_service template not found')

    for rel,data in snapshot.items():
        if (ROOT/rel).read_bytes()!=data:
            raise RuntimeError('Backend changed unexpectedly: '+rel)

    run(sys.executable,'manage.py','check')
    run(sys.executable,'manage.py','makemigrations','--check','--dry-run')

    print('\n'+'='*80)
    print(' PHASE 04 READY')
    print('='*80)
    print('✓ header rebuilt and larger')
    print('✓ links no longer use browser purple/default styling')
    print('✓ product list redesigned')
    print('✓ best sellers redesigned')
    print('✓ discounts redesigned')
    print('✓ guide/customer-service pages redesigned')
    print('✓ empty states designed')
    print('✓ backend unchanged')
    print('\nRun: python manage.py runserver')

if __name__=='__main__':
    main()
