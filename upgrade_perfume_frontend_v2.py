#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations
import shutil, subprocess, sys, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / ".perfume_frontend_backup_v2"
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
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#070605">
<title>{% block title %}{{ settings.site_title|default:"VÉLORA Parfums" }}{% endblock %}</title>
<script>
try{
  const t=localStorage.getItem("velora-theme");
  document.documentElement.dataset.perfumeTheme=(t==="day"||t==="night")?t:"night";
}catch(e){}
</script>
<link rel="stylesheet" href="{% static 'vendor/vazir/font-face.css' %}">
<link rel="stylesheet" href="{% static 'vendor/fontawesome/css/all.min.css' %}">
<link rel="stylesheet" href="{% static 'css/perfume-luxury-v2.css' %}">
{% block extra_css %}{% endblock %}
</head>
<body>
<div class="noise-layer"></div>
<div class="page-progress" data-progress></div>
<div class="custom-cursor" data-cursor></div>
<div class="custom-cursor-ring" data-cursor-ring></div>

<header class="v2-header" data-header>
  <div class="v2-header-shell">
    <a class="v2-brand" href="{% url 'first:home' %}">
      <span class="v2-brand-main">{{ settings.site_name|default:"VÉLORA" }}</span>
      <span class="v2-brand-sub">MAISON DE PARFUM · 2026</span>
    </a>

    <nav class="v2-nav">
      <a href="{% url 'first:home' %}"><span>01</span>خانه</a>
      <a href="{% url 'first:product_list' %}"><span>02</span>کالکشن</a>
      <a href="{% url 'first:best_sellers' %}"><span>03</span>پرفروش‌ها</a>
      <a href="{% url 'first:discounts' %}"><span>04</span>پیشنهادها</a>
      <a href="{% url 'first:customer_service' 'shopping-guide' %}"><span>05</span>راهنما</a>
    </nav>

    <div class="v2-actions">
      <button data-search-open aria-label="جستجو"><i class="fa-solid fa-magnifying-glass"></i></button>
      <button data-theme-toggle aria-label="تغییر تم">
        <i class="fa-regular fa-moon only-night"></i>
        <i class="fa-regular fa-sun only-day"></i>
      </button>
      {% if user.is_authenticated %}
      <a href="{% url 'first:profile' %}" aria-label="حساب"><i class="fa-regular fa-user"></i></a>
      {% else %}
      <a href="{% url 'first:login' %}" aria-label="ورود"><i class="fa-regular fa-user"></i></a>
      {% endif %}
      <a href="{% url 'first:cart' %}" aria-label="سبد"><i class="fa-solid fa-bag-shopping"></i></a>
      <button class="v2-menu-toggle" data-menu-open><span></span><span></span></button>
    </div>
  </div>
</header>

<aside class="v2-menu" data-menu>
  <div class="v2-menu-top"><span>VÉLORA / MENU</span><button data-menu-close>×</button></div>
  <nav>
    <a href="{% url 'first:home' %}"><small>01</small><strong>خانه</strong></a>
    <a href="{% url 'first:product_list' %}"><small>02</small><strong>کالکشن عطرها</strong></a>
    <a href="{% url 'first:best_sellers' %}"><small>03</small><strong>پرفروش‌ها</strong></a>
    <a href="{% url 'first:discounts' %}"><small>04</small><strong>پیشنهادهای ویژه</strong></a>
    <a href="{% url 'first:wishlist' %}"><small>05</small><strong>علاقه‌مندی‌ها</strong></a>
    {% if user.is_authenticated %}
    <a href="{% url 'first:user_orders' %}"><small>06</small><strong>سفارش‌های من</strong></a>
    <a href="{% url 'first:profile' %}"><small>07</small><strong>حساب کاربری</strong></a>
    {% else %}
    <a href="{% url 'first:login' %}"><small>06</small><strong>ورود</strong></a>
    <a href="{% url 'first:signup' %}"><small>07</small><strong>ثبت‌نام</strong></a>
    {% endif %}
  </nav>
</aside>

<div class="v2-search" data-search>
  <button class="v2-search-close" data-search-close>×</button>
  <div class="v2-search-inner">
    <span class="v2-eyebrow">SEARCH THE ARCHIVE</span>
    <h2>رایحه بعدی‌ات<br>را پیدا کن.</h2>
    <form method="get" action="{% url 'first:search_products' %}">
      <input name="q" type="search" placeholder="نام عطر، برند، نت یا حس..." autocomplete="off">
      <button type="submit"><span>SEARCH</span><i class="fa-solid fa-arrow-left"></i></button>
    </form>
    <div class="v2-search-hints">
      <a href="{% url 'first:search_products' %}?q=گرم">گرم</a>
      <a href="{% url 'first:search_products' %}?q=چوبی">چوبی</a>
      <a href="{% url 'first:search_products' %}?q=گلی">گلی</a>
      <a href="{% url 'first:search_products' %}?q=خنک">خنک</a>
    </div>
  </div>
</div>

{% if messages %}
<div class="v2-toasts">
  {% for message in messages %}
  <div class="v2-toast {{ message.tags }}"><span>{{ message }}</span><button data-toast-close>×</button></div>
  {% endfor %}
</div>
{% endif %}

<main>{% block content %}{% endblock %}</main>

<footer class="v2-footer">
  <div class="v2-footer-top">
    <div class="v2-footer-brand">
      <span class="v2-eyebrow">A HOUSE OF SCENT</span>
      <h2>{{ settings.site_name|default:"VÉLORA" }}</h2>
      <p>عطر برای ما یک محصول نیست؛ یک امضاست.</p>
    </div>
    <div class="v2-footer-links"><span>DISCOVER</span><a href="{% url 'first:product_list' %}">همه عطرها</a><a href="{% url 'first:best_sellers' %}">پرفروش‌ها</a><a href="{% url 'first:discounts' %}">پیشنهادهای ویژه</a></div>
    <div class="v2-footer-links"><span>SERVICE</span><a href="{% url 'customer_care:support_home' %}">پشتیبانی</a><a href="{% url 'customer_care:order_tracking' %}">پیگیری سفارش</a><a href="{% url 'first:customer_service' 'shipping-returns' %}">ارسال و مرجوعی</a></div>
    <div class="v2-footer-news"><span>PRIVATE NOTES</span><p>خبر کالکشن‌های تازه و پیشنهادهای محدود.</p><div><input type="email" placeholder="ایمیل شما"><button>←</button></div></div>
  </div>
  <div class="v2-footer-bottom"><span>{{ settings.footer_text|default:"© 2026 VÉLORA PARFUMS" }}</span><span>SCENT / MEMORY / IDENTITY</span></div>
</footer>

