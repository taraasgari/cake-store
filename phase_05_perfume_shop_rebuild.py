#!/usr/bin/env python
# -*- coding: utf-8 -*-

# PHASE 05 — PERFUME ONLINE SHOP REBUILD
#
# Extract this package INSIDE perfume-shop, then run:
#   .\venv\Scripts\Activate.ps1
#   python .\perfume_phase05_package\phase_05_perfume_shop_rebuild.py
#   python manage.py runserver
#
# Frontend only. Backend files are byte-checked.

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path


HERE = Path(__file__).resolve().parent

if (HERE / "manage.py").exists():
    ROOT = HERE
elif (HERE.parent / "manage.py").exists():
    ROOT = HERE.parent
else:
    raise SystemExit(
        "Could not find manage.py. Extract perfume_phase05_package inside perfume-shop."
    )

ASSET_SOURCE = HERE / "assets" / "hero-luxury.png"
BACKUP = ROOT / ".perfume_frontend_phase05_backup"

BASE = ROOT / "first/templates/perfume_base.html"
INDEX = ROOT / "first/templates/index.html"
CSS = ROOT / "static/css/perfume-phase05.css"
JS = ROOT / "static/js/perfume-phase05.js"
HERO_TARGET = ROOT / "static/images/perfume/hero-luxury.png"

BACKEND_GUARD = [
    "first/views.py",
    "first/models.py",
    "first/urls.py",
    "first/forms.py",
    "first/context_processors.py",
    "customer_care/views.py",
    "customer_care/models.py",
    "customer_care/urls.py",
]


def run(*args):
    print("\n> " + " ".join(map(str, args)))
    p = subprocess.run(list(args), cwd=ROOT, text=True)
    if p.returncode:
        raise RuntimeError("Command failed: " + " ".join(map(str, args)))


def backup(path: Path):
    if not path.exists():
        return
    dst = BACKUP / path.relative_to(ROOT)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)


def write(path: Path, content: str):
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    print("[WRITE]", path.relative_to(ROOT).as_posix())