<script src="{% static 'js/perfume-luxury-v2.js' %}"></script>
{% block extra_js %}{% endblock %}
</body>
</html>
'''

FILES["first/templates/includes/perfume_product_card.html"] = r'''
{% load custom_filters %}
<article class="v2-product-card reveal">
  <a class="v2-product-visual" href="{% url 'first:product_detail' product.slug %}">
    <div class="v2-product-index">0{{ forloop.counter|default:1 }}</div>
    <div class="v2-badges">
      {% if product.is_new %}<span>NEW</span>{% endif %}
      {% if product.is_best_seller %}<span>ICON</span>{% endif %}
      {% if product.discount_percent %}<span class="sale">-{{ product.discount_percent|format_number }}%</span>{% endif %}
    </div>
    <div class="v2-card-glow"></div>
    {% if product.main_image %}
    <img src="{{ product.main_image.url }}" alt="{{ product.name }}" loading="lazy">
    {% else %}
    <div class="v2-placeholder-bottle"><span>V</span></div>
    {% endif %}
  </a>
  <div class="v2-product-info">
    <div>{% if product.brand %}<small>{{ product.brand.name }}</small>{% endif %}<a class="v2-product-name" href="{% url 'first:product_detail' product.slug %}">{{ product.name }}</a></div>
    <div class="v2-product-meta">
      <div><strong>{{ product.final_price|price_format }}</strong><span> تومان</span>{% if product.discount_percent %}<del>{{ product.price|price_format }}</del>{% endif %}</div>
      {% if product.has_variants %}
      <a class="v2-round-action" href="{% url 'first:product_detail' product.slug %}"><i class="fa-solid fa-arrow-left"></i></a>
      {% else %}
      <form method="post" action="{% url 'first:add_to_cart' product.id %}">{% csrf_token %}<button class="v2-round-action"><i class="fa-solid fa-bag-shopping"></i></button></form>
      {% endif %}
    </div>
  </div>
</article>
'''

FILES["first/templates/index.html"] = r'''
{% extends 'perfume_base.html' %}
{% load custom_filters %}
{% block title %}{{ settings.site_title|default:"VÉLORA — عطر فراتر از زمان" }}{% endblock %}
{% block content %}
{% firstof featured_products.0 best_sellers.0 new_products.0 as hero_product %}

<section class="v2-hero">
  {% for slider in sliders %}{% if forloop.first %}<img class="v2-hero-bg" src="{{ slider.image.url }}" alt="">{% endif %}{% endfor %}
  <div class="v2-hero-overlay"></div><div class="v2-hero-gridlines"></div><div class="v2-hero-arch"></div>

  <div class="v2-hero-left">
    <span class="v2-eyebrow">A HIGHER FORM OF BEAUTY</span>
    <h1><span>رایحه‌ای</span><em>فراتر از زمان</em></h1>
    <p>کالکشنی برای کسانی که می‌خواهند رایحه‌شان قبل از آن‌ها وارد شود و بعد از آن‌ها بماند.</p>
    <div class="v2-hero-actions">
      <a class="v2-btn v2-btn-gold" href="{% url 'first:product_list' %}"><span>کشف کالکشن</span><i class="fa-solid fa-arrow-left"></i></a>
      <a class="v2-btn v2-btn-link" href="#manifesto"><span class="v2-play"><i class="fa-solid fa-play"></i></span>داستان خانه عطر</a>
    </div>
    <div class="v2-hero-proof"><div class="v2-avatar-stack"><i></i><i></i><i></i><i></i></div><span>برای کسانی که عطر را بخشی از شخصیت می‌دانند</span></div>
  </div>

  <div class="v2-hero-center">
    <div class="v2-orbit o1"></div><div class="v2-orbit o2"></div><div class="v2-orbit o3"></div>
    <div class="v2-spark s1"></div><div class="v2-spark s2"></div><div class="v2-spark s3"></div>
    {% if hero_product and hero_product.main_image %}
    <a href="{% url 'first:product_detail' hero_product.slug %}" class="v2-hero-product"><img src="{{ hero_product.main_image.url }}" alt="{{ hero_product.name }}"></a>
    {% else %}
    <div class="v2-hero-bottle"><div class="cap"></div><div class="glass"><span>VÉLORA</span><small>ÉCLAT · EXTRAIT</small></div></div>
    {% endif %}
    <div class="v2-hero-label"><span>01 / SIGNATURE</span><strong>{% if hero_product %}{{ hero_product.name }}{% else %}ÉCLAT NOIR{% endif %}</strong></div>
  </div>

  <aside class="v2-hero-right">
    <div class="v2-mini-feature"><span>01</span><i class="fa-regular fa-gem"></i><div><b>ترکیب‌های منتخب</b><small>مواد اولیه باکیفیت</small></div></div>
    <div class="v2-mini-feature"><span>02</span><i class="fa-regular fa-clock"></i><div><b>حضور ماندگار</b><small>رایحه‌ای با امضای مشخص</small></div></div>
    <div class="v2-mini-feature"><span>03</span><i class="fa-regular fa-heart"></i><div><b>انتخاب شخصی</b><small>برای سبک و شخصیت شما</small></div></div>
  </aside>
  <div class="v2-scroll-note">SCROLL TO DISCOVER <span></span></div>
</section>

<section class="v2-ticker"><div><span>AUTHENTICITY</span><i>✦</i><span>EXTRAIT</span><i>✦</i><span>CRAFT</span><i>✦</i><span>MEMORY</span><i>✦</i><span>IDENTITY</span><i>✦</i><span>AUTHENTICITY</span><i>✦</i><span>EXTRAIT</span></div></section>

<section class="v2-icons-section" id="manifesto">
  <div class="v2-section-number">01</div>
  <div class="v2-section-head reveal">
    <div><span class="v2-eyebrow">OUR SIGNATURE COLLECTION</span><h2>آیکون‌ها،<br>در هر نت.</h2></div>
    <div><p>چهار شخصیت، چهار برداشت از حضور. از مینیمال و روشن تا تاریک، گرم و عمیق.</p><a href="{% url 'first:product_list' %}">مشاهده کالکشن کامل ←</a></div>
  </div>
  <div class="v2-featured-grid">
    {% for product in best_sellers|slice:":4" %}{% include 'includes/perfume_product_card.html' %}
    {% empty %}{% for product in featured_products|slice:":4" %}{% include 'includes/perfume_product_card.html' %}
    {% empty %}{% for product in new_products|slice:":4" %}{% include 'includes/perfume_product_card.html' %}{% endfor %}{% endfor %}{% endfor %}
  </div>
</section>

<section class="v2-editorial-split reveal">
  <div class="v2-split-art"><div class="v2-face-art"></div><div class="v2-art-copy">YOUR SCENT<br>ENTERS FIRST.</div><span class="v2-art-index">02</span></div>
  <div class="v2-split-copy">
    <span class="v2-eyebrow">PERFUME FINDER</span><h2>رایحه‌ات باید شبیه خودت باشد؛ نه شبیه بقیه.</h2><p>از حس شروع کن. روشن، چوبی، گلی یا گرم. مسیر انتخاب را کوتاه کرده‌ایم.</p>
    <div class="v2-scent-links">
      <a href="{% url 'first:search_products' %}?q=خنک"><span>01</span><b>FRESH</b><small>شفاف / مرکباتی</small></a>
      <a href="{% url 'first:search_products' %}?q=چوبی"><span>02</span><b>WOODY</b><small>خشک / عمیق</small></a>
      <a href="{% url 'first:search_products' %}?q=گلی"><span>03</span><b>FLORAL</b><small>نرم / روشن</small></a>
      <a href="{% url 'first:search_products' %}?q=گرم"><span>04</span><b>AMBER</b><small>گرم / شبانه</small></a>
    </div>
  </div>
</section>

<section class="v2-mosaic">
  <a class="v2-mosaic-card large" href="{% url 'first:product_list' %}?sort=-created_at"><span>NEW / 2026</span><h3>تازه‌رسیده‌ها</h3><p>رایحه‌هایی که تازه وارد آرشیو شده‌اند.</p><b>DISCOVER ↗</b><div class="v2-mosaic-bottle"></div></a>
  <a class="v2-mosaic-card dark" href="{% url 'first:best_sellers' %}"><span>ICONS</span><h3>پرفروش‌ترین‌ها</h3><b>VIEW EDIT ↗</b><div class="v2-mosaic-rings"></div></a>
  <a class="v2-mosaic-card warm" href="{% url 'first:product_list' %}"><span>GIFTING</span><h3>هدیه‌ای که<br>فراموش نمی‌شود.</h3><b>SELECT A GIFT ↗</b><div class="v2-gift-cube"></div></a>
</section>

<section class="v2-craft reveal">
  <div class="v2-craft-copy"><span class="v2-section-number inline">03</span><span class="v2-eyebrow">FROM NATURE TO ART</span><h2>از ماده خام،<br>تا یک امضای نامرئی.</h2><p>هر عطر یک تعادل است: شروعی که توجه را می‌گیرد، قلبی که شخصیت می‌سازد و پایه‌ای که در حافظه می‌ماند.</p><a class="v2-btn v2-btn-outline" href="{% url 'first:customer_service' 'shopping-guide' %}">راهنمای انتخاب عطر ←</a></div>
  <div class="v2-craft-art"><div class="petal p1"></div><div class="petal p2"></div><div class="petal p3"></div><div class="petal p4"></div><span>NATURE<br>INSPIRES<br>EVERYTHING</span></div>
</section>

{% if new_products %}
<section class="v2-new-section"><div class="v2-section-head reveal"><div><span class="v2-eyebrow">NEW DISCOVERIES</span><h2>تازه وارد آرشیو</h2></div><a href="{% url 'first:product_list' %}?sort=-created_at">مشاهده همه ←</a></div><div class="v2-featured-grid">{% for product in new_products|slice:":4" %}{% include 'includes/perfume_product_card.html' %}{% endfor %}</div></section>
{% endif %}

<section class="v2-quote"><span>04</span><blockquote>“Perfume is the most intense form of memory.”</blockquote><small>JEAN-PAUL GUERLAIN</small></section>
{% endblock %}
'''

FILES["first/templates/products/product_list.html"] = r'''
{% extends 'perfume_base.html' %}{% load custom_filters %}
{% block title %}کالکشن عطرها | {{ settings.site_name|default:"VÉLORA" }}{% endblock %}
{% block content %}
<section class="v2-catalog-hero">
  <div><span class="v2-eyebrow">THE ARCHIVE / 2026</span><h1>کالکشن<br><em>عطرها</em></h1><p>رایحه‌هایی برای ساعات مختلف روز، فصل‌های مختلف و شخصیت‌های متفاوت.</p></div>
  <div class="v2-catalog-art"><div class="v2-catalog-orbit"></div><div class="v2-mosaic-bottle catalog-bottle"></div></div>
</section>
<section class="v2-catalog">
  <aside class="v2-filter-panel" data-filters>
    <div class="v2-filter-mobile-head"><span>FILTER ARCHIVE</span><button data-filter-close>×</button></div>
    <div class="v2-filter-block"><span>CATEGORY</span><a href="{% url 'first:product_list' %}">همه عطرها <small>{{ total_products }}</small></a>{% for category in categories %}{% if category.slug %}<a href="?category={{ category.slug }}">{{ category.name }}</a>{% endif %}{% endfor %}</div>
    <div class="v2-filter-block"><span>MAISON / BRAND</span>{% for brand in brands %}{% if brand.slug %}<a href="?brand={{ brand.slug }}">{{ brand.name }}</a>{% endif %}{% endfor %}</div>
    <form class="v2-filter-block" method="get"><span>PRICE RANGE</span><div class="v2-price-pair"><input type="number" name="min_price" value="{{ request.GET.min_price }}" placeholder="از"><input type="number" name="max_price" value="{{ request.GET.max_price }}" placeholder="تا"></div><button class="v2-btn v2-btn-outline" type="submit">اعمال فیلتر</button></form>
  </aside>
  <div class="v2-catalog-main">
    <div class="v2-catalog-toolbar"><div><button data-filter-open><i class="fa-solid fa-sliders"></i> فیلتر</button><span>{{ page_obj.paginator.count }} رایحه</span></div><label>مرتب‌سازی <select data-sort><option value="-created_at">جدیدترین</option><option value="-sales_count">پرفروش‌ترین</option><option value="-rating">بالاترین امتیاز</option><option value="price">قیمت کم به زیاد</option><option value="-price">قیمت زیاد به کم</option></select></label></div>
    <div class="v2-catalog-grid">{% for product in page_obj %}{% include 'includes/perfume_product_card.html' %}{% empty %}<div class="v2-empty"><span>NO RESULTS</span><h2>رایحه‌ای پیدا نشد.</h2></div>{% endfor %}</div>
  </div>
</section>
{% endblock %}
'''

FILES["first/templates/products/product_detail.html"] = r'''
{% extends 'perfume_base.html' %}{% load custom_filters %}
{% block title %}{{ product.name }} | {{ settings.site_name|default:"VÉLORA" }}{% endblock %}
{% block content %}
<section class="v2-detail">
  <div class="v2-detail-gallery">
    <div class="v2-detail-index">PRODUCT / {{ product.id|stringformat:"03d" }}</div>
    <div class="v2-detail-main"><div class="v2-detail-orbit"></div>{% if product.main_image %}<img id="detailMainImage" src="{{ product.main_image.url }}" alt="{{ product.name }}">{% else %}<div class="v2-hero-bottle"><div class="cap"></div><div class="glass"><span>VÉLORA</span></div></div>{% endif %}</div>
    {% if product.main_image %}<div class="v2-thumbs"><button data-image="{{ product.main_image.url }}"><img src="{{ product.main_image.url }}" alt=""></button>{% for image in product.images.all %}<button data-image="{{ image.image.url }}"><img src="{{ image.image.url }}" alt=""></button>{% endfor %}</div>{% endif %}
  </div>

  <div class="v2-detail-info">
    <div class="v2-detail-topline"><span class="v2-eyebrow">{{ product.brand.name|default:"SIGNATURE FRAGRANCE" }}</span><span>{% if product.is_best_seller %}ICON{% endif %}</span></div>
    <h1>{{ product.name }}</h1>
    <div class="v2-detail-rating"><span>★★★★★</span><b>{{ product.rating|floatformat:1 }}</b><small>{{ reviews.count }} REVIEW</small></div>
    {% if product.short_description %}<p class="v2-detail-lead">{{ product.short_description }}</p>{% endif %}
    <div class="v2-detail-price"><strong id="detailPrice">{{ product.final_price|price_format }}</strong><span>تومان</span>{% if product.discount_percent %}<del>{{ product.price|price_format }}</del>{% endif %}</div>

    <div class="v2-notes-pyramid">
      <div><span>01</span><small>TOP</small><b>نت آغازین</b><p>اولین برخورد با رایحه</p></div>
      <div><span>02</span><small>HEART</small><b>نت میانی</b><p>شخصیت اصلی عطر</p></div>
      <div><span>03</span><small>BASE</small><b>نت پایه</b><p>رد ماندگار روی پوست</p></div>
    </div>

    <form method="post" action="{% url 'first:add_to_cart' product.id %}" class="v2-buy-form">
      {% csrf_token %}<input type="hidden" name="variant" id="variantInput">
      {% if product.has_variants %}
      <div class="v2-variant-head"><span>SELECT VARIANT</span><small>حجم یا تنوع</small></div>
      <div class="v2-variants">
        {% for variant in available_variants %}
        <button type="button" data-variant="{{ variant.id }}" data-price="{{ variant.final_price }}" data-stock="{{ variant.stock }}" data-vimage="{% if variant.image %}{{ variant.image.url }}{% endif %}">
          {% if variant.volume_ml %}{{ variant.volume_ml }} ml{% elif variant.size %}{{ variant.size }}{% elif variant.color %}{{ variant.color.name }}{% else %}گزینه {{ forloop.counter }}{% endif %}
        </button>
        {% endfor %}
      </div>
      {% endif %}
      <div class="v2-buy-row"><div class="v2-qty"><button type="button" data-minus>−</button><input id="qty" name="qty" value="1" min="1" type="number"><button type="button" data-plus>+</button></div><button class="v2-btn v2-btn-gold grow" {% if not product.is_in_stock %}disabled{% endif %}>افزودن به سبد <i class="fa-solid fa-bag-shopping"></i></button></div>
    </form>

    {% if user.is_authenticated %}<form method="post" action="{% url 'first:add_to_wishlist' product.id %}">{% csrf_token %}<button class="v2-wishlist">♡ افزودن به آرشیو شخصی</button></form>{% endif %}
    <div class="v2-detail-guarantees"><div><i class="fa-regular fa-gem"></i><span><b>اصالت</b><small>تضمین اصالت کالا</small></span></div><div><i class="fa-solid fa-gift"></i><span><b>هدیه</b><small>بسته‌بندی لوکس</small></span></div><div><i class="fa-solid fa-truck-fast"></i><span><b>ارسال</b><small>بسته‌بندی امن</small></span></div></div>
  </div>