def copy_asset(src: Path, dst: Path):
    if not src.exists():
        raise RuntimeError(f"Missing package asset: {src}")
    backup(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print("[ASSET]", dst.relative_to(ROOT).as_posix())


def patch_base():
    if not BASE.exists():
        raise RuntimeError("first/templates/perfume_base.html not found.")

    text = BASE.read_text(encoding="utf-8")
    original = text

    css_link = '<link rel="stylesheet" href="{% static \'css/perfume-phase05.css\' %}">'
    js_link = '<script src="{% static \'js/perfume-phase05.js\' %}"></script>'

    if "perfume-phase05.css" not in text:
        if "{% block extra_css %}" in text:
            text = text.replace(
                "{% block extra_css %}",
                css_link + "\n    {% block extra_css %}",
                1,
            )
        else:
            text = text.replace("</head>", "    " + css_link + "\n</head>", 1)

    if "perfume-phase05.js" not in text:
        if "</body>" not in text:
            raise RuntimeError("Could not find </body> in perfume_base.html")
        text = text.replace("</body>", "    " + js_link + "\n</body>", 1)

    if text != original:
        backup(BASE)
        BASE.write_text(text, encoding="utf-8")
        print("[PATCH] first/templates/perfume_base.html")


def discover_product_list() -> Path | None:
    candidates = [
        ROOT / "first/templates/products/product_list.html",
        ROOT / "first/templates/product_list.html",
    ]
    for p in candidates:
        if p.exists():
            return p

    root = ROOT / "first/templates"
    if not root.exists():
        return None

    for p in root.rglob("*.html"):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "p4-shop-layout" in txt or (
            "محدوده قیمت" in txt and "دسته‌بندی" in txt and "sort" in txt
        ):
            return p
    return None


QUICK_CATEGORIES = r'''
<section class="p5-quick-categories">
  <div class="p4-wrap">
    <div class="p5-section-title compact">
      <div>
        <span>QUICK DISCOVERY</span>
        <h2>دسته‌بندی دقیق‌تر عطرها</h2>
      </div>
    </div>

    <div class="p5-quick-grid">
      <a href="{% url 'first:search_products' %}?q=زنانه"><i class="fa-solid fa-venus"></i><strong>عطر زنانه</strong><small>Female</small></a>
      <a href="{% url 'first:search_products' %}?q=مردانه"><i class="fa-solid fa-mars"></i><strong>عطر مردانه</strong><small>Male</small></a>
      <a href="{% url 'first:search_products' %}?q=یونیسکس"><i class="fa-solid fa-venus-mars"></i><strong>یونیسکس</strong><small>Unisex</small></a>
      <a href="{% url 'first:search_products' %}?q=نیش"><i class="fa-regular fa-gem"></i><strong>عطر نیش</strong><small>Niche</small></a>
      <a href="{% url 'first:search_products' %}?q=دکانت"><i class="fa-solid fa-vial"></i><strong>سمپل و دکانت</strong><small>Sample</small></a>
      <a href="{% url 'first:search_products' %}?q=گرم"><i class="fa-solid fa-fire"></i><strong>گرم و شرقی</strong><small>Amber</small></a>
      <a href="{% url 'first:search_products' %}?q=خنک"><i class="fa-regular fa-snowflake"></i><strong>خنک و تازه</strong><small>Fresh</small></a>
      <a href="{% url 'first:search_products' %}?q=چوبی"><i class="fa-solid fa-tree"></i><strong>چوبی</strong><small>Woody</small></a>
      <a href="{% url 'first:search_products' %}?q=گلی"><i class="fa-solid fa-seedling"></i><strong>گلی</strong><small>Floral</small></a>
      <a href="{% url 'first:search_products' %}?q=مرکباتی"><i class="fa-solid fa-lemon"></i><strong>مرکباتی</strong><small>Citrus</small></a>
    </div>
  </div>
</section>
'''


def patch_product_list():
    p = discover_product_list()
    if not p:
        print("[WARN] Product-list template not found; homepage still receives precise categories.")
        return

    text = p.read_text(encoding="utf-8")
    if "p5-quick-categories" in text:
        print("[SKIP] Product-list quick categories already installed.")
        return

    markers = [
        '<section class="p4-wrap p4-shop-layout">',
        '<section class="p4-shop-layout">',
    ]
    for marker in markers:
        if marker in text:
            backup(p)
            text = text.replace(marker, QUICK_CATEGORIES + "\n\n" + marker, 1)
            p.write_text(text, encoding="utf-8")
            print("[PATCH]", p.relative_to(ROOT).as_posix(), "-> precise categories")
            return

    if "{% block content %}" in text:
        backup(p)
        text = text.replace(
            "{% block content %}",
            "{% block content %}\n" + QUICK_CATEGORIES,
            1,
        )
        p.write_text(text, encoding="utf-8")
        print("[PATCH]", p.relative_to(ROOT).as_posix(), "-> precise categories")


HOME_TEMPLATE = r'''
{% extends 'perfume_base.html' %}
{% load static %}
{% load custom_filters %}

{% block title %}{{ settings.site_title|default:'فروشگاه عطر | کالکشن عطرهای لوکس' }}{% endblock %}

{% block content %}

<section class="p5-hero" data-p5-hero>
  <div class="p5-hero-slide p5-hero-banner is-active" data-p5-hero-slide="0">
    <img src="{% static 'images/perfume/hero-luxury.png' %}" alt="کالکشن عطرهای لوکس">
    <a class="p5-banner-hit" href="{% url 'first:product_list' %}" aria-label="مشاهده محصولات"></a>
  </div>

  <div class="p5-hero-slide p5-hero-product-slide" data-p5-hero-slide="1">
    <div class="p5-hero-copy">
      <span>NEW PERFUME EDIT</span>
      <h1>تازه‌ترین رایحه‌های<br><em>فروشگاه</em></h1>
      <p>منتخب عطرهای تازه برای استایل روزانه، رسمی و شبانه.</p>
      <div>
        <a class="p5-primary" href="{% url 'first:product_list' %}?sort=-created_at">مشاهده تازه‌رسیده‌ها <i class="fa-solid fa-arrow-left"></i></a>
        <a class="p5-secondary" href="{% url 'first:best_sellers' %}">پرفروش‌ترین‌ها</a>
      </div>
    </div>

    <div class="p5-hero-product-art">
      {% firstof new_products.0 featured_products.0 best_sellers.0 as hero_product_two %}
      {% if hero_product_two and hero_product_two.main_image %}
      <a href="{% url 'first:product_detail' hero_product_two.slug %}">
        <img src="{{ hero_product_two.main_image.url }}" alt="{{ hero_product_two.name }}">
      </a>
      {% else %}
      <img src="{% static 'images/perfume/hero-luxury.png' %}" alt="">
      {% endif %}
    </div>
  </div>

  <div class="p5-hero-slide p5-hero-product-slide p5-hero-night-slide" data-p5-hero-slide="2">
    <div class="p5-hero-copy">
      <span>NIGHT SIGNATURE</span>
      <h1>انتخاب‌های عمیق‌تر<br><em>برای شب</em></h1>
      <p>رایحه‌های چوبی، گرم، تلخ و کهربایی برای حضور ماندگارتر.</p>
      <div>
        <a class="p5-primary" href="{% url 'first:search_products' %}?q=گرم">رایحه‌های گرم <i class="fa-solid fa-arrow-left"></i></a>
        <a class="p5-secondary" href="{% url 'first:search_products' %}?q=چوبی">رایحه‌های چوبی</a>
      </div>
    </div>

    <div class="p5-hero-product-art">
      {% firstof best_sellers.0 featured_products.1 new_products.1 as hero_product_three %}
      {% if hero_product_three and hero_product_three.main_image %}
      <a href="{% url 'first:product_detail' hero_product_three.slug %}">
        <img src="{{ hero_product_three.main_image.url }}" alt="{{ hero_product_three.name }}">
      </a>
      {% else %}
      <img src="{% static 'images/perfume/hero-luxury.png' %}" alt="">
      {% endif %}
    </div>
  </div>

  <div class="p5-hero-controls">
    <button type="button" class="is-active" data-p5-hero-dot="0">01</button>
    <button type="button" data-p5-hero-dot="1">02</button>
    <button type="button" data-p5-hero-dot="2">03</button>
  </div>
</section>


<section class="p5-trust-strip">
  <div class="p4-wrap">
    <article><i class="fa-solid fa-shield-halved"></i><div><strong>تضمین اصالت</strong><span>خرید مطمئن و شفاف</span></div></article>
    <article><i class="fa-solid fa-truck-fast"></i><div><strong>ارسال حرفه‌ای</strong><span>بسته‌بندی مناسب عطر</span></div></article>
    <article><i class="fa-solid fa-gift"></i><div><strong>مناسب هدیه</strong><span>انتخاب برای مناسبت‌های خاص</span></div></article>
    <article><i class="fa-solid fa-headset"></i><div><strong>مشاوره رایحه</strong><span>برای انتخاب دقیق‌تر</span></div></article>
  </div>
</section>


<section class="p5-category-section">
  <div class="p4-wrap">
    <div class="p5-section-title">
      <div>
        <span>SHOP BY CATEGORY</span>
        <h2>دسته‌بندی‌های عطر</h2>
        <p>از جنسیت و نوع استفاده تا خانواده رایحه، سریع‌تر به انتخاب مناسب برسید.</p>
      </div>
      <a href="{% url 'first:product_list' %}">همه محصولات <i class="fa-solid fa-arrow-left"></i></a>
    </div>

    <div class="p5-category-grid">
      <a href="{% url 'first:search_products' %}?q=زنانه"><i class="fa-solid fa-venus"></i><strong>عطر زنانه</strong><small>FEMME</small></a>
      <a href="{% url 'first:search_products' %}?q=مردانه"><i class="fa-solid fa-mars"></i><strong>عطر مردانه</strong><small>HOMME</small></a>
      <a href="{% url 'first:search_products' %}?q=یونیسکس"><i class="fa-solid fa-venus-mars"></i><strong>یونیسکس</strong><small>UNISEX</small></a>
      <a href="{% url 'first:search_products' %}?q=نیش"><i class="fa-regular fa-gem"></i><strong>عطر نیش</strong><small>NICHE</small></a>
      <a href="{% url 'first:search_products' %}?q=دکانت"><i class="fa-solid fa-vial"></i><strong>سمپل و دکانت</strong><small>SAMPLE</small></a>
      <a href="{% url 'first:search_products' %}?q=هدیه"><i class="fa-solid fa-gift"></i><strong>ست هدیه</strong><small>GIFT SET</small></a>
    </div>

    <div class="p5-scent-pills">
      <a href="{% url 'first:search_products' %}?q=گرم">گرم و شرقی</a>
      <a href="{% url 'first:search_products' %}?q=خنک">خنک و تازه</a>
      <a href="{% url 'first:search_products' %}?q=چوبی">چوبی</a>
      <a href="{% url 'first:search_products' %}?q=گلی">گلی</a>
      <a href="{% url 'first:search_products' %}?q=مرکباتی">مرکباتی</a>
      <a href="{% url 'first:search_products' %}?q=شیرین">شیرین</a>
      <a href="{% url 'first:search_products' %}?q=تلخ">تلخ</a>
      <a href="{% url 'first:search_products' %}?q=رسمی">رسمی</a>
    </div>
  </div>
</section>


{% firstof new_products featured_products best_sellers as first_rail %}
<section class="p5-products-section p5-products-light">
  <div class="p4-wrap">
    <div class="p5-section-title">
      <div>
        <span>NEW ARRIVALS</span>
        <h2>تازه‌رسیده‌ها</h2>
        <p>محصولات جدید فروشگاه با چینش متراکم و فروشگاهی.</p>
      </div>
      <div class="p5-rail-actions">
        <button type="button" data-p5-rail-prev="new"><i class="fa-solid fa-chevron-right"></i></button>
        <button type="button" data-p5-rail-next="new"><i class="fa-solid fa-chevron-left"></i></button>
      </div>
    </div>

    <div class="p5-product-rail" data-p5-rail="new">
      {% for product in first_rail|slice:":12" %}
      <article class="p5-shop-card">
        <a class="p5-shop-card-media" href="{% url 'first:product_detail' product.slug %}">
          {% if product.discount_percent %}<span class="p5-sale-badge">-{{ product.discount_percent|format_number }}%</span>{% endif %}
          {% if product.main_image %}
          <img src="{{ product.main_image.url }}" alt="{{ product.name }}" loading="lazy">
          {% else %}
          <div class="p5-no-image"><i class="fa-solid fa-spray-can-sparkles"></i></div>
          {% endif %}
        </a>

        <div class="p5-shop-card-body">
          <small>{{ product.brand.name|default:'PERFUME HOUSE' }}</small>
          <a class="p5-shop-card-title" href="{% url 'first:product_detail' product.slug %}">{{ product.name }}</a>

          <div class="p5-shop-card-meta">
            <div>
              {% if product.discount_percent %}<del>{{ product.price|price_format }}</del>{% endif %}
              <strong>{{ product.final_price|price_format }} <span>تومان</span></strong>
            </div>

            {% if product.has_variants %}
            <a class="p5-mini-cart" href="{% url 'first:product_detail' product.slug %}"><i class="fa-solid fa-arrow-left"></i></a>
            {% else %}
            <form method="post" action="{% url 'first:add_to_cart' product.id %}">
              {% csrf_token %}
              <button type="submit" class="p5-mini-cart"><i class="fa-solid fa-bag-shopping"></i></button>
            </form>
            {% endif %}
          </div>
        </div>
      </article>
      {% empty %}
      <div class="p5-rail-empty">هنوز محصولی برای نمایش وجود ندارد.</div>
      {% endfor %}
    </div>
  </div>
</section>


<section class="p5-promo-section">
  <div class="p4-wrap p5-promo-grid">
    <a class="p5-promo-card p5-promo-women" href="{% url 'first:search_products' %}?q=زنانه">
      <div>
        <span>FEMME EDIT</span>
        <h3>عطرهای زنانه</h3>
        <p>از رایحه‌های گلی و روشن تا انتخاب‌های گرم و مجلسی.</p>
        <b>مشاهده کالکشن <i class="fa-solid fa-arrow-left"></i></b>
      </div>
      {% firstof new_products.0 featured_products.0 best_sellers.0 as promo_women %}
      {% if promo_women and promo_women.main_image %}<img src="{{ promo_women.main_image.url }}" alt="">{% endif %}
    </a>

    <a class="p5-promo-card p5-promo-men" href="{% url 'first:search_products' %}?q=مردانه">
      <div>
        <span>HOMME EDIT</span>
        <h3>عطرهای مردانه</h3>
        <p>رایحه‌های چوبی، تلخ، خنک و رسمی برای استفاده روز و شب.</p>
        <b>مشاهده کالکشن <i class="fa-solid fa-arrow-left"></i></b>
      </div>
      {% firstof best_sellers.0 featured_products.1 new_products.1 as promo_men %}
      {% if promo_men and promo_men.main_image %}<img src="{{ promo_men.main_image.url }}" alt="">{% endif %}
    </a>
  </div>
</section>


{% firstof best_sellers featured_products new_products as best_rail %}
<section class="p5-products-section p5-products-dark">
  <div class="p4-wrap">
    <div class="p5-section-title">
      <div>
        <span>MOST WANTED</span>
        <h2>پرفروش‌ترین‌ها</h2>
        <p>انتخاب‌هایی که بیشتر از بقیه مورد توجه خریداران قرار گرفته‌اند.</p>
      </div>
      <div class="p5-rail-actions">
        <button type="button" data-p5-rail-prev="best"><i class="fa-solid fa-chevron-right"></i></button>
        <button type="button" data-p5-rail-next="best"><i class="fa-solid fa-chevron-left"></i></button>
      </div>
    </div>

    <div class="p5-product-rail" data-p5-rail="best">
      {% for product in best_rail|slice:":12" %}
      <article class="p5-shop-card">
        <a class="p5-shop-card-media" href="{% url 'first:product_detail' product.slug %}">
          {% if product.is_best_seller %}<span class="p5-icon-badge">ICON</span>{% endif %}
          {% if product.main_image %}
          <img src="{{ product.main_image.url }}" alt="{{ product.name }}" loading="lazy">
          {% else %}
          <div class="p5-no-image"><i class="fa-solid fa-spray-can-sparkles"></i></div>
          {% endif %}
        </a>

        <div class="p5-shop-card-body">
          <small>{{ product.brand.name|default:'PERFUME HOUSE' }}</small>
          <a class="p5-shop-card-title" href="{% url 'first:product_detail' product.slug %}">{{ product.name }}</a>
          <div class="p5-shop-card-meta">
            <div>
              {% if product.discount_percent %}<del>{{ product.price|price_format }}</del>{% endif %}
              <strong>{{ product.final_price|price_format }} <span>تومان</span></strong>
            </div>
            <a class="p5-mini-cart" href="{% url 'first:product_detail' product.slug %}"><i class="fa-solid fa-arrow-left"></i></a>
          </div>
        </div>
      </article>
      {% empty %}
      <div class="p5-rail-empty">هنوز داده‌ای برای بخش پرفروش‌ها وجود ندارد.</div>
      {% endfor %}
    </div>
  </div>
</section>


<section class="p5-shop-guide">
  <div class="p4-wrap p5-shop-guide-grid">
    <div class="p5-shop-guide-copy">
      <span>PERFUME SHOPPING GUIDE</span>
      <h2>برای خرید عطر، فقط<br>اسم برند کافی نیست.</h2>
      <p>غلظت، خانواده بویایی، فصل استفاده و موقعیت مصرف روی انتخاب عطر تأثیر دارند. قبل از خرید، سبک رایحه‌ای که دوست دارید را مشخص کنید.</p>
      <a href="{% url 'first:customer_service' 'shopping-guide' %}">راهنمای خرید عطر <i class="fa-solid fa-arrow-left"></i></a>
    </div>

    <div class="p5-guide-cards">
      <article><b>01</b><i class="fa-regular fa-sun"></i><strong>روزانه</strong><small>تمیز، مرکباتی، خنک</small></article>
      <article><b>02</b><i class="fa-regular fa-moon"></i><strong>شبانه</strong><small>گرم، چوبی، شرقی</small></article>
      <article><b>03</b><i class="fa-solid fa-user-tie"></i><strong>رسمی</strong><small>تلخ، عمیق، ماندگار</small></article>
      <article><b>04</b><i class="fa-solid fa-gift"></i><strong>هدیه</strong><small>انتخاب امن‌تر و محبوب</small></article>
    </div>
  </div>
</section>


{% if brands %}
<section class="p5-brands">
  <div class="p4-wrap">
    <span>CURATED BRANDS</span>
    <div>
      {% for brand in brands %}
        {% if brand.slug %}<a href="{% url 'first:brand_products' brand.slug %}">{{ brand.name }}</a>{% endif %}
      {% endfor %}
    </div>
  </div>
</section>
{% endif %}

{% endblock %}
'''


CSS_TEXT = r'''
:root,
html[data-perfume-theme="night"]{
  --p-bg:#0b0908!important;
  --p-bg-2:#100c09!important;
  --p-surface:#17110d!important;
  --p-surface-2:#24180f!important;
  --p-text:#f7f1e8!important;
  --p-muted:#b8aa99!important;
  --p-gold:#c8944b!important;
  --p-gold-deep:#8b5c29!important;
  --p-gold-pale:#e6c88f!important;
  --p-line:rgba(212,169,101,.18)!important;
  --p-line-strong:rgba(212,169,101,.42)!important;
  --p-shadow:0 24px 70px rgba(0,0,0,.34)!important;
}

html[data-perfume-theme="day"]{
  --p-bg:#f5efe7!important;
  --p-bg-2:#ece0d1!important;
  --p-surface:#fffaf4!important;
  --p-surface-2:#eadbc8!important;
  --p-text:#1a1410!important;
  --p-muted:#75685c!important;
  --p-gold:#9b6c31!important;
  --p-gold-deep:#77481d!important;
  --p-gold-pale:#bd8a45!important;
  --p-line:rgba(112,75,38,.16)!important;
  --p-line-strong:rgba(139,91,40,.34)!important;
  --p-shadow:0 22px 55px rgba(70,45,24,.13)!important;
}

body,.phase-main{
  background:
    radial-gradient(circle at 83% 4%,rgba(171,110,48,.06),transparent 22%),
    var(--p-bg)!important;
  color:var(--p-text)!important;
}

.p4-top-strip{
  min-height:36px!important;
  background:#090706!important;
}
.p4-top-strip-inner{gap:50px!important}
.p4-top-strip span{font-size:11px!important}

.p4-header{
  background:color-mix(in srgb,var(--p-bg) 96%,transparent)!important;
  border-color:var(--p-line)!important;
}
html[data-perfume-theme="day"] .p4-header{
  background:rgba(250,245,238,.96)!important;
}
.p4-mainbar{
  min-height:90px!important;
  grid-template-columns:285px minmax(420px,1fr) auto!important;
  gap:26px!important;
}
.p4-brand-mark{width:58px!important;height:58px!important}
.p4-brand-copy strong{font-size:24px!important}
.p4-search{height:58px!important;background:var(--p-surface)!important}
.p4-search button,.p4-search input{height:56px!important}
.p4-search input{font-size:14px!important}
.p4-icon{width:48px!important;height:48px!important;font-size:18px!important}
.p4-cart{height:48px!important;padding-inline:16px!important;font-size:13px!important}
.p4-navrow{min-height:58px!important}
.p4-nav{gap:34px!important}
.p4-nav a{padding:18px 0!important;font-size:14px!important;font-weight:600!important}
.p4-support{font-size:13px!important}

.p4-footer{
  background:#0b0908!important;
  color:#f6efe6!important;
  border-top-color:rgba(216,179,109,.18)!important;
}
.p4-footer h2{color:#f6efe6!important}
.p4-footer p,.p4-footer a,.p4-footer-bottom{color:#aa9c8c!important}
.p4-footer-links>span,.p4-footer-note>span,.p4-footer-brand>span{color:#d5a85f!important}

/* HERO */
.p5-hero{
  width:min(1640px,calc(100% - 36px));
  height:min(730px,calc(100vh - 184px));
  min-height:570px;
  margin:18px auto 0;
  position:relative;
  overflow:hidden;
  border:1px solid var(--p-line);
  background:#090706;
  box-shadow:var(--p-shadow);
}
.p5-hero-slide{
  position:absolute;
  inset:0;
  opacity:0;
  pointer-events:none;
  transition:opacity .6s ease,transform .8s ease;
  transform:scale(1.012);
}
.p5-hero-slide.is-active{opacity:1;pointer-events:auto;transform:scale(1)}
.p5-hero-banner img{width:100%;height:100%;object-fit:cover;display:block}
.p5-banner-hit{position:absolute;inset:0}
.p5-hero-product-slide{
  display:grid;
  grid-template-columns:1fr 1.05fr;
  background:
    radial-gradient(circle at 72% 28%,rgba(184,117,48,.18),transparent 25%),
    linear-gradient(115deg,#080706,#21160e 58%,#0a0806);
}
.p5-hero-night-slide{
  background:
    radial-gradient(circle at 72% 25%,rgba(210,168,108,.12),transparent 22%),
    linear-gradient(115deg,#050403,#17100c 58%,#050403);
}
.p5-hero-copy{
  position:relative;
  z-index:3;
  padding:74px 70px;
  display:flex;
  flex-direction:column;
  justify-content:center;
}
.p5-hero-copy>span{color:#d1a35c;font-size:10px;letter-spacing:.24em}
.p5-hero-copy h1{
  margin:15px 0 18px!important;
  color:#f8f1e8!important;
  font-size:clamp(54px,5.7vw,96px)!important;
  line-height:.98!important;
  font-weight:700!important;
}
.p5-hero-copy h1 em{display:block;color:#e1ba76;font-style:normal}
.p5-hero-copy p{max-width:590px;color:#b9aa99!important;font-size:17px;line-height:2}
.p5-hero-copy>div{display:flex;flex-wrap:wrap;gap:12px;margin-top:26px}
.p5-primary,.p5-secondary{
  min-height:52px;padding:0 22px;display:inline-flex;align-items:center;gap:11px;
  border:1px solid rgba(216,179,109,.38);color:#f6eee5!important
}
.p5-primary{border:0;background:linear-gradient(120deg,#e5c68e,#9a682d);color:#171008!important}
.p5-hero-product-art{position:relative;display:grid;place-items:center;padding:50px;overflow:hidden}
.p5-hero-product-art:before,.p5-hero-product-art:after{
  content:"";position:absolute;border:1px solid rgba(216,179,109,.24);border-radius:50%
}
.p5-hero-product-art:before{width:70%;height:34%;transform:rotate(-16deg)}
.p5-hero-product-art:after{width:48%;height:61%;transform:rotate(37deg)}
.p5-hero-product-art>a,.p5-hero-product-art>img{width:82%;height:82%;position:relative;z-index:2}
.p5-hero-product-art a img,.p5-hero-product-art>img{
  width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 45px 38px rgba(0,0,0,.55))
}
.p5-hero-controls{position:absolute;z-index:8;right:30px;bottom:26px;display:flex;gap:8px}
.p5-hero-controls button{
  width:48px;height:32px;border:1px solid rgba(226,186,119,.25);
  background:rgba(6,5,4,.55);color:#b9aa99;cursor:pointer
}
.p5-hero-controls button.is-active{
  border-color:#d7a85c;color:#e3bf7e;background:rgba(117,74,29,.34)
}

/* TRUST */
.p5-trust-strip{border-bottom:1px solid var(--p-line);background:var(--p-surface)}
.p5-trust-strip>.p4-wrap{display:grid;grid-template-columns:repeat(4,1fr)}
.p5-trust-strip article{
  min-height:94px;padding:16px 24px;display:flex;align-items:center;gap:13px;border-left:1px solid var(--p-line)
}
.p5-trust-strip article:last-child{border-left:0}
.p5-trust-strip i{
  width:42px;height:42px;flex:none;border:1px solid var(--p-line-strong);border-radius:50%;
  display:grid;place-items:center;color:var(--p-gold)
}
.p5-trust-strip strong{display:block;font-size:13px}
.p5-trust-strip span{color:var(--p-muted);font-size:10px}

/* TITLES */
.p5-section-title{margin-bottom:28px;display:flex;align-items:end;justify-content:space-between;gap:30px}
.p5-section-title>div>span{color:var(--p-gold);letter-spacing:.2em;font-size:9px}
.p5-section-title h2{margin:7px 0 4px!important;font-size:37px!important;font-weight:750!important}
.p5-section-title p{margin:0;color:var(--p-muted)!important;font-size:13px}
.p5-section-title>a{
  min-height:44px;padding:0 16px;display:inline-flex;align-items:center;gap:10px;
  border:1px solid var(--p-line-strong);color:var(--p-text)!important
}
.p5-section-title.compact{margin-bottom:18px}

/* CATEGORIES */
.p5-category-section{padding:72px 0;background:var(--p-bg)}
html[data-perfume-theme="day"] .p5-category-section{background:#f2e9de}
.p5-category-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}
.p5-category-grid a{
  min-height:175px;padding:20px 14px;border:1px solid var(--p-line);
  background:linear-gradient(145deg,var(--p-surface),var(--p-surface-2));
  display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;transition:.25s
}
.p5-category-grid a:hover{transform:translateY(-5px);border-color:var(--p-line-strong);box-shadow:var(--p-shadow)}
.p5-category-grid i{
  width:64px;height:64px;margin-bottom:14px;border:1px solid var(--p-line-strong);border-radius:50%;
  display:grid;place-items:center;color:var(--p-gold);font-size:23px
}
.p5-category-grid strong{font-size:15px}
.p5-category-grid small{margin-top:4px;color:var(--p-muted)!important;letter-spacing:.13em;font-size:8px}
.p5-scent-pills{margin-top:18px;display:flex;flex-wrap:wrap;gap:8px}
.p5-scent-pills a{
  padding:9px 15px;border:1px solid var(--p-line);border-radius:999px;background:var(--p-surface);
  color:var(--p-muted)!important;font-size:11px
}
.p5-scent-pills a:hover{color:var(--p-gold)!important;border-color:var(--p-line-strong)}

.p5-quick-categories{padding:38px 0 0;background:var(--p-bg)}
.p5-quick-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:9px}
.p5-quick-grid a{
  min-height:92px;padding:13px;border:1px solid var(--p-line);background:var(--p-surface);
  display:grid;grid-template-columns:38px 1fr;grid-template-rows:auto auto;align-items:center
}
.p5-quick-grid i{grid-row:1/3;color:var(--p-gold);font-size:19px}
.p5-quick-grid strong{font-size:12px}
.p5-quick-grid small{color:var(--p-muted)!important;font-size:8px}

/* PRODUCT RAILS */
.p5-products-section{padding:72px 0;border-top:1px solid var(--p-line)}
.p5-products-light{background:var(--p-surface)}
html[data-perfume-theme="day"] .p5-products-light{background:#fffaf4}
.p5-products-dark{background:var(--p-bg-2)}
html[data-perfume-theme="day"] .p5-products-dark{background:#e8dbc9}
.p5-rail-actions{display:flex;gap:7px}
.p5-rail-actions button{
  width:44px;height:44px;border:1px solid var(--p-line);background:var(--p-bg);color:var(--p-text);cursor:pointer
}
.p5-product-rail{
  display:grid;grid-auto-flow:column;grid-auto-columns:minmax(220px,1fr);grid-template-rows:1fr;
  gap:10px;overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:none;padding-bottom:3px
}
.p5-product-rail::-webkit-scrollbar{display:none}
.p5-shop-card{
  min-width:220px;scroll-snap-align:start;border:1px solid var(--p-line);background:var(--p-surface);transition:.25s
}
.p5-shop-card:hover{transform:translateY(-4px);border-color:var(--p-line-strong);box-shadow:var(--p-shadow)}
.p5-shop-card-media{
  height:250px;position:relative;display:grid;place-items:center;overflow:hidden;
  background:radial-gradient(circle at 50% 72%,rgba(154,94,39,.10),transparent 42%),
             color-mix(in srgb,var(--p-surface) 86%,var(--p-bg))
}
.p5-shop-card-media img{width:100%;height:100%;padding:18px;object-fit:contain;transition:.35s}
.p5-shop-card:hover .p5-shop-card-media img{transform:scale(1.045)}
.p5-sale-badge,.p5-icon-badge{position:absolute;z-index:2;top:10px;right:10px;padding:4px 7px;font-size:8px}
.p5-sale-badge{background:#87362f;color:#fff}
.p5-icon-badge{background:var(--p-gold-pale);color:#171008}
.p5-no-image{color:var(--p-gold);font-size:36px}
.p5-shop-card-body{padding:13px 14px 15px}
.p5-shop-card-body>small{display:block;color:var(--p-muted)!important;font-size:9px}
.p5-shop-card-title{
  min-height:43px;margin-top:4px;display:block;color:var(--p-text)!important;font-size:12px;font-weight:650;line-height:1.8
}
.p5-shop-card-meta{
  min-height:46px;margin-top:10px;padding-top:10px;border-top:1px solid var(--p-line);
  display:flex;justify-content:space-between;align-items:end;gap:8px
}
.p5-shop-card-meta del{display:block;color:var(--p-muted);font-size:8px}
.p5-shop-card-meta strong{display:block;font-size:11px}
.p5-shop-card-meta strong span{color:var(--p-muted);font-size:8px;font-weight:400}
.p5-mini-cart{
  width:34px;height:34px;border:1px solid var(--p-line);border-radius:50%;background:none;
  color:var(--p-text)!important;display:grid;place-items:center;cursor:pointer
}
.p5-mini-cart:hover{border-color:var(--p-gold);color:var(--p-gold)!important}
.p5-rail-empty{min-width:500px;padding:55px;border:1px solid var(--p-line);color:var(--p-muted)}

/* PROMOS */
.p5-promo-section{padding:26px 0 72px;background:var(--p-surface)}
.p5-promo-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.p5-promo-card{
  min-height:330px;position:relative;overflow:hidden;padding:42px;border:1px solid var(--p-line);
  background:radial-gradient(circle at 80% 30%,rgba(214,171,107,.15),transparent 24%),
             linear-gradient(120deg,var(--p-surface-2),var(--p-bg));
  display:flex;align-items:center
}
.p5-promo-card>div{max-width:56%;position:relative;z-index:2}
.p5-promo-card>img{
  position:absolute;left:4%;bottom:0;width:42%;height:90%;object-fit:contain;
  filter:drop-shadow(0 28px 30px rgba(0,0,0,.3))
}
.p5-promo-card span{color:var(--p-gold);letter-spacing:.17em;font-size:9px}
.p5-promo-card h3{margin:8px 0!important;font-size:34px!important}
.p5-promo-card p{color:var(--p-muted)!important;line-height:1.9}
.p5-promo-card b{margin-top:15px;display:inline-flex;align-items:center;gap:9px;color:var(--p-gold)}

/* GUIDE */
.p5-shop-guide{padding:76px 0;background:var(--p-surface);border-top:1px solid var(--p-line)}
html[data-perfume-theme="day"] .p5-shop-guide{background:#f9f2e9}
.p5-shop-guide-grid{display:grid;grid-template-columns:1fr 1fr;gap:28px}
.p5-shop-guide-copy{padding:48px;border:1px solid var(--p-line);background:var(--p-bg)}
.p5-shop-guide-copy>span{color:var(--p-gold);letter-spacing:.2em;font-size:9px}
.p5-shop-guide-copy h2{margin:12px 0 18px!important;font-size:47px!important;line-height:1.12!important}
.p5-shop-guide-copy p{color:var(--p-muted)!important;line-height:2}
.p5-shop-guide-copy a{
  min-height:48px;margin-top:18px;padding:0 18px;display:inline-flex;align-items:center;gap:10px;
  border:1px solid var(--p-line-strong);color:var(--p-text)!important
}
.p5-guide-cards{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.p5-guide-cards article{padding:24px;border:1px solid var(--p-line);background:var(--p-bg)}
.p5-guide-cards b{display:block;color:var(--p-gold);font-size:10px}
.p5-guide-cards i{margin:22px 0;color:var(--p-gold);font-size:27px}
.p5-guide-cards strong{display:block;font-size:17px}
.p5-guide-cards small{color:var(--p-muted)!important}

/* BRANDS */
.p5-brands{padding:48px 0 65px;background:var(--p-bg-2);border-top:1px solid var(--p-line)}
.p5-brands>.p4-wrap>span{display:block;text-align:center;color:var(--p-gold);letter-spacing:.22em;font-size:9px}
.p5-brands>.p4-wrap>div{margin-top:22px;display:flex;flex-wrap:wrap;justify-content:center;gap:30px}
.p5-brands a{color:var(--p-muted)!important;font-size:17px;font-weight:600}
.p5-brands a:hover{color:var(--p-gold)!important}

/* EXISTING P4 PAGES */
.p4-page-hero,.p4-feature-hero,.p4-service-hero{
  background:radial-gradient(circle at 78% 18%,rgba(179,113,47,.09),transparent 22%),var(--p-surface)!important
}
html[data-perfume-theme="day"] .p4-page-hero,
html[data-perfume-theme="day"] .p4-feature-hero,
html[data-perfume-theme="day"] .p4-service-hero{
  background:radial-gradient(circle at 78% 18%,rgba(165,105,47,.08),transparent 22%),#eadfce!important
}
.p4-filter,.p4-toolbar,.p4-service-menu,.p4-service-content,.p4-product-card,.p4-empty{
  background:var(--p-surface)!important;border-color:var(--p-line)!important
}
html[data-perfume-theme="day"] .p4-product-media{background:#f1e8dc!important}

/* TRACKING */
.p5-tracking-wrap{
  width:min(1220px,calc(100% - 44px));margin:52px auto 82px;
  display:grid;grid-template-columns:.9fr 1.1fr;gap:18px
}
.p5-tracking-info,.p5-tracking-card{min-height:560px;border:1px solid var(--p-line)}
.p5-tracking-info{
  padding:52px 42px;position:relative;overflow:hidden;
  background:radial-gradient(circle at 50% 62%,rgba(169,100,40,.18),transparent 30%),
             linear-gradient(145deg,var(--p-surface-2),var(--p-bg))
}
.p5-tracking-info>span{color:var(--p-gold);letter-spacing:.2em;font-size:9px}
.p5-tracking-info h2{margin:12px 0 16px!important;font-size:50px!important;line-height:1.08!important}
.p5-tracking-info p{max-width:500px;color:var(--p-muted)!important;line-height:2}
.p5-tracking-steps{margin-top:34px;display:grid;gap:10px}
.p5-tracking-steps div{padding:14px;display:grid;grid-template-columns:36px 1fr;border:1px solid var(--p-line)}
.p5-tracking-steps b{color:var(--p-gold)}
.p5-tracking-steps small{color:var(--p-muted)!important}
.p5-tracking-orbit{
  position:absolute;left:-80px;bottom:-80px;width:300px;height:300px;
  border:1px solid var(--p-line-strong);border-radius:50%
}
.p5-tracking-orbit:after{content:"";position:absolute;inset:55px;border:1px solid var(--p-line);border-radius:50%}
.p5-tracking-card{padding:48px;display:flex;align-items:center;background:var(--p-surface)}
.p5-tracking-existing{width:100%}
.p5-tracking-existing form{width:100%;max-width:620px;display:grid;gap:17px}
.p5-tracking-existing form label{display:grid;gap:7px;color:var(--p-muted);font-size:12px}
.p5-tracking-existing form input{
  width:100%!important;min-height:54px!important;padding:0 14px!important;
  border:1px solid var(--p-line)!important;background:var(--p-bg)!important;color:var(--p-text)!important;outline:none!important
}
.p5-tracking-existing form input:focus{
  border-color:var(--p-line-strong)!important;box-shadow:0 0 0 4px rgba(216,179,109,.05)!important
}
.p5-tracking-existing form button,.p5-tracking-existing form input[type="submit"]{
  min-height:54px!important;padding:0 18px!important;border:0!important;
  background:linear-gradient(120deg,var(--p-gold-pale),var(--p-gold-deep))!important;
  color:#171008!important;cursor:pointer!important
}

@media(min-width:1300px){
  .p5-product-rail{grid-auto-columns:calc((100% - 40px)/5)}
}
@media(max-width:1250px){
  .p4-mainbar{grid-template-columns:250px minmax(300px,1fr) auto!important}
  .p5-category-grid{grid-template-columns:repeat(3,1fr)}
  .p5-quick-grid{grid-template-columns:repeat(3,1fr)}
}
@media(max-width:980px){
  .p4-mainbar{grid-template-columns:1fr auto!important;min-height:82px!important}
  .p5-hero{height:800px}
  .p5-hero-product-slide{grid-template-columns:1fr}
  .p5-hero-copy{padding:42px 30px 10px}
  .p5-hero-product-art{padding:10px 30px 80px}
  .p5-trust-strip>.p4-wrap{grid-template-columns:1fr 1fr}
  .p5-promo-grid,.p5-shop-guide-grid,.p5-tracking-wrap{grid-template-columns:1fr}
  .p5-tracking-info,.p5-tracking-card{min-height:auto}
}
@media(max-width:680px){
  .p5-hero{width:calc(100% - 20px);min-height:650px;height:72vh}
  .p5-hero-copy h1{font-size:46px!important}
  .p5-trust-strip>.p4-wrap{grid-template-columns:1fr}
  .p5-category-section,.p5-products-section,.p5-shop-guide{padding:52px 0}
  .p5-category-grid{grid-template-columns:1fr 1fr}
  .p5-quick-grid{grid-template-columns:1fr 1fr}
  .p5-section-title{align-items:flex-start;flex-direction:column}
  .p5-product-rail{grid-auto-columns:76%}
  .p5-promo-grid{grid-template-columns:1fr}
  .p5-promo-card{min-height:300px;padding:28px}
  .p5-promo-card>div{max-width:62%}
  .p5-guide-cards{grid-template-columns:1fr 1fr}
  .p5-shop-guide-copy{padding:30px 22px}
  .p5-shop-guide-copy h2{font-size:38px!important}
  .p5-tracking-wrap{width:calc(100% - 24px);margin:26px auto 55px}
  .p5-tracking-info,.p5-tracking-card{padding:30px 20px}
  .p5-tracking-info h2{font-size:40px!important}
}
'''


JS_TEXT = r'''
(() => {
  "use strict";

  const $ = (s, r=document) => r.querySelector(s);
  const $$ = (s, r=document) => [...r.querySelectorAll(s)];

  function initHero(){
    const root = $("[data-p5-hero]");
    if(!root) return;

    const slides = $$("[data-p5-hero-slide]", root);
    const dots = $$("[data-p5-hero-dot]", root);
    if(!slides.length) return;

    let current = 0;
    let timer = null;

    function show(i){
      current = (i + slides.length) % slides.length;
      slides.forEach((slide,n) => slide.classList.toggle("is-active", n === current));
      dots.forEach((dot,n) => dot.classList.toggle("is-active", n === current));
    }

    function stop(){
      if(timer){ clearInterval(timer); timer = null; }
    }

    function start(){
      stop();
      timer = setInterval(() => show(current + 1), 6500);
    }

    dots.forEach(dot => {
      dot.addEventListener("click", () => {
        show(Number(dot.dataset.p5HeroDot || 0));
        start();
      });
    });

    root.addEventListener("mouseenter", stop);
    root.addEventListener("mouseleave", start);
    show(0);
    start();
  }

  function initRails(){
    $$("[data-p5-rail]").forEach(rail => {
      const name = rail.dataset.p5Rail;
      const prev = document.querySelector(`[data-p5-rail-prev="${name}"]`);
      const next = document.querySelector(`[data-p5-rail-next="${name}"]`);

      const amount = () => Math.max(rail.clientWidth * .78, 300);

      prev?.addEventListener("click", () => {
        rail.scrollBy({left: amount(), behavior:"smooth"});
      });

      next?.addEventListener("click", () => {
        rail.scrollBy({left: -amount(), behavior:"smooth"});
      });
    });
  }

  function looksLikeTrackingPage(){
    const path = location.pathname.toLowerCase();

    if(
      path.includes("order-tracking") ||
      path.includes("order_tracking") ||
      path.includes("track-order") ||
      path.includes("tracking")
    ) return true;

    const heading = document.querySelector("main h1, main h2");
    return Boolean(heading && heading.textContent.includes("پیگیری سفارش"));
  }

  function upgradeTracking(){
    if(!looksLikeTrackingPage()) return;

    const main = $(".phase-main");
    if(!main || $(".p5-tracking-wrap", main)) return;

    const form = $("form", main);
    if(!form) return;

    const existingNodes = [...main.childNodes];

    const wrapper = document.createElement("section");
    wrapper.className = "p5-tracking-wrap";
    wrapper.innerHTML = `
      <aside class="p5-tracking-info">
        <span>ORDER TRACKING</span>
        <h2>سفارشت کجاست؟</h2>
        <p>
          کد سفارش و شماره تلفنی که هنگام ثبت سفارش وارد کرده‌اید را وارد کنید.
          نتیجه پیگیری با همان منطق فعلی سایت در این بخش نمایش داده می‌شود.
        </p>

        <div class="p5-tracking-steps">
          <div><b>01</b><span><strong>کد سفارش</strong><small>شماره سفارش ثبت‌شده</small></span></div>
          <div><b>02</b><span><strong>شماره تلفن</strong><small>همان شماره هنگام خرید</small></span></div>
          <div><b>03</b><span><strong>مشاهده وضعیت</strong><small>مرحله فعلی پردازش و ارسال</small></span></div>
        </div>

        <div class="p5-tracking-orbit"></div>
      </aside>

      <div class="p5-tracking-card">
        <div class="p5-tracking-existing"></div>
      </div>
    `;

    const host = $(".p5-tracking-existing", wrapper);
    existingNodes.forEach(node => host.appendChild(node));
    main.appendChild(wrapper);
  }

  document.addEventListener("DOMContentLoaded", () => {
    initHero();
    initRails();
    upgradeTracking();
  });
})();
'''


def main():
    print("=" * 82)
    print(" PHASE 05 — PERFUME ONLINE SHOP REBUILD")
    print("=" * 82)

    if BACKUP.exists():
        raise SystemExit(
            f"Backup already exists: {BACKUP}\n"
            "Rename/delete it only if you intentionally want to rerun Phase 05."
        )

    if not INDEX.exists():
        raise SystemExit("first/templates/index.html not found.")

    BACKUP.mkdir(parents=True)

    backend_snapshot = {
        rel: (ROOT / rel).read_bytes()
        for rel in BACKEND_GUARD
        if (ROOT / rel).exists()
    }

    copy_asset(ASSET_SOURCE, HERO_TARGET)
    write(INDEX, HOME_TEMPLATE)
    write(CSS, CSS_TEXT)
    write(JS, JS_TEXT)
    patch_base()
    patch_product_list()

    for rel, before in backend_snapshot.items():
        if (ROOT / rel).read_bytes() != before:
            raise RuntimeError("Backend changed unexpectedly: " + rel)

    print("\n[CHECK] Django")
    run(sys.executable, "manage.py", "check")

    print("\n[CHECK] Migration drift")
    run(sys.executable, "manage.py", "makemigrations", "--check", "--dry-run")

    print("\n" + "=" * 82)
    print(" PHASE 05 READY")
    print("=" * 82)
    print("✓ supplied luxury perfume image installed in homepage hero")
    print("✓ no CSS sticker bottle in the main hero")
    print("✓ homepage rebuilt as a perfume online shop")
    print("✓ dense product rails inspired by the cosmetics reference")
    print("✓ precise perfume/scent categories added")
    print("✓ product-list quick categories added")
    print("✓ day: ivory / light brown / gold / white")
    print("✓ night: black / dark brown / gold / off-white")
    print("✓ order tracking upgraded without backend changes")
    print("✓ shared header tightened and made more readable")
    print("✓ backend byte-for-byte unchanged")

    print("\nNow run:")
    print("  python manage.py runserver")
    print("\nCheck:")
    print("  /")
    print("  /products/")
    print("  /best-sellers/")
    print("  /discounts/")
    print("  /customer-service/shopping-guide/")
    print("  order tracking page")


if __name__ == "__main__":
    main()