</section>

<section class="v2-detail-story"><div><span class="v2-section-number inline">01</span><span class="v2-eyebrow">THE CHARACTER</span><h2>رایحه‌ای که<br>بعد از شما می‌ماند.</h2></div><div class="v2-description">{{ product.description|linebreaks }}</div></section>

<section class="v2-reviews">
  <div class="v2-section-head"><div><span class="v2-eyebrow">COMMUNITY NOTES</span><h2>تجربه خریداران</h2></div></div>
  {% if user.is_authenticated %}<form class="v2-review-form" method="post" action="{% url 'first:add_review' product.id %}">{% csrf_token %}<select name="rating"><option value="5">★★★★★</option><option value="4">★★★★☆</option><option value="3">★★★☆☆</option><option value="2">★★☆☆☆</option><option value="1">★☆☆☆☆</option></select><textarea name="comment" rows="4" required placeholder="تجربه‌ات از این رایحه را بنویس..."></textarea><button class="v2-btn v2-btn-outline">ثبت نظر</button></form>{% endif %}
  <div class="v2-review-grid">{% for review in reviews %}<article class="reveal"><span>★★★★★</span><p>{{ review.comment }}</p><small>{{ review.user.username }} / {{ review.created_at|date:"Y.m.d" }}</small></article>{% empty %}<div class="v2-empty"><span>NO REVIEWS YET</span><h3>اولین تجربه را ثبت کن.</h3></div>{% endfor %}</div>
</section>

{% if similar_products %}<section class="v2-new-section"><div class="v2-section-head"><div><span class="v2-eyebrow">YOU MAY ALSO LIKE</span><h2>رایحه‌های مشابه</h2></div></div><div class="v2-featured-grid">{% for product in similar_products %}{% include 'includes/perfume_product_card.html' %}{% endfor %}</div></section>{% endif %}
{% endblock %}
'''

FILES["static/css/perfume-luxury-v2.css"] = r'''
:root{--bg:#070605;--bg-soft:#0d0b09;--surface:#12100d;--surface2:#18140f;--text:#f5efe7;--muted:#9e9487;--gold:#d3ad6c;--gold2:#9d6f32;--gold3:#f0d7a4;--line:rgba(212,174,108,.18);--line2:rgba(212,174,108,.42);--serif:Georgia,"Times New Roman",serif;--shadow:0 35px 110px rgba(0,0,0,.42);--max:1560px}
html[data-perfume-theme="day"]{--bg:#f3ede4;--bg-soft:#faf6ef;--surface:#fffaf3;--surface2:#eadfd1;--text:#17130f;--muted:#6a6056;--gold:#976b30;--gold2:#c79b5a;--gold3:#805721;--line:rgba(116,86,49,.18);--line2:rgba(130,92,42,.4);--shadow:0 35px 100px rgba(75,50,24,.12)}
*{box-sizing:border-box}html{scroll-behavior:smooth;background:var(--bg)}body{margin:0;background:var(--bg);color:var(--text);font-family:Vazir,Tahoma,sans-serif;line-height:1.85;overflow-x:hidden;transition:.35s}a{color:inherit;text-decoration:none}img{display:block;max-width:100%}button,input,textarea,select{font:inherit}.noise-layer{position:fixed;z-index:9999;inset:0;pointer-events:none;opacity:.03;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}.page-progress{position:fixed;z-index:1000;top:0;left:0;height:1px;width:0;background:var(--gold)}.custom-cursor,.custom-cursor-ring{position:fixed;z-index:10000;pointer-events:none;border-radius:50%;transform:translate(-50%,-50%)}.custom-cursor{width:5px;height:5px;background:var(--gold)}.custom-cursor-ring{width:28px;height:28px;border:1px solid rgba(211,173,108,.55)}.custom-cursor-ring.active{width:52px;height:52px}.v2-eyebrow{font-size:8px;letter-spacing:.3em;color:var(--gold);font-weight:700;direction:ltr}.v2-section-number{font-family:var(--serif);font-size:120px;color:color-mix(in srgb,var(--gold) 12%,transparent);line-height:.7;position:absolute;left:4vw;top:45px}.v2-section-number.inline{position:static;font-size:34px;color:var(--gold);display:block;margin-bottom:16px}.grow{flex:1}
.v2-header{position:fixed;z-index:100;top:18px;left:0;right:0;padding:0 2.5vw;transition:.3s}.v2-header-shell{max-width:var(--max);margin:auto;height:76px;border:1px solid rgba(211,173,108,.14);background:rgba(7,6,5,.42);backdrop-filter:blur(18px);display:grid;grid-template-columns:250px 1fr 250px;align-items:center;padding:0 20px}.v2-header.scrolled{top:0}html[data-perfume-theme="day"] .v2-header-shell{background:rgba(250,245,237,.65)}.v2-brand{display:flex;flex-direction:column;width:max-content;direction:ltr}.v2-brand-main{font-family:var(--serif);font-size:23px;letter-spacing:.32em;color:var(--gold3)}.v2-brand-sub{font-size:6px;letter-spacing:.32em;color:var(--muted)}.v2-nav{display:flex;justify-content:center;gap:24px}.v2-nav a{font-size:10px}.v2-nav a span{font-size:6px;color:var(--gold);margin-left:5px}.v2-actions{display:flex;justify-content:flex-end;direction:ltr}.v2-actions>*{width:38px;height:38px;border:0;background:none;display:grid;place-items:center;color:var(--text)}.only-day{display:none}html[data-perfume-theme="day"] .only-night{display:none}html[data-perfume-theme="day"] .only-day{display:block}.v2-menu-toggle{display:none!important}.v2-menu-toggle span{width:18px;height:1px;background:currentColor;margin:2px}
.v2-menu{position:fixed;z-index:200;inset:0;background:#080705;color:#f4eee5;padding:30px 7vw;transform:translateY(-105%);transition:.5s}.v2-menu.open{transform:none}.v2-menu-top{display:flex;justify-content:space-between;color:#d3ad6c}.v2-menu-top button{font-size:38px;background:none;border:0;color:#fff}.v2-menu nav{display:grid;margin-top:50px}.v2-menu nav a{display:flex;align-items:center;gap:28px;border-bottom:1px solid rgba(211,173,108,.18);padding:12px 0}.v2-menu nav small{color:#d3ad6c}.v2-menu nav strong{font-family:var(--serif);font-weight:400;font-size:clamp(27px,5vw,58px)}
.v2-search{position:fixed;z-index:210;inset:0;background:rgba(6,5,4,.97);color:#f5efe7;display:grid;place-items:center;opacity:0;visibility:hidden;transition:.25s}.v2-search.open{opacity:1;visibility:visible}.v2-search-close{position:absolute;left:5vw;top:4vh;border:0;background:none;color:#fff;font-size:42px}.v2-search-inner{width:min(900px,88vw)}.v2-search h2{font-family:var(--serif);font-size:clamp(45px,7vw,90px);font-weight:400;line-height:.95}.v2-search form{display:flex;border-bottom:1px solid rgba(211,173,108,.38)}.v2-search input{flex:1;background:none;border:0;color:#fff;padding:16px 0;outline:none}.v2-search form button{border:0;background:none;color:#d3ad6c}.v2-search-hints{display:flex;gap:8px;margin-top:18px}.v2-search-hints a{border:1px solid rgba(211,173,108,.2);padding:5px 12px;font-size:8px}
.v2-toasts{position:fixed;z-index:220;top:105px;right:25px}.v2-toast{padding:12px 14px;border:1px solid var(--line);background:var(--surface);display:flex;gap:15px}.v2-toast button{border:0;background:none;color:var(--muted)}
.v2-btn{min-height:48px;padding:0 24px;display:inline-flex;align-items:center;justify-content:center;gap:14px;border:1px solid transparent;font-size:10px;transition:.25s}.v2-btn-gold{background:linear-gradient(120deg,var(--gold3),var(--gold2));color:#171009}.v2-btn-outline{border-color:var(--line2)}.v2-btn-link{padding:0}.v2-play{width:38px;height:38px;border:1px solid var(--line2);border-radius:50%;display:grid;place-items:center}
.v2-hero{height:100vh;min-height:780px;position:relative;display:grid;grid-template-columns:1fr 1.15fr .72fr;align-items:center;padding:135px 4.5vw 55px;overflow:hidden}.v2-hero-bg{position:absolute;z-index:-5;inset:0;width:100%;height:100%;object-fit:cover;opacity:.38}.v2-hero-overlay{position:absolute;z-index:-4;inset:0;background:linear-gradient(90deg,rgba(5,4,3,.96),rgba(5,4,3,.76) 29%,rgba(5,4,3,.2) 61%,rgba(5,4,3,.85))}html[data-perfume-theme="day"] .v2-hero-overlay{background:linear-gradient(90deg,rgba(248,243,235,.98),rgba(248,243,235,.82),rgba(248,243,235,.28),rgba(248,243,235,.92))}.v2-hero-gridlines{position:absolute;z-index:-3;inset:0;background-image:linear-gradient(rgba(211,173,108,.055) 1px,transparent 1px),linear-gradient(90deg,rgba(211,173,108,.055) 1px,transparent 1px);background-size:90px 90px}.v2-hero-arch{position:absolute;z-index:-2;width:39%;height:80%;left:31%;top:8%;border:1px solid rgba(211,173,108,.18);border-radius:49% 49% 0 0/34% 34% 0 0}.v2-hero-left h1{font-family:var(--serif);font-weight:400;line-height:.9}.v2-hero-left h1 span,.v2-hero-left h1 em{display:block}.v2-hero-left h1 span{font-size:clamp(60px,6.5vw,104px)}.v2-hero-left h1 em{font-size:clamp(50px,5.6vw,88px);font-style:normal;color:var(--gold3)}.v2-hero-left>p{color:var(--muted);max-width:540px}.v2-hero-actions{display:flex;gap:16px;margin-top:30px}.v2-hero-proof{display:flex;align-items:center;gap:13px;margin-top:35px;color:var(--muted);font-size:9px}.v2-avatar-stack{display:flex}.v2-avatar-stack i{width:30px;height:30px;border:1px solid var(--gold);border-radius:50%;margin-left:-8px;background:radial-gradient(circle at 50% 28%,#d4b994,#74503d 35%,#1c1511 36%)}.v2-hero-center{height:630px;position:relative;display:grid;place-items:center}.v2-hero-product{z-index:4;width:72%;height:530px}.v2-hero-product img{width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 50px 38px rgba(0,0,0,.65));animation:v2float 5s ease-in-out infinite}.v2-orbit{position:absolute;border:1px solid rgba(231,168,77,.58);border-radius:50%}.o1{width:75%;height:36%;transform:rotate(-19deg);z-index:5;animation:orbit1 13s linear infinite}.o2{width:55%;height:62%;transform:rotate(38deg);opacity:.38;animation:orbit2 18s linear infinite}.o3{width:90%;height:18%;opacity:.18}.v2-spark{position:absolute;width:6px;height:6px;border-radius:50%;background:#ffd890;box-shadow:0 0 22px #f4a93f}.s1{right:18%;top:25%}.s2{left:20%;bottom:27%}.s3{right:35%;bottom:12%}.v2-hero-bottle{z-index:3;width:250px;height:410px;position:relative}.v2-hero-bottle .glass{position:absolute;bottom:0;width:100%;height:315px;border:2px solid rgba(220,171,99,.7);border-radius:30px;background:linear-gradient(90deg,#0c0907,#75441d,#120b07 62%,#693a17);display:flex;align-items:center;justify-content:center;flex-direction:column;color:#d5a760}.v2-hero-bottle .cap{position:absolute;top:0;left:60px;width:130px;height:85px;border:1px solid #a4773e;border-radius:15px;background:#302416}.v2-hero-label{position:absolute;left:0;bottom:25px}.v2-hero-label span{font-size:6px;color:var(--gold)}.v2-hero-label strong{display:block;font-family:var(--serif);font-weight:400}.v2-hero-right{display:grid;gap:30px}.v2-mini-feature{display:grid;grid-template-columns:22px 42px 1fr;gap:10px}.v2-mini-feature>span{font-size:6px;color:var(--gold)}.v2-mini-feature>i{width:40px;height:40px;border:1px solid var(--line2);border-radius:50%;display:grid;place-items:center;color:var(--gold)}.v2-mini-feature b{display:block;font-size:10px}.v2-mini-feature small{color:var(--muted);font-size:7px}.v2-scroll-note{position:absolute;right:4vw;bottom:30px;font-size:6px;color:var(--muted)}
.v2-ticker{height:46px;border-top:1px solid var(--line);border-bottom:1px solid var(--line);overflow:hidden;display:flex;align-items:center}.v2-ticker>div{display:flex;gap:28px;white-space:nowrap;animation:ticker 24s linear infinite}.v2-ticker span{font-family:var(--serif);color:var(--muted)}.v2-ticker i{color:var(--gold)}
.v2-icons-section,.v2-new-section,.v2-reviews{max-width:var(--max);margin:auto;padding:90px 4.5vw;position:relative}.v2-section-head{display:grid;grid-template-columns:1fr .85fr;gap:80px;align-items:end;margin-bottom:35px}.v2-section-head h2,.v2-split-copy h2,.v2-craft-copy h2,.v2-detail-story h2,.v2-reviews h2{font-family:var(--serif);font-size:clamp(42px,5vw,70px);font-weight:400;line-height:1}.v2-section-head p,.v2-split-copy p,.v2-craft-copy p{color:var(--muted)}.v2-featured-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.v2-product-card{border:1px solid var(--line);background:linear-gradient(145deg,var(--surface),var(--surface2));overflow:hidden;transition:.35s}.v2-product-card:hover{transform:translateY(-7px);box-shadow:var(--shadow)}.v2-product-visual{height:370px;display:grid;place-items:center;position:relative;overflow:hidden}.v2-product-visual img{width:100%;height:100%;object-fit:contain;padding:28px;position:relative;z-index:2}.v2-product-index{position:absolute;left:12px;bottom:5px;font-family:var(--serif);font-size:60px;color:rgba(211,173,108,.08)}.v2-badges{position:absolute;z-index:3;top:12px;right:12px;display:flex;gap:5px}.v2-badges span{font-size:6px;padding:3px 7px;background:var(--gold3);color:#171008}.v2-badges .sale{background:#7a2f2b;color:#fff}.v2-card-glow{position:absolute;width:180px;height:180px;border-radius:50%;background:#7b451f;filter:blur(65px);opacity:.16}.v2-placeholder-bottle{width:82px;height:155px;border:1px solid var(--gold);display:grid;place-items:center}.v2-product-info{padding:15px}.v2-product-info small{font-size:7px;color:var(--gold)}.v2-product-name{display:block;font-family:var(--serif);font-size:18px}.v2-product-meta{display:flex;justify-content:space-between;align-items:end;margin-top:14px}.v2-product-meta strong{font-size:11px}.v2-product-meta span,.v2-product-meta del{font-size:7px;color:var(--muted)}.v2-product-meta del{display:block}.v2-round-action{width:36px;height:36px;border:1px solid var(--line);border-radius:50%;display:grid;place-items:center;background:none;color:var(--text)}
.v2-editorial-split{display:grid;grid-template-columns:1fr 1.05fr;min-height:620px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.v2-split-art{position:relative;overflow:hidden;background:radial-gradient(circle at 45% 35%,#8a5f45 0 7%,#5b3829 25%,#1b110d 54%,#080605 74%);display:flex;align-items:flex-end;padding:38px}.v2-face-art{position:absolute;left:22%;top:8%;width:47%;height:76%;border-radius:48%;background:radial-gradient(ellipse at 54% 25%,#9c6b50 0 12%,#5e3b2e 28%,#1a100c 61%,transparent 62%)}.v2-art-copy{position:relative;font-family:var(--serif);font-size:34px;color:#e4c9a1}.v2-art-index{position:absolute;right:25px;top:20px;font-family:var(--serif);font-size:110px;color:rgba(255,255,255,.05)}.v2-split-copy{padding:70px 7vw;display:flex;justify-content:center;flex-direction:column}.v2-scent-links{display:grid;grid-template-columns:1fr 1fr;margin-top:25px;border-top:1px solid var(--line)}.v2-scent-links a{padding:18px 0;border-bottom:1px solid var(--line);display:grid;grid-template-columns:25px 1fr;grid-template-rows:auto auto}.v2-scent-links span{grid-row:1/3;color:var(--gold)}.v2-scent-links small{color:var(--muted)}
.v2-mosaic{display:grid;grid-template-columns:1.3fr 1fr 1fr;min-height:420px}.v2-mosaic-card{position:relative;overflow:hidden;padding:45px 4vw;display:flex;flex-direction:column;justify-content:flex-end;color:#f3ece3}.v2-mosaic-card.large{background:radial-gradient(circle at 75% 32%,#8f6038 0 12%,transparent 28%),#21130b}.v2-mosaic-card.dark{background:#16130f}.v2-mosaic-card.warm{background:#5d4027}.v2-mosaic-card>span{font-size:7px;color:#d4ad6c}.v2-mosaic-card h3{font-family:var(--serif);font-size:35px;font-weight:400}.v2-mosaic-card p{color:#c5b7a7}.v2-mosaic-bottle{position:absolute;right:68%;top:18%;width:90px;height:170px;border:1px solid #c29459;background:#321c0d;border-radius:8px}.v2-mosaic-rings{position:absolute;right:15%;top:18%;width:210px;height:210px;border:1px solid rgba(216,173,105,.28);border-radius:50%}.v2-gift-cube{position:absolute;right:58%;top:26%;width:125px;height:125px;background:#0c0907;border:1px solid #bc8e52}
.v2-craft{display:grid;grid-template-columns:1fr 1fr;min-height:560px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.v2-craft-copy{padding:80px 8vw;display:flex;justify-content:center;flex-direction:column}.v2-craft-art{position:relative;overflow:hidden;background:radial-gradient(circle at 50% 50%,#d8c3a3 0 7%,#9b764f 11%,#3b2c1f 35%,#080706 70%);display:grid;place-items:center}.v2-craft-art>span{position:relative;z-index:3;font-family:var(--serif);font-size:27px;color:#e1c59b}.petal{position:absolute;border-radius:55% 45% 55% 45%;background:linear-gradient(135deg,#e5d4b6,#9d7c55);opacity:.72}.p1{width:230px;height:110px;left:12%;top:25%}.p2{width:180px;height:90px;right:15%;top:18%}.p3{width:250px;height:120px;right:5%;bottom:18%}.p4{width:170px;height:80px;left:18%;bottom:13%}.v2-quote{padding:70px 5vw;max-width:var(--max);margin:auto;display:grid;grid-template-columns:80px 1fr auto;align-items:center}.v2-quote>span{font-family:var(--serif);font-size:70px;color:rgba(211,173,108,.13)}.v2-quote blockquote{font-family:var(--serif);font-size:30px;font-style:italic}.v2-quote small{font-size:7px;color:var(--gold)}
.v2-catalog-hero{padding:155px 4.5vw 55px;max-width:var(--max);margin:auto;display:grid;grid-template-columns:1fr 360px;align-items:end;border-bottom:1px solid var(--line)}.v2-catalog-hero h1{font-family:var(--serif);font-size:clamp(60px,8vw,115px);font-weight:400;line-height:.82}.v2-catalog-hero h1 em{font-style:normal;color:var(--gold3)}.v2-catalog-hero p{color:var(--muted)}.v2-catalog-art{height:230px;position:relative;display:grid;place-items:center}.v2-catalog-orbit{position:absolute;width:210px;height:210px;border:1px solid var(--line2);border-radius:50%}.catalog-bottle{position:relative;right:auto;top:auto}.v2-catalog{max-width:var(--max);margin:auto;padding:45px 4.5vw 90px;display:grid;grid-template-columns:250px 1fr;gap:40px}.v2-filter-panel{border-left:1px solid var(--line);padding-left:23px;position:sticky;top:110px;height:max-content}.v2-filter-block{display:grid;gap:6px;padding-bottom:22px;margin-bottom:22px;border-bottom:1px solid var(--line)}.v2-filter-block>span{font-size:7px;color:var(--gold)}.v2-filter-block a{color:var(--muted);font-size:9px}.v2-filter-block input,.v2-catalog-toolbar select{background:var(--surface);border:1px solid var(--line);color:var(--text);padding:9px}.v2-price-pair{display:grid;grid-template-columns:1fr 1fr;gap:6px}.v2-filter-mobile-head{display:none}.v2-catalog-toolbar{display:flex;justify-content:space-between;margin-bottom:22px;color:var(--muted)}.v2-catalog-toolbar>div{display:flex;gap:10px}.v2-catalog-toolbar button{display:none}.v2-catalog-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.v2-empty{grid-column:1/-1;border:1px solid var(--line);padding:60px;text-align:center}
.v2-detail{max-width:var(--max);margin:auto;padding:135px 4.5vw 70px;display:grid;grid-template-columns:1.05fr .95fr;gap:65px}.v2-detail-index{font-size:7px;color:var(--gold)}.v2-detail-main{height:680px;border:1px solid var(--line);background:var(--surface);display:grid;place-items:center;position:relative}.v2-detail-main>img{width:100%;height:100%;object-fit:contain;padding:50px;z-index:2}.v2-detail-orbit{position:absolute;width:68%;height:30%;border:1px solid var(--line2);border-radius:50%;transform:rotate(-17deg)}.v2-thumbs{display:flex;gap:7px;margin-top:9px}.v2-thumbs button{width:72px;height:72px;border:1px solid var(--line);background:var(--surface)}.v2-thumbs img{width:100%;height:100%;object-fit:contain}.v2-detail-info{padding-top:36px}.v2-detail-topline{display:flex;justify-content:space-between}.v2-detail-info h1{font-family:var(--serif);font-size:clamp(52px,5.6vw,82px);font-weight:400;line-height:.92}.v2-detail-rating{display:flex;gap:9px;color:var(--muted)}.v2-detail-rating span{color:var(--gold)}.v2-detail-lead{color:var(--muted)}.v2-detail-price{display:flex;gap:8px;align-items:baseline}.v2-detail-price strong{font-family:var(--serif);font-size:32px}.v2-detail-price span,.v2-detail-price del{color:var(--muted);font-size:8px}.v2-notes-pyramid{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--line);border-bottom:1px solid var(--line);margin:26px 0}.v2-notes-pyramid>div{padding:17px;border-left:1px solid var(--line)}.v2-notes-pyramid small{color:var(--gold)}.v2-notes-pyramid b{display:block;font-family:var(--serif)}.v2-notes-pyramid p{font-size:7px;color:var(--muted)}.v2-variants{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:15px}.v2-variants button{border:1px solid var(--line);background:none;color:var(--text);padding:8px 12px}.v2-variants button.selected{border-color:var(--gold)}.v2-buy-row{display:flex;gap:8px}.v2-qty{height:48px;border:1px solid var(--line);display:flex}.v2-qty button{width:36px;border:0;background:none;color:var(--text)}.v2-qty input{width:42px;border:0;background:none;color:var(--text);text-align:center}.v2-wishlist{width:100%;border:0;background:none;color:var(--muted);padding:11px}.v2-detail-guarantees{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--line);margin-top:20px}.v2-detail-guarantees>div{display:flex;gap:8px;padding:14px}.v2-detail-guarantees i{color:var(--gold)}.v2-detail-guarantees small{display:block;color:var(--muted)}.v2-detail-story{display:grid;grid-template-columns:.8fr 1.2fr;gap:8vw;padding:80px 8vw;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.v2-description{color:var(--muted)}.v2-review-form{display:grid;gap:8px;border:1px solid var(--line);padding:20px}.v2-review-form select,.v2-review-form textarea{background:var(--surface);border:1px solid var(--line);color:var(--text);padding:10px}.v2-review-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:20px}.v2-review-grid article{border:1px solid var(--line);padding:20px}.v2-review-grid article>span{color:var(--gold)}.v2-review-grid p{color:var(--muted)}
.v2-footer{border-top:1px solid var(--line);padding:65px 4.5vw 20px;background:var(--surface)}.v2-footer-top{max-width:var(--max);margin:auto;display:grid;grid-template-columns:1.4fr .7fr .7fr 1.1fr;gap:42px}.v2-footer-brand h2{font-family:var(--serif);font-weight:400;font-size:48px}.v2-footer-brand p,.v2-footer-news p{color:var(--muted)}.v2-footer-links{display:flex;flex-direction:column;gap:7px}.v2-footer-links>span,.v2-footer-news>span{font-size:7px;color:var(--gold)}.v2-footer-links a{color:var(--muted);font-size:9px}.v2-footer-news>div{height:44px;border:1px solid var(--line);display:flex}.v2-footer-news input{flex:1;min-width:0;border:0;background:none;color:var(--text);padding:0 10px}.v2-footer-news button{width:45px;border:0;background:none;color:var(--gold)}.v2-footer-bottom{max-width:var(--max);margin:42px auto 0;border-top:1px solid var(--line);padding-top:16px;display:flex;justify-content:space-between;color:var(--muted);font-size:7px}
@keyframes v2float{50%{transform:translateY(-12px)}}@keyframes orbit1{to{transform:rotate(341deg)}}@keyframes orbit2{to{transform:rotate(-322deg)}}@keyframes ticker{to{transform:translateX(-50%)}}
@media(max-width:1200px){.v2-header-shell{grid-template-columns:210px 1fr 190px}.v2-nav{gap:15px}.v2-hero{grid-template-columns:1fr 1.08fr}.v2-hero-right{display:none}.v2-featured-grid{grid-template-columns:repeat(3,1fr)}.v2-featured-grid>*:nth-child(4){display:none}.v2-mosaic{grid-template-columns:1fr 1fr}.v2-mosaic-card.warm{grid-column:1/-1}.v2-catalog-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:900px){.custom-cursor,.custom-cursor-ring{display:none}.v2-header{top:0;padding:0}.v2-header-shell{height:72px;border-left:0;border-right:0;grid-template-columns:1fr auto;padding:0 18px}.v2-nav{display:none}.v2-menu-toggle{display:grid!important}.v2-hero{height:auto;min-height:900px;padding:95px 20px 45px;display:flex;flex-direction:column}.v2-hero-center{order:0;width:100%;height:430px}.v2-hero-left{order:1}.v2-hero-product{height:360px;width:65%}.v2-hero-arch{width:70%;height:45%;left:15%;top:6%}.v2-section-head{grid-template-columns:1fr;gap:10px}.v2-icons-section,.v2-new-section,.v2-reviews{padding:60px 20px}.v2-featured-grid{grid-template-columns:repeat(2,1fr)}.v2-featured-grid>*:nth-child(4){display:block}.v2-editorial-split{grid-template-columns:1fr}.v2-split-art{height:380px}.v2-split-copy{padding:50px 24px}.v2-mosaic{grid-template-columns:1fr}.v2-mosaic-card.warm{grid-column:auto}.v2-mosaic-card{min-height:260px}.v2-craft{grid-template-columns:1fr}.v2-craft-copy{padding:55px 24px}.v2-craft-art{height:360px}.v2-quote{grid-template-columns:1fr;padding:50px 20px}.v2-catalog-hero{padding:115px 20px 45px;grid-template-columns:1fr}.v2-catalog-art{display:none}.v2-catalog{display:block;padding:30px 20px}.v2-filter-panel{position:fixed;z-index:170;top:0;right:0;bottom:0;width:min(350px,90vw);background:var(--surface);padding:70px 20px;transform:translateX(105%);transition:.3s}.v2-filter-panel.open{transform:none}.v2-filter-mobile-head{display:flex;justify-content:space-between}.v2-catalog-toolbar button{display:block}.v2-detail{padding:105px 20px;grid-template-columns:1fr}.v2-detail-main{height:520px}.v2-detail-story{grid-template-columns:1fr;padding:55px 20px}.v2-review-grid{grid-template-columns:1fr}.v2-footer-top{grid-template-columns:1fr 1fr}.v2-footer-brand{grid-column:1/-1}}
@media(max-width:560px){.v2-featured-grid,.v2-catalog-grid{grid-template-columns:1fr}.v2-product-visual{height:400px}.v2-scent-links{grid-template-columns:1fr}.v2-notes-pyramid{grid-template-columns:1fr}.v2-buy-row{flex-direction:column}.v2-detail-guarantees{grid-template-columns:1fr}.v2-footer-top{grid-template-columns:1fr}.v2-footer-brand{grid-column:auto}}
'''

FILES["static/js/perfume-luxury-v2.js"] = r'''
(() => {
  const root=document.documentElement;
  const $=(s,c=document)=>c.querySelector(s);
  const $$=(s,c=document)=>[...c.querySelectorAll(s)];

  function setTheme(t){root.dataset.perfumeTheme=t;try{localStorage.setItem("velora-theme",t)}catch(e){}}

  document.addEventListener("click",e=>{
    if(e.target.closest("[data-theme-toggle]")){setTheme(root.dataset.perfumeTheme==="night"?"day":"night");return}
    if(e.target.closest("[data-menu-open]")){$("[data-menu]")?.classList.add("open");document.body.style.overflow="hidden";return}
    if(e.target.closest("[data-menu-close]")){$("[data-menu]")?.classList.remove("open");document.body.style.overflow="";return}
    if(e.target.closest("[data-search-open]")){$("[data-search]")?.classList.add("open");document.body.style.overflow="hidden";return}
    if(e.target.closest("[data-search-close]")){$("[data-search]")?.classList.remove("open");document.body.style.overflow="";return}
    if(e.target.closest("[data-filter-open]")){$("[data-filters]")?.classList.add("open");return}
    if(e.target.closest("[data-filter-close]")){$("[data-filters]")?.classList.remove("open");return}
    if(e.target.closest("[data-toast-close]")){e.target.closest(".v2-toast")?.remove();return}

    const th=e.target.closest("[data-image]");
    if(th){const img=$("#detailMainImage");if(img)img.src=th.dataset.image;return}

    const v=e.target.closest("[data-variant]");
    if(v){
      $$("[data-variant]").forEach(x=>x.classList.remove("selected"));v.classList.add("selected");
      const i=$("#variantInput"),p=$("#detailPrice"),m=$("#detailMainImage"),q=$("#qty");
      if(i)i.value=v.dataset.variant||"";
      if(p)p.textContent=new Intl.NumberFormat("fa-IR").format(Number(v.dataset.price||0));
      if(m&&v.dataset.vimage)m.src=v.dataset.vimage;
      if(q)q.max=Math.max(1,Number(v.dataset.stock||1));
      return;
    }

    if(e.target.closest("[data-minus]")){const q=$("#qty");if(q)q.value=Math.max(1,Number(q.value||1)-1);return}
    if(e.target.closest("[data-plus]")){const q=$("#qty");if(q)q.value=Math.min(Number(q.max||9999),Number(q.value||1)+1)}
  });

  document.addEventListener("change",e=>{
    const s=e.target.closest("[data-sort]");if(!s)return;
    const u=new URL(location.href);u.searchParams.set("sort",s.value);u.searchParams.delete("page");location.href=u;
  });

  const header=$("[data-header]"),progress=$("[data-progress]");
  function sync(){
    header?.classList.toggle("scrolled",scrollY>20);
    if(progress){const max=document.documentElement.scrollHeight-innerHeight;progress.style.width=(max>0?(scrollY/max)*100:0)+"%"}
  }
  sync();addEventListener("scroll",sync,{passive:true});

  const cursor=$("[data-cursor]"),ring=$("[data-cursor-ring]");
  if(matchMedia("(pointer:fine)").matches&&cursor&&ring){
    addEventListener("mousemove",e=>{cursor.style.left=e.clientX+"px";cursor.style.top=e.clientY+"px";ring.animate({left:e.clientX+"px",top:e.clientY+"px"},{duration:260,fill:"forwards"})});
    $$("a,button,input,select,textarea").forEach(el=>{el.addEventListener("mouseenter",()=>ring.classList.add("active"));el.addEventListener("mouseleave",()=>ring.classList.remove("active"))});
  }

  document.querySelector("[data-variant]")?.click();

  if("IntersectionObserver" in window){
    const items=$$(".reveal");
    items.forEach(el=>{el.style.opacity="0";el.style.transform="translateY(24px)";el.style.transition="opacity .7s ease,transform .7s ease"});
    const io=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.style.opacity="1";entry.target.style.transform="translateY(0)";io.unobserve(entry.target)}}),{threshold:.08});
    items.forEach(el=>io.observe(el));
  }
})();
'''

def main():
    print("="*76)
    print(" VÉLORA FRONTEND V2 — EDITORIAL UPGRADE")
    print("="*76)

    if not (ROOT/"manage.py").exists():
        raise SystemExit("Put this file beside manage.py inside perfume-shop.")

    backend=[
      "first/views.py","first/models.py","first/urls.py","first/forms.py",
      "first/context_processors.py","customer_care/views.py","customer_care/models.py","customer_care/urls.py"
    ]
    snap={p:(ROOT/p).read_bytes() for p in backend if (ROOT/p).exists()}

    if BACKUP.exists():
        raise SystemExit(f"Backup already exists: {BACKUP}")

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
    except Exception:
        for rel in written:
            dst=ROOT/rel;src=BACKUP/rel
            if src.exists():
                dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
            elif dst.exists():
                dst.unlink()
        raise

    print("\n"+"="*76)
    print(" V2 FRONTEND READY")
    print("="*76)
    print("Backend remained byte-for-byte unchanged.")
    print("Run: python manage.py runserver")
    print("Check home, catalog, and product detail first.")

if __name__=="__main__":
    main()
