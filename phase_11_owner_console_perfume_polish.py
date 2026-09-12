#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP = ROOT / ".perfume_frontend_phase11_backup" / STAMP

URLS = ROOT / "first" / "urls.py"
DASHBOARD = ROOT / "first" / "templates" / "dashboard"
ADMIN_BASE = DASHBOARD / "perfume_admin_base.html"
OWNER_PANEL = DASHBOARD / "owner_panel.html"
ADMIN_DASHBOARD = DASHBOARD / "admin_dashboard.html"
ADMIN_ADD_PRODUCT = DASHBOARD / "admin_add_product.html"
ADMIN_CSS = ROOT / "static" / "css" / "perfume-admin-v1.css"
ADMIN_JS = ROOT / "static" / "js" / "perfume-admin-v1.js"
ANALYTICS_VIEWS = ROOT / "first" / "analytics_views.py"
STATIC_CSS_DIR = ROOT / "static" / "css"

PROTECTED_BACKEND = [
    ROOT / "first" / "models.py",
    ROOT / "first" / "urls.py",
    ROOT / "first" / "views.py",
    ROOT / "first" / "forms.py",
    ROOT / "first" / "decorators.py",
    ROOT / "first" / "context_processors.py",
]

COLOR_REPLACEMENTS = {
    "#ec4899": "#b7823c", "#f472b6": "#d7ad63", "#db2777": "#8a5528",
    "#be185d": "#6f4625", "#b5125b": "#8a5528", "#e91e63": "#b7823c",
    "#d81b60": "#a87332", "#c2185b": "#845122", "#ff4081": "#d7ad63",
    "#f43f5e": "#9b6730", "#fb7185": "#d7ad63", "#7c3aed": "#8a5528",
    "#a855f7": "#b7823c", "#9333ea": "#845122", "#8b5cf6": "#b7823c",
    "#6d28d9": "#6f4625", "#3b82f6": "#8a5528", "#2563eb": "#6f4625",
    "#10b981": "#a87332", "#22c55e": "#b7823c", "#16a34a": "#845122",
    "#0ea5e9": "#a87332",
    "rgba(236, 64, 122": "rgba(215, 173, 99",
    "rgba(216, 27, 96": "rgba(183, 130, 60",
    "rgba(124, 58, 237": "rgba(111, 70, 37",
    "LUXURY BEAUTY STORE": "MAISON DE PARFUM",
    "آرایشی شاپ": "فروشگاه عطر",
    "محصولات آرایشی": "محصولات عطر",
    "لوازم آرایشی": "عطر و ادکلن",
    "رنگ محصول": "ظاهر / رنگ شیشه",
    "رنگ‌ها": "ظاهر شیشه‌ها",
}


def fail(message: str) -> None:
    print("\n[ERROR]", message)
    raise SystemExit(1)


def run(*args: str) -> None:
    print("\n> " + " ".join(map(str, args)))
    result = subprocess.run(list(args), cwd=ROOT)
    if result.returncode:
        fail("Command failed: " + " ".join(map(str, args)))


def backup(path: Path) -> None:
    if not path.exists():
        return
    target = BACKUP / path.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(path, target)


def write(path: Path, content: str) -> None:
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    print("[WRITE]", path.relative_to(ROOT).as_posix())


def route_names() -> set[str]:
    if not URLS.exists():
        return set()
    source = URLS.read_text(encoding="utf-8", errors="ignore")
    return set(re.findall(r"name\s*=\s*['\"]([A-Za-z0-9_:-]+)['\"]", source))


def dashboard_assets() -> str:
    if (ROOT / "static/css/tailwind.min.css").exists():
        return '<link rel="stylesheet" href="{% static \'css/tailwind.min.css\' %}">'
    if (ROOT / "static/vendor/tailwind/tailwindcss.js").exists():
        return '<script src="{% static \'vendor/tailwind/tailwindcss.js\' %}"></script>'
    return ""


def nav_link(name: str, label: str, icon: str) -> str:
    return (
        f'<a class="pa-nav-link {{% if request.resolver_match.url_name == \'{name}\' %}}active{{% endif %}}" '
        f'href="{{% url \'first:{name}\' %}}">'
        f'<i class="fa-solid {icon}"></i><span>{label}</span></a>'
    )


def make_nav(names: set[str]) -> str:
    items = []
    # admin_dashboard deliberately hidden from nav so the old dashboard section is not visible.
    candidates = [
        ("owner_panel", "پنل مالک", "fa-crown"),
        ("admin_products", "عطرها و محصولات", "fa-spray-can-sparkles"),
        ("admin_orders", "سفارش‌ها", "fa-receipt"),
        ("warehouse", "انبار عطرها", "fa-warehouse"),
        ("warehouse_products", "موجودی رایحه‌ها", "fa-boxes-stacked"),
        ("analytics_dashboard", "آمار فروش", "fa-chart-line"),
        ("admin_users", "مشتریان", "fa-users"),
        ("admin_reviews", "نظرات", "fa-star"),
        ("site_settings", "تنظیمات فروشگاه", "fa-sliders"),
        ("number_format_settings", "فرمت اعداد", "fa-hashtag"),
        ("customizer", "طراحی بصری", "fa-wand-magic-sparkles"),
    ]
    for name, label, icon in candidates:
        if name in names:
            items.append(nav_link(name, label, icon))
    return "\n".join(items)


def make_user_menu(names: set[str]) -> str:
    parts = []
    if "owner_panel" in names:
        parts.append('<a href="{% url \'first:owner_panel\' %}"><i class="fa-solid fa-crown"></i><span>پنل مالکیت</span></a>')
    elif "admin_dashboard" in names:
        parts.append('<a href="{% url \'first:admin_dashboard\' %}"><i class="fa-solid fa-crown"></i><span>پنل مالکیت</span></a>')
    if "profile" in names:
        parts.append('<a href="{% url \'first:profile\' %}"><i class="fa-solid fa-user"></i><span>پروفایل من</span></a>')
    if "edit_profile" in names:
        parts.append('<a href="{% url \'first:edit_profile\' %}"><i class="fa-solid fa-user-pen"></i><span>ویرایش پروفایل</span></a>')
    if "customizer" in names:
        parts.append('<a href="{% url \'first:customizer\' %}"><i class="fa-solid fa-wand-magic-sparkles"></i><span>طراحی بصری سایت</span></a>')
    parts.append('<a href="{% url \'first:home\' %}"><i class="fa-solid fa-store"></i><span>مشاهده فروشگاه</span></a>')
    if "logout" in names:
        parts.append(
            '<form method="post" action="{% url \'first:logout\' %}">{% csrf_token %}'
            '<button type="submit"><i class="fa-solid fa-arrow-right-from-bracket"></i><span>خروج</span></button>'
            '</form>'
        )
    return "\n".join(parts)


def make_quick_actions(names: set[str]) -> str:
    candidates = [
        ("admin_products", "مدیریت عطرها", "محصولات، برندها، حجم‌ها و قیمت‌ها", "fa-spray-can-sparkles"),
        ("admin_orders", "سفارش‌ها", "پردازش خرید، پرداخت و ارسال", "fa-receipt"),
        ("warehouse", "انبار", "کنترل موجودی عطرها و سمپل‌ها", "fa-warehouse"),
        ("analytics_dashboard", "آمار فروش", "روند فروش، مشتری و موجودی", "fa-chart-line"),
        ("customizer", "طراحی بصری", "ظاهر سایت و بخش‌های صفحه اصلی", "fa-wand-magic-sparkles"),
        ("site_settings", "تنظیمات فروشگاه", "لوگو، تماس، اسلایدر و اطلاعات برند", "fa-sliders"),
        ("admin_users", "مشتریان", "حساب‌های کاربری و سطح دسترسی", "fa-users"),
        ("admin_reviews", "نظرات", "بازخورد کاربران درباره رایحه‌ها", "fa-star"),
    ]
    cards = []
    for name, title, desc, icon in candidates:
        if name not in names:
            continue
        cards.append(
            f'<a class="pa-action-card" href="{{% url \'first:{name}\' %}}">'
            f'<span class="pa-action-icon"><i class="fa-solid {icon}"></i></span>'
            f'<span class="pa-action-copy"><strong>{title}</strong><small>{desc}</small></span>'
            '<i class="fa-solid fa-arrow-left pa-action-arrow"></i></a>'
        )
    return "\n".join(cards)


def more_link(names: set[str], name: str, label: str) -> str:
    return f'<a href="{{% url \'first:{name}\' %}}">{label} ←</a>' if name in names else ""


ADMIN_BASE_TEMPLATE = r"""
{% load static %}
<!doctype html>
<html lang="fa" dir="rtl" data-perfume-theme="night">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <title>{% block admin_title %}پنل مالک{% endblock %} | {{ settings.site_name|default:'فروشگاه عطر' }}</title>
  <script>
  try{
    const saved=localStorage.getItem("velora-theme")||localStorage.getItem("perfume-theme")||"night";
    document.documentElement.dataset.perfumeTheme=(saved==="day"||saved==="night")?saved:"night";
  }catch(e){}
  </script>
  <link rel="stylesheet" href="{% static 'vendor/vazir/font-face.css' %}">
  <link rel="stylesheet" href="{% static 'vendor/fontawesome/css/all.min.css' %}">
  __DASHBOARD_ASSETS__
  <link rel="stylesheet" href="{% static 'css/perfume-admin-v1.css' %}">
  {% block extra_css %}{% endblock %}
</head>
<body class="pa-body">
<section class="pa-shell">
  <aside class="pa-sidebar" data-pa-sidebar>
    <div class="pa-sidebar-brand">
      <span class="pa-monogram">V</span>
      <span><strong>{{ settings.site_name|default:'فروشگاه عطر' }}</strong><small>OWNER CONSOLE</small></span>
    </div>
    <button class="pa-sidebar-close" type="button" data-pa-close aria-label="بستن منو"><i class="fa-solid fa-xmark"></i></button>
    <nav class="pa-nav">__NAV__</nav>
    <div class="pa-sidebar-foot">
      <a href="{% url 'first:home' %}"><i class="fa-solid fa-arrow-up-right-from-square"></i><span>مشاهده فروشگاه</span></a>
      <div class="pa-owner-mini"><span class="pa-owner-avatar">{{ user.username|first|upper }}</span><span><strong>{{ user.username }}</strong><small>{% if user.is_superuser %}مالک فروشگاه{% else %}مدیر فروشگاه{% endif %}</small></span></div>
    </div>
  </aside>
  <div class="pa-main">
    <header class="pa-topbar">
      <div class="pa-topbar-start">
        <button class="pa-menu-button" type="button" data-pa-open aria-label="باز کردن منو"><i class="fa-solid fa-bars"></i></button>
        <a class="pa-shop-brand" href="{% url 'first:home' %}"><span class="pa-shop-mark">V</span><span><small>MAISON DE PARFUM</small><strong>{{ settings.site_name|default:'فروشگاه عطر' }}</strong></span></a>
      </div>
      <form class="pa-admin-search" action="{% url 'first:admin_products' %}" method="get">
        <button type="submit" aria-label="جستجو"><i class="fa-solid fa-magnifying-glass"></i></button>
        <input type="search" name="search" placeholder="جستجوی عطر، برند، خانواده رایحه..." value="{{ request.GET.search|default:'' }}">
      </form>
      <div class="pa-topbar-actions">
        <a class="pa-icon-button" href="{% url 'first:home' %}" title="فروشگاه"><i class="fa-solid fa-store"></i></a>
        <button class="pa-icon-button" type="button" data-pa-theme title="حالت روز/شب"><i class="fa-solid fa-circle-half-stroke"></i></button>
        <details class="pa-account-menu">
          <summary><span class="pa-account-avatar">{{ user.username|first|upper }}</span><span class="pa-account-name">{{ user.username }}</span><i class="fa-solid fa-chevron-down"></i></summary>
          <div class="pa-account-dropdown"><div class="pa-account-head"><strong>{{ user.username }}</strong><small dir="ltr">{{ user.email|default:'بدون ایمیل' }}</small></div>__USER_MENU__</div>
        </details>
      </div>
    </header>
    {% if messages %}<div class="pa-messages">{% for message in messages %}<div class="pa-message {{ message.tags|default:'info' }}"><i class="fa-solid fa-circle-info"></i><span>{{ message }}</span><button type="button" data-pa-message-close aria-label="بستن پیام"><i class="fa-solid fa-xmark"></i></button></div>{% endfor %}</div>{% endif %}
    <main class="pa-content">{% block admin_content %}{% block content %}{% endblock %}{% endblock %}</main>
  </div>
</section>
<div class="pa-overlay" data-pa-overlay></div>
<script src="{% static 'js/perfume-admin-v1.js' %}"></script>
{% block extra_js %}{% endblock %}
</body>
</html>
"""

OWNER_TEMPLATE = r"""
{% extends 'dashboard/perfume_admin_base.html' %}
{% load custom_filters %}
{% block admin_title %}پنل مالک{% endblock %}
{% block admin_content %}
<div class="pa-owner-dashboard">
  <section class="pa-dashboard-hero">
    <div><span class="pa-eyebrow">OWNER PERFUME CONSOLE</span><h1>پنل مالک فروشگاه عطر</h1><p>مرکز کنترل فروشگاه؛ از مدیریت رایحه‌ها و سفارش‌ها تا طراحی بصری، گزارش فروش و موجودی انبار.</p></div>
    <div class="pa-owner-seal"><i class="fa-solid fa-crown"></i><span>مالک</span></div>
  </section>
  <section class="pa-metrics">
    <article><span><i class="fa-solid fa-spray-can-sparkles"></i></span><small>محصولات عطر</small><strong>{{ total_products|default:0 }}</strong></article>
    <article><span><i class="fa-solid fa-receipt"></i></span><small>سفارش‌ها</small><strong>{{ total_orders|default:0 }}</strong></article>
    <article><span><i class="fa-solid fa-users"></i></span><small>مشتریان</small><strong>{{ total_users|default:0 }}</strong></article>
    <article class="gold"><span><i class="fa-solid fa-coins"></i></span><small>درآمد تاییدشده</small><strong>{{ total_revenue|default_if_none:0|price_format }}</strong><em>تومان</em></article>
  </section>
  <section class="pa-secondary-metrics">
    <div><i class="fa-regular fa-clock"></i><span><small>سفارش در انتظار</small><strong>{{ pending_orders|default:0 }}</strong></span></div>
    <div><i class="fa-regular fa-star"></i><span><small>نظر ثبت‌شده</small><strong>{{ total_reviews|default:0 }}</strong></span></div>
    <div><i class="fa-regular fa-heart"></i><span><small>علاقه‌مندی‌ها</small><strong>{{ total_wishlist|default:0 }}</strong></span></div>
  </section>
  <section class="pa-panel-section"><div class="pa-section-title"><div><span class="pa-eyebrow">MANAGE THE HOUSE OF SCENT</span><h2>ابزارهای اصلی مالک</h2></div><p>داشبورد قدیمی حذف شد؛ همه مسیرهای مهم از همین کنسول قابل دسترسی‌اند.</p></div><div class="pa-action-grid">__QUICK_ACTIONS__</div></section>
  <div class="pa-dashboard-columns">
    <section class="pa-panel-card"><div class="pa-card-head"><div><span class="pa-eyebrow">RECENT ORDERS</span><h2>آخرین سفارش‌ها</h2></div>__ORDERS_MORE__</div><div class="pa-list">{% for order in recent_orders %}<article class="pa-list-row"><span class="pa-list-icon"><i class="fa-solid fa-bag-shopping"></i></span><span class="pa-list-copy"><strong>#{{ order.order_number }}</strong><small>{{ order.created_at|date:'Y/m/d H:i' }} · {{ order.get_status_display }}</small></span><strong class="pa-row-value">{{ order.total|price_format }} <small>تومان</small></strong></article>{% empty %}<div class="pa-empty"><i class="fa-solid fa-receipt"></i><p>هنوز سفارشی ثبت نشده است.</p></div>{% endfor %}</div></section>
    <section class="pa-panel-card"><div class="pa-card-head"><div><span class="pa-eyebrow">BEST SELLERS</span><h2>پرفروش‌ترین عطرها</h2></div>__PRODUCTS_MORE__</div><div class="pa-list">{% for product in best_products %}<article class="pa-list-row"><span class="pa-product-thumb">{% if product.main_image %}<img src="{{ product.main_image.url }}" alt="{{ product.name }}">{% else %}<i class="fa-solid fa-spray-can-sparkles"></i>{% endif %}</span><span class="pa-list-copy"><strong>{{ product.name }}</strong><small>{{ product.sales_count|default:0 }} فروش</small></span><strong class="pa-row-value">{{ product.final_price|price_format }} <small>تومان</small></strong></article>{% empty %}<div class="pa-empty"><i class="fa-solid fa-spray-can-sparkles"></i><p>هنوز فروش محصولی ثبت نشده است.</p></div>{% endfor %}</div></section>
  </div>
  <section class="pa-panel-card"><div class="pa-card-head"><div><span class="pa-eyebrow">NEW MEMBERS</span><h2>آخرین مشتریان</h2></div>__USERS_MORE__</div><div class="pa-user-grid">{% for u in recent_users %}<article><span>{{ u.username|first|upper }}</span><strong>{{ u.username }}</strong><small dir="ltr">{{ u.email|default:'بدون ایمیل' }}</small></article>{% empty %}<div class="pa-empty"><i class="fa-solid fa-users"></i><p>هنوز مشتری جدیدی ثبت نشده است.</p></div>{% endfor %}</div></section>
</div>
{% endblock %}
"""

ADD_PRODUCT_TEMPLATE = r"""
{% extends 'dashboard/perfume_admin_base.html' %}
{% block admin_title %}افزودن عطر جدید{% endblock %}
{% block admin_content %}
<section class="pa-product-form-page">
  <div class="pa-page-hero"><div><span class="pa-eyebrow">NEW FRAGRANCE</span><h1>افزودن عطر جدید</h1><p>محصول را مثل یک فروشگاه عطر ثبت کن؛ برند، غلظت، خانواده رایحه، حجم، قیمت، تصویر و تنوع‌ها.</p></div><a class="pa-ghost-link" href="{% url 'first:admin_products' %}"><i class="fa-solid fa-arrow-right"></i>بازگشت به عطرها</a></div>
  <form class="pa-product-form" method="post" enctype="multipart/form-data" novalidate>{% csrf_token %}
    <section class="pa-form-card"><div class="pa-form-card-head"><span><i class="fa-solid fa-spray-can-sparkles"></i></span><div><h2>هویت رایحه</h2><p>اطلاعات اصلی محصول که در صفحه فروشگاه نمایش داده می‌شود.</p></div></div><div class="pa-form-grid">
      <label class="pa-field pa-span-2"><span>نام عطر *</span><input name="name" required placeholder="مثلاً Velora Noir Eau de Parfum" value="{{ form_data.name|default:'' }}"></label>
      <label class="pa-field"><span>دسته‌بندی</span><select name="category"><option value="">بدون دسته‌بندی</option>{% for category in categories %}<option value="{{ category.id }}" {% if form_data.category == category.id|stringformat:'s' %}selected{% endif %}>{{ category.name }}</option>{% endfor %}</select></label>
      <label class="pa-field"><span>برند عطر</span><select name="brand"><option value="">بدون برند</option>{% for brand in brands %}<option value="{{ brand.id }}" {% if form_data.brand == brand.id|stringformat:'s' %}selected{% endif %}>{{ brand.name }}</option>{% endfor %}</select></label>
      <label class="pa-field"><span>غلظت / نوع رایحه</span><select name="product_type"><option value="">بدون نوع</option>{% for product_type in product_types %}<option value="{{ product_type.id }}" {% if form_data.product_type == product_type.id|stringformat:'s' %}selected{% endif %}>{{ product_type.name }}</option>{% endfor %}</select></label>
      <label class="pa-field"><span>موجودی محصول ساده</span><input name="stock" type="number" min="0" inputmode="numeric" value="{{ form_data.stock|default:'0' }}"></label>
      <label class="pa-field pa-span-2"><span>خلاصه رایحه</span><textarea name="short_description" rows="3" placeholder="یک توضیح کوتاه برای کارت محصول...">{{ form_data.short_description|default:'' }}</textarea></label>
      <label class="pa-field pa-span-2"><span>توضیحات کامل</span><textarea name="description" rows="7" placeholder="حس رایحه، موقعیت استفاده، ماندگاری، پخش بو و توضیحات محصول...">{{ form_data.description|default:'' }}</textarea></label>
    </div></section>
    <section class="pa-form-card"><div class="pa-form-card-head"><span><i class="fa-solid fa-tags"></i></span><div><h2>قیمت و جایگاه فروش</h2><p>قیمت پایه، تخفیف و وضعیت نمایش در فروشگاه.</p></div></div><div class="pa-form-grid">
      <label class="pa-field"><span>قیمت اصلی *</span><input name="price" required type="number" min="0" inputmode="decimal" placeholder="مثلاً 3500000" value="{{ form_data.price|default:'' }}"></label>
      <label class="pa-field"><span>قیمت تخفیف‌خورده</span><input name="discount_price" type="number" min="0" inputmode="decimal" placeholder="اختیاری" value="{{ form_data.discount_price|default:'' }}"></label>
      <label class="pa-field pa-span-2"><span>تگ‌های رایحه</span><select name="tags" multiple size="7">{% for tag in tags %}<option value="{{ tag.id }}">{{ tag.name }}</option>{% endfor %}</select><small>مثلاً گرم، خنک، چوبی، مرکباتی، رسمی، روزمره.</small></label>
      <div class="pa-check-grid pa-span-2"><label><input type="checkbox" name="is_active" checked> فعال در فروشگاه</label><label><input type="checkbox" name="is_featured"> پیشنهاد ویژه</label><label><input type="checkbox" name="is_new"> رایحه جدید</label><label><input type="checkbox" name="is_best_seller"> پرفروش</label></div>
    </div></section>
    <section class="pa-form-card"><div class="pa-form-card-head"><span><i class="fa-solid fa-image"></i></span><div><h2>تصاویر محصول</h2><p>تصویر اصلی و گالری محصول. اولین تصویر به‌صورت پیش‌فرض تصویر اصلی است.</p></div></div><label class="pa-upload-box"><input type="file" name="product_images" accept="image/*" multiple required data-pa-product-images><input type="hidden" name="main_image_index" value="0"><i class="fa-solid fa-cloud-arrow-up"></i><strong>تصاویر عطر را انتخاب کن</strong><small>حداکثر ۸ تصویر؛ JPG، PNG یا WEBP</small></label><div class="pa-image-preview" data-pa-image-preview></div></section>
    <section class="pa-form-card"><div class="pa-form-card-head"><span><i class="fa-solid fa-flask"></i></span><div><h2>تنوع‌های عطر</h2><p>برای حجم‌های ۳۰، ۵۰، ۱۰۰ میل یا ظاهر/رنگ شیشه، تنوع جدا ثبت کن.</p></div></div><label class="pa-switch-row"><input type="checkbox" name="has_variants" data-pa-has-variants><span>این عطر چند تنوع دارد</span></label><div class="pa-variants" data-pa-variants hidden><div class="pa-variant-head"><strong>تنوع‌ها</strong><button type="button" class="pa-small-gold" data-pa-add-variant><i class="fa-solid fa-plus"></i>افزودن تنوع</button></div><div data-pa-variant-list></div></div></section>
    <div class="pa-form-actions"><a class="pa-btn ghost" href="{% url 'first:admin_products' %}">انصراف</a><button class="pa-btn gold" type="submit"><i class="fa-solid fa-check"></i>ثبت عطر</button></div>
  </form>
</section>
<template id="pa-variant-template"><article class="pa-variant-row"><input type="hidden" name="variant_keys" value=""><input type="hidden" name="variant_ids" value=""><label><span>ظاهر / رنگ شیشه</span><select name="variant_colors"><option value="">بدون رنگ</option>{% for color in colors %}<option value="{{ color.id }}">{{ color.name }}</option>{% endfor %}</select></label><label><span>حجم میل</span><input name="variant_volumes" type="number" min="0" placeholder="100"></label><label><span>عنوان سایز</span><input name="variant_sizes" placeholder="Full Size / Sample"></label><label><span>قیمت تنوع</span><input name="variant_prices" type="number" min="0" placeholder="اختیاری"></label><label><span>قیمت تخفیف</span><input name="variant_discount_prices" type="number" min="0" placeholder="اختیاری"></label><label><span>موجودی</span><input name="variant_stocks" type="number" min="0" value="0"></label><label><span>تصویر تنوع</span><input type="file" name="variant_image_0" accept="image/*"></label><label class="pa-radio-default"><input type="radio" name="variant_default" value="0"><span>پیش‌فرض</span></label><button type="button" class="pa-remove-variant" data-pa-remove-variant title="حذف تنوع"><i class="fa-solid fa-trash"></i></button></article></template>
<script>(()=>{const i=document.querySelector('[data-pa-product-images]'),p=document.querySelector('[data-pa-image-preview]');i?.addEventListener('change',()=>{p.innerHTML='';[...i.files].slice(0,8).forEach((f,n)=>{const c=document.createElement('div');c.className='pa-image-thumb';const im=document.createElement('img');im.src=URL.createObjectURL(f);im.alt=f.name;const b=document.createElement('span');b.textContent=n===0?'تصویر اصلی':`گالری ${n+1}`;c.append(im,b);p.append(c)})});const h=document.querySelector('[data-pa-has-variants]'),v=document.querySelector('[data-pa-variants]'),l=document.querySelector('[data-pa-variant-list]'),t=document.getElementById('pa-variant-template');function r(){[...l.children].forEach((row,n)=>{row.querySelector('input[name="variant_keys"]').value=`variant-${n}-${Date.now()}`;row.querySelectorAll('input,select').forEach(inp=>{if(inp.type==='file')inp.name=`variant_image_${n}`;if(inp.name==='variant_default')inp.value=String(n)});const radio=row.querySelector('input[name="variant_default"]');if(n===0&&!l.querySelector('input[name="variant_default"]:checked'))radio.checked=true})}function a(){l.append(t.content.cloneNode(true));r()}h?.addEventListener('change',()=>{v.hidden=!h.checked;if(h.checked&&!l.children.length)a()});document.querySelector('[data-pa-add-variant]')?.addEventListener('click',a);l?.addEventListener('click',e=>{const b=e.target.closest('[data-pa-remove-variant]');if(!b)return;b.closest('.pa-variant-row')?.remove();r()})})();</script>
{% endblock %}
"""

ADMIN_JS_TEXT = r"""
(() => {
  "use strict";
  const sidebar=document.querySelector("[data-pa-sidebar]");
  const overlay=document.querySelector("[data-pa-overlay]");
  function openSidebar(){sidebar?.classList.add("open");overlay?.classList.add("show");document.body.style.overflow="hidden"}
  function closeSidebar(){sidebar?.classList.remove("open");overlay?.classList.remove("show");document.body.style.overflow=""}
  function toggleTheme(){const r=document.documentElement;const next=(r.dataset.perfumeTheme||"night")==="night"?"day":"night";r.dataset.perfumeTheme=next;try{localStorage.setItem("velora-theme",next);localStorage.setItem("perfume-theme",next);localStorage.setItem("theme",next)}catch(_){}}
  document.addEventListener("click",e=>{if(e.target.closest("[data-pa-open]")){openSidebar();return}if(e.target.closest("[data-pa-close]")||e.target.closest("[data-pa-overlay]")){closeSidebar();return}if(e.target.closest("[data-pa-theme]")){toggleTheme();return}const c=e.target.closest("[data-pa-message-close]");if(c)c.closest(".pa-message")?.remove();const m=e.target.closest(".pa-account-menu");document.querySelectorAll(".pa-account-menu[open]").forEach(x=>{if(x!==m)x.removeAttribute("open")})});
  document.addEventListener("keydown",e=>{if(e.key==="Escape"){closeSidebar();document.querySelectorAll(".pa-account-menu[open]").forEach(x=>x.removeAttribute("open"))}});
})();
"""

ADMIN_CSS_TEXT = r"""
:root{--pa-bg:#070604;--pa-bg-soft:#0d0907;--pa-panel:#15100c;--pa-panel-2:#1e160f;--pa-panel-3:#2a1d12;--pa-text:#fff8ed;--pa-heading:#fffaf3;--pa-muted:#b6aa99;--pa-faint:#7e715f;--pa-gold:#d7ad63;--pa-gold-2:#b7823c;--pa-gold-3:#f1d69a;--pa-brown:#6f4625;--pa-ivory:#f8efe2;--pa-line:rgba(215,173,99,.20);--pa-line-strong:rgba(215,173,99,.42);--pa-shadow:0 26px 80px rgba(0,0,0,.38);--pa-radius:28px}
html[data-perfume-theme=day]{--pa-bg:#f7efe3;--pa-bg-soft:#efe1d0;--pa-panel:#fffaf2;--pa-panel-2:#f1e3d1;--pa-panel-3:#e5d1ba;--pa-text:#22170f;--pa-heading:#120d09;--pa-muted:#6f614f;--pa-faint:#8f7a61;--pa-gold:#a87332;--pa-gold-2:#845122;--pa-gold-3:#c69550;--pa-line:rgba(116,80,39,.18);--pa-line-strong:rgba(116,80,39,.38);--pa-shadow:0 26px 72px rgba(100,70,34,.14)}
*{box-sizing:border-box}html,body{min-height:100%}body.pa-body{margin:0;background:radial-gradient(circle at 85% 5%,rgba(215,173,99,.16),transparent 32rem),radial-gradient(circle at 10% 15%,rgba(111,70,37,.16),transparent 28rem),linear-gradient(135deg,var(--pa-bg),var(--pa-bg-soft));color:var(--pa-text);font-family:Vazir,Tahoma,Arial,sans-serif;line-height:1.85}a{color:inherit;text-decoration:none}button,input,select,textarea{font-family:inherit}button{cursor:pointer}
.pa-shell{width:100%;min-height:100vh;display:grid;grid-template-columns:310px minmax(0,1fr)}.pa-sidebar{position:sticky;top:0;height:100vh;padding:24px 18px;border-left:1px solid var(--pa-line);background:linear-gradient(180deg,rgba(255,255,255,.035),transparent 28%),rgba(9,7,5,.88);backdrop-filter:blur(18px);z-index:20;overflow-y:auto}html[data-perfume-theme=day] .pa-sidebar{background:rgba(255,250,242,.88)}.pa-sidebar-brand{display:flex;align-items:center;gap:14px;padding:12px 10px 22px;border-bottom:1px solid var(--pa-line)}.pa-monogram,.pa-shop-mark{width:58px;height:58px;display:grid;place-items:center;border:1px solid var(--pa-line-strong);color:var(--pa-gold-3);background:radial-gradient(circle at 35% 25%,rgba(215,173,99,.22),transparent 42%),rgba(0,0,0,.25);font-family:Georgia,"Times New Roman",serif;font-size:34px;font-weight:800}html[data-perfume-theme=day] .pa-monogram,html[data-perfume-theme=day] .pa-shop-mark{color:var(--pa-gold-2);background:rgba(255,255,255,.55)}.pa-sidebar-brand strong,.pa-shop-brand strong{display:block;color:var(--pa-heading);font-size:1.15rem;font-weight:950}.pa-sidebar-brand small,.pa-shop-brand small{display:block;margin-top:1px;color:var(--pa-gold);font-size:.62rem;letter-spacing:.24em}
.pa-nav{display:grid;gap:8px;padding:22px 0}.pa-nav-link{min-height:48px;display:flex;align-items:center;gap:12px;padding:0 14px;border:1px solid transparent;border-radius:18px;color:var(--pa-muted);font-weight:850;transition:.2s}.pa-nav-link i{width:22px;text-align:center;color:var(--pa-gold)}.pa-nav-link:hover,.pa-nav-link.active{color:var(--pa-heading);border-color:var(--pa-line);background:linear-gradient(135deg,rgba(215,173,99,.16),rgba(111,70,37,.10));transform:translateX(-2px)}.pa-sidebar-foot{margin-top:auto;padding-top:16px;border-top:1px solid var(--pa-line);display:grid;gap:12px}.pa-sidebar-foot>a{min-height:46px;display:flex;align-items:center;gap:10px;padding:0 14px;border:1px solid var(--pa-line);border-radius:16px;color:var(--pa-gold-3)}.pa-owner-mini{display:flex;align-items:center;gap:10px;padding:12px;border-radius:18px;background:rgba(255,255,255,.035);border:1px solid var(--pa-line)}.pa-owner-avatar,.pa-account-avatar{width:38px;height:38px;display:grid;place-items:center;border-radius:50%;background:linear-gradient(135deg,var(--pa-gold),var(--pa-brown));color:#100a05;font-weight:950}.pa-owner-mini strong{display:block}.pa-owner-mini small{display:block;color:var(--pa-muted);font-size:.72rem}
.pa-main{min-width:0}.pa-topbar{position:sticky;top:0;z-index:18;min-height:92px;display:grid;grid-template-columns:auto minmax(260px,560px) auto;align-items:center;gap:22px;padding:16px 32px;border-bottom:1px solid var(--pa-line);background:rgba(9,7,5,.78);backdrop-filter:blur(18px)}html[data-perfume-theme=day] .pa-topbar{background:rgba(255,250,242,.84)}.pa-topbar-start,.pa-topbar-actions,.pa-shop-brand{display:flex;align-items:center;gap:12px}.pa-menu-button,.pa-sidebar-close,.pa-icon-button{width:48px;height:48px;display:grid;place-items:center;border:1px solid var(--pa-line);border-radius:15px;background:rgba(255,255,255,.035);color:var(--pa-text);transition:.2s}.pa-menu-button:hover,.pa-icon-button:hover{border-color:var(--pa-line-strong);color:var(--pa-gold-3);transform:translateY(-2px)}.pa-menu-button,.pa-sidebar-close{display:none}.pa-admin-search{height:54px;display:grid;grid-template-columns:54px 1fr;border:1px solid var(--pa-line);border-radius:18px;overflow:hidden;background:rgba(255,255,255,.035)}html[data-perfume-theme=day] .pa-admin-search{background:rgba(255,255,255,.62)}.pa-admin-search button{border:0;border-left:1px solid var(--pa-line);background:transparent;color:var(--pa-gold);font-size:1.05rem}.pa-admin-search input{width:100%;border:0;outline:0;background:transparent;color:var(--pa-text);padding:0 18px}.pa-admin-search input::placeholder{color:var(--pa-faint)}
.pa-account-menu{position:relative}.pa-account-menu summary{list-style:none;min-height:48px;display:flex;align-items:center;gap:9px;padding:6px 10px 6px 16px;border:1px solid var(--pa-line);border-radius:16px;background:rgba(255,255,255,.035);color:var(--pa-heading);font-weight:900;cursor:pointer}.pa-account-menu summary::-webkit-details-marker{display:none}.pa-account-dropdown{position:absolute;top:calc(100% + 12px);left:0;width:270px;padding:12px;border:1px solid var(--pa-line);border-radius:20px;background:rgba(14,10,7,.96);box-shadow:var(--pa-shadow);z-index:40}html[data-perfume-theme=day] .pa-account-dropdown{background:rgba(255,250,242,.98)}.pa-account-head{padding:10px 12px 14px;border-bottom:1px solid var(--pa-line);margin-bottom:8px}.pa-account-head strong{display:block;color:var(--pa-heading)}.pa-account-head small{color:var(--pa-muted);font-size:.78rem;overflow:hidden;text-overflow:ellipsis;display:block}.pa-account-dropdown a,.pa-account-dropdown button{width:100%;min-height:42px;display:flex;align-items:center;gap:10px;border:0;border-radius:14px;padding:0 12px;background:transparent;color:var(--pa-text);font-weight:850;text-align:right;transition:.2s}.pa-account-dropdown a:hover,.pa-account-dropdown button:hover{background:rgba(215,173,99,.12);color:var(--pa-gold-3)}.pa-account-dropdown form{margin:8px 0 0;padding-top:8px;border-top:1px solid var(--pa-line)}.pa-account-dropdown form button{color:#f0caa0}
.pa-messages{width:min(1280px,calc(100% - 56px));margin:22px auto 0;display:grid;gap:10px}.pa-message{display:flex;align-items:center;gap:10px;padding:13px 15px;border:1px solid var(--pa-line);border-radius:18px;background:rgba(255,255,255,.04)}.pa-message button{margin-right:auto;border:0;background:transparent;color:inherit}.pa-content{width:min(1280px,calc(100% - 56px));margin:0 auto;padding:38px 0 70px}.pa-eyebrow{display:inline-block;color:var(--pa-gold);font-size:.72rem;font-weight:950;letter-spacing:.22em}.pa-dashboard-hero,.pa-page-hero{min-height:250px;display:flex;align-items:center;justify-content:space-between;gap:24px;padding:clamp(26px,4vw,48px);border:1px solid var(--pa-line);border-radius:var(--pa-radius);background:radial-gradient(circle at 12% 20%,rgba(215,173,99,.18),transparent 26rem),linear-gradient(135deg,rgba(255,255,255,.07),rgba(255,255,255,.018)),var(--pa-panel);box-shadow:var(--pa-shadow);position:relative;overflow:hidden}.pa-dashboard-hero:after,.pa-page-hero:after{content:"";position:absolute;inset:18px;border:1px solid rgba(215,173,99,.10);border-radius:calc(var(--pa-radius) - 10px);pointer-events:none}.pa-dashboard-hero h1,.pa-page-hero h1{margin:8px 0 10px;color:var(--pa-heading);font-size:clamp(2rem,4vw,4.2rem);line-height:1.28;font-weight:950}.pa-dashboard-hero p,.pa-page-hero p{max-width:760px;margin:0;color:var(--pa-muted);font-size:1rem}.pa-owner-seal{width:150px;height:150px;display:grid;place-items:center;gap:8px;border:1px solid var(--pa-line-strong);border-radius:50%;color:var(--pa-gold-3);background:radial-gradient(circle,rgba(215,173,99,.22),rgba(111,70,37,.08));font-weight:950;text-align:center}.pa-owner-seal i{display:block;font-size:2.2rem}
.pa-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin-top:22px}.pa-metrics article,.pa-secondary-metrics>div,.pa-action-card,.pa-panel-card,.pa-form-card{border:1px solid var(--pa-line);border-radius:24px;background:linear-gradient(135deg,rgba(255,255,255,.065),rgba(255,255,255,.018)),var(--pa-panel);box-shadow:0 18px 48px rgba(0,0,0,.16)}.pa-metrics article{min-height:140px;padding:24px;position:relative;overflow:hidden}.pa-metrics article:after{content:"";position:absolute;width:86px;height:86px;left:-24px;bottom:-24px;border-radius:50%;background:rgba(215,173,99,.10)}.pa-metrics span{width:48px;height:48px;display:grid;place-items:center;border-radius:16px;color:var(--pa-gold-3);background:rgba(215,173,99,.12)}.pa-metrics small{display:block;margin-top:16px;color:var(--pa-muted);font-weight:850}.pa-metrics strong{display:block;margin-top:4px;color:var(--pa-heading);font-size:2.2rem;line-height:1;font-weight:950}.pa-metrics em{color:var(--pa-muted);font-size:.76rem;font-style:normal}.pa-secondary-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:18px}.pa-secondary-metrics>div{display:flex;align-items:center;gap:14px;min-height:92px;padding:20px}.pa-secondary-metrics i{width:45px;height:45px;display:grid;place-items:center;border-radius:15px;color:var(--pa-gold-3);background:rgba(215,173,99,.12)}.pa-secondary-metrics small{display:block;color:var(--pa-muted)}.pa-secondary-metrics strong{color:var(--pa-heading);font-size:1.6rem}.pa-panel-section,.pa-panel-card{margin-top:22px;padding:24px}.pa-section-title,.pa-card-head{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;margin-bottom:18px}.pa-section-title h2,.pa-card-head h2,.pa-form-card-head h2{margin:4px 0 0;color:var(--pa-heading);font-size:1.45rem;font-weight:950}.pa-section-title p{margin:0;color:var(--pa-muted)}.pa-card-head a{color:var(--pa-gold-3);font-weight:900}.pa-action-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.pa-action-card{min-height:138px;padding:20px;display:grid;grid-template-columns:52px 1fr auto;align-items:center;gap:14px;transition:.2s}.pa-action-card:hover{transform:translateY(-4px);border-color:var(--pa-line-strong);box-shadow:var(--pa-shadow)}.pa-action-icon{width:52px;height:52px;display:grid;place-items:center;border-radius:18px;color:var(--pa-gold-3);background:rgba(215,173,99,.12);font-size:1.2rem}.pa-action-copy strong{display:block;color:var(--pa-heading);font-weight:950}.pa-action-copy small{display:block;margin-top:4px;color:var(--pa-muted);font-size:.78rem}.pa-action-arrow{color:var(--pa-gold)}
.pa-dashboard-columns{display:grid;grid-template-columns:1fr 1fr;gap:22px}.pa-list{display:grid;gap:12px}.pa-list-row{display:grid;grid-template-columns:52px 1fr auto;align-items:center;gap:14px;padding:13px;border:1px solid var(--pa-line);border-radius:18px;background:rgba(255,255,255,.025)}.pa-list-icon,.pa-product-thumb{width:52px;height:52px;display:grid;place-items:center;border-radius:15px;color:var(--pa-gold-3);background:rgba(215,173,99,.12);overflow:hidden}.pa-product-thumb img{width:100%;height:100%;object-fit:cover}.pa-list-copy strong{display:block;color:var(--pa-heading)}.pa-list-copy small{color:var(--pa-muted)}.pa-row-value{color:var(--pa-gold-3);white-space:nowrap}.pa-row-value small{color:var(--pa-muted);font-size:.7rem}.pa-empty{min-height:150px;display:grid;place-items:center;text-align:center;color:var(--pa-muted);border:1px dashed var(--pa-line);border-radius:20px}.pa-empty i{font-size:2rem;color:var(--pa-gold)}.pa-user-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.pa-user-grid article{min-height:110px;padding:18px;border:1px solid var(--pa-line);border-radius:18px;background:rgba(255,255,255,.025)}.pa-user-grid article span{width:42px;height:42px;display:grid;place-items:center;border-radius:50%;background:rgba(215,173,99,.13);color:var(--pa-gold-3);font-weight:950}.pa-user-grid article strong{display:block;margin-top:10px;color:var(--pa-heading)}.pa-user-grid article small{color:var(--pa-muted)}
.pa-ghost-link,.pa-btn,.pa-small-gold{min-height:46px;display:inline-flex;align-items:center;justify-content:center;gap:9px;border-radius:15px;padding:0 18px;font-weight:950}.pa-ghost-link,.pa-btn.ghost{border:1px solid var(--pa-line);color:var(--pa-text);background:rgba(255,255,255,.035)}.pa-btn.gold,.pa-small-gold{border:1px solid var(--pa-line-strong);color:#150d06;background:linear-gradient(135deg,var(--pa-gold-3),var(--pa-gold-2));box-shadow:0 16px 40px rgba(215,173,99,.18)}.pa-product-form-page,.pa-product-form{display:grid;gap:22px}.pa-form-card{padding:28px}.pa-form-card-head{display:flex;align-items:center;gap:14px;margin-bottom:24px;padding-bottom:18px;border-bottom:1px solid var(--pa-line)}.pa-form-card-head>span{width:54px;height:54px;display:grid;place-items:center;border-radius:18px;background:rgba(215,173,99,.12);color:var(--pa-gold-3);font-size:1.25rem}.pa-form-card-head p{margin:3px 0 0;color:var(--pa-muted)}.pa-form-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.pa-span-2{grid-column:span 2}.pa-field{display:grid;gap:8px;color:var(--pa-heading);font-weight:900}.pa-field small{color:var(--pa-muted);font-weight:500}.pa-field input,.pa-field select,.pa-field textarea,.pa-variant-row input,.pa-variant-row select{width:100%;min-height:52px;border:1px solid var(--pa-line);border-radius:16px;outline:0;background:rgba(255,255,255,.055);color:var(--pa-text);padding:0 15px;transition:.18s}html[data-perfume-theme=day] .pa-field input,html[data-perfume-theme=day] .pa-field select,html[data-perfume-theme=day] .pa-field textarea,html[data-perfume-theme=day] .pa-variant-row input,html[data-perfume-theme=day] .pa-variant-row select{background:rgba(255,255,255,.72)}.pa-field textarea{padding:14px 15px;resize:vertical}.pa-field input:focus,.pa-field select:focus,.pa-field textarea:focus,.pa-variant-row input:focus,.pa-variant-row select:focus{border-color:var(--pa-line-strong);box-shadow:0 0 0 4px rgba(215,173,99,.10)}.pa-check-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.pa-check-grid label,.pa-switch-row{min-height:54px;display:flex;align-items:center;gap:10px;border:1px solid var(--pa-line);border-radius:16px;padding:0 14px;background:rgba(255,255,255,.035);color:var(--pa-text);font-weight:850}.pa-check-grid input,.pa-switch-row input,.pa-radio-default input{accent-color:var(--pa-gold-2)}.pa-upload-box{min-height:210px;display:grid;place-items:center;text-align:center;gap:8px;border:1px dashed var(--pa-line-strong);border-radius:24px;background:radial-gradient(circle at center,rgba(215,173,99,.12),transparent 28rem),rgba(255,255,255,.025);color:var(--pa-text);cursor:pointer}.pa-upload-box input[type=file]{display:none}.pa-upload-box i{font-size:2.4rem;color:var(--pa-gold)}.pa-upload-box strong{color:var(--pa-heading);font-size:1.2rem}.pa-upload-box small{color:var(--pa-muted)}.pa-image-preview{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:12px;margin-top:14px}.pa-image-thumb{position:relative;aspect-ratio:1;border:1px solid var(--pa-line);border-radius:18px;overflow:hidden;background:rgba(255,255,255,.035)}.pa-image-thumb img{width:100%;height:100%;object-fit:cover}.pa-image-thumb span{position:absolute;right:8px;bottom:8px;padding:5px 8px;border-radius:999px;background:rgba(9,7,5,.75);color:var(--pa-gold-3);font-size:.68rem;font-weight:900}.pa-variants{margin-top:16px;display:grid;gap:14px}.pa-variant-head{display:flex;align-items:center;justify-content:space-between;gap:12px}.pa-variant-row{position:relative;display:grid;grid-template-columns:1.1fr .7fr .8fr .8fr .8fr .7fr 1fr auto auto;gap:12px;align-items:end;padding:16px;border:1px solid var(--pa-line);border-radius:20px;background:rgba(255,255,255,.028)}.pa-variant-row label{display:grid;gap:7px;color:var(--pa-heading);font-weight:850}.pa-variant-row label span{font-size:.76rem;color:var(--pa-muted)}.pa-radio-default{min-height:52px;display:flex!important;align-items:center;justify-content:center;border:1px solid var(--pa-line);border-radius:16px;padding:0 10px}.pa-remove-variant{width:52px;height:52px;border:1px solid rgba(215,173,99,.30);border-radius:16px;background:rgba(111,70,37,.18);color:var(--pa-gold-3)}.pa-form-actions{position:sticky;bottom:16px;z-index:10;display:flex;align-items:center;justify-content:flex-end;gap:12px;padding:14px;border:1px solid var(--pa-line);border-radius:22px;background:rgba(9,7,5,.78);backdrop-filter:blur(16px)}html[data-perfume-theme=day] .pa-form-actions{background:rgba(255,250,242,.82)}
.pa-body [class*=pink],.pa-body [class*=rose],.pa-body [class*=fuchsia],.pa-body [class*=purple]{border-color:var(--pa-line)!important}.pa-body [class*=text-pink],.pa-body [class*=text-rose],.pa-body [class*=text-fuchsia],.pa-body [class*=text-purple]{color:var(--pa-gold)!important}.pa-body [class*=bg-pink],.pa-body [class*=bg-rose],.pa-body [class*=bg-fuchsia],.pa-body [class*=bg-purple],.pa-body [class*=bg-blue],.pa-body [class*=bg-green]{background:linear-gradient(135deg,var(--pa-gold-3),var(--pa-gold-2))!important;color:#140d07!important}.pa-body [class*=from-pink],.pa-body [class*=from-rose],.pa-body [class*=from-purple],.pa-body [class*=from-fuchsia],.pa-body [class*=from-blue],.pa-body [class*=from-green]{--tw-gradient-from:var(--pa-gold-3)!important;--tw-gradient-to:rgba(215,173,99,0)!important;--tw-gradient-stops:var(--tw-gradient-from),var(--tw-gradient-to)!important}.pa-body [class*=to-pink],.pa-body [class*=to-rose],.pa-body [class*=to-purple],.pa-body [class*=to-fuchsia],.pa-body [class*=to-blue],.pa-body [class*=to-green]{--tw-gradient-to:var(--pa-gold-2)!important}.pa-body [class*=border-pink],.pa-body [class*=border-rose],.pa-body [class*=border-purple],.pa-body [class*=border-fuchsia]{border-color:var(--pa-line-strong)!important}.pa-body [class*=shadow-pink],.pa-body [class*=shadow-purple]{box-shadow:0 18px 48px rgba(116,80,39,.18)!important}.pa-body .container,.pa-body .max-w-7xl,.pa-body .max-w-6xl,.pa-body .max-w-5xl{width:min(1280px,calc(100% - 48px))!important;margin-left:auto!important;margin-right:auto!important}.pa-body table{color:var(--pa-text)}.pa-body th{color:var(--pa-heading)}.pa-body td{color:var(--pa-muted)}
@media(max-width:1120px){.pa-shell{grid-template-columns:1fr}.pa-sidebar{position:fixed;inset:0 0 0 auto;width:min(330px,88vw);transform:translateX(105%);transition:.25s}.pa-sidebar.open{transform:none}.pa-sidebar-close{display:grid;position:absolute;top:14px;left:14px}.pa-overlay{position:fixed;inset:0;z-index:19;background:rgba(0,0,0,.55);opacity:0;pointer-events:none;transition:.2s}.pa-overlay.show{opacity:1;pointer-events:auto}.pa-menu-button{display:grid}.pa-topbar{grid-template-columns:auto 1fr auto}.pa-dashboard-columns{grid-template-columns:1fr}.pa-action-grid{grid-template-columns:repeat(2,1fr)}.pa-metrics{grid-template-columns:repeat(2,1fr)}.pa-user-grid{grid-template-columns:repeat(2,1fr)}.pa-variant-row{grid-template-columns:repeat(2,1fr)}}
@media(max-width:720px){.pa-topbar{grid-template-columns:auto 1fr;padding:12px;gap:12px}.pa-admin-search{grid-column:1/-1;order:3}.pa-shop-mark{width:46px;height:46px;font-size:27px}.pa-shop-brand strong{font-size:.95rem}.pa-shop-brand small{font-size:.48rem}.pa-account-name{display:none}.pa-content{width:calc(100% - 24px);padding:24px 0 60px}.pa-dashboard-hero,.pa-page-hero{flex-direction:column;align-items:flex-start;min-height:auto;padding:24px}.pa-owner-seal{width:100px;height:100px}.pa-metrics,.pa-secondary-metrics,.pa-action-grid,.pa-user-grid,.pa-form-grid,.pa-check-grid{grid-template-columns:1fr}.pa-span-2{grid-column:auto}.pa-form-card{padding:18px}.pa-section-title,.pa-card-head{align-items:flex-start;flex-direction:column}.pa-list-row{grid-template-columns:48px 1fr}.pa-row-value{grid-column:2}.pa-form-actions{position:static;flex-direction:column;align-items:stretch}.pa-variant-row{grid-template-columns:1fr}}
"""


def replace_file_text(path: Path, replacements: dict[str, str]) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    original = text
    for old, new in replacements.items():
        text = text.replace(old, new)
    if text != original:
        backup(path)
        path.write_text(text, encoding="utf-8")
        print("[PATCH] palette/copy ->", path.relative_to(ROOT).as_posix())
        return True
    return False


def sweep_palette() -> None:
    targets = []
    if STATIC_CSS_DIR.exists():
        targets.extend(STATIC_CSS_DIR.rglob("*.css"))
    if DASHBOARD.exists():
        targets.extend(DASHBOARD.rglob("*.html"))
    analytics_tpl = ROOT / "first" / "templates" / "analytics"
    if analytics_tpl.exists():
        targets.extend(analytics_tpl.rglob("*.html"))
    if ANALYTICS_VIEWS.exists():
        targets.append(ANALYTICS_VIEWS)
    for path in sorted(set(targets)):
        replace_file_text(path, COLOR_REPLACEMENTS)


def main() -> None:
    print("=" * 88)
    print(" PHASE 11 — PERFUME OWNER CONSOLE POLISH")
    print("=" * 88)
    required = [ROOT / "manage.py", URLS, DASHBOARD]
    missing = [p for p in required if not p.exists()]
    if missing:
        fail("Put this script beside manage.py. Missing:\n" + "\n".join(str(p) for p in missing))
    BACKUP.mkdir(parents=True, exist_ok=True)

    snapshot = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in PROTECTED_BACKEND if p.exists()}
    names = route_names()
    owner = (OWNER_TEMPLATE
        .replace("__QUICK_ACTIONS__", make_quick_actions(names))
        .replace("__ORDERS_MORE__", more_link(names, "admin_orders", "مشاهده سفارش‌ها"))
        .replace("__PRODUCTS_MORE__", more_link(names, "admin_products", "مدیریت عطرها"))
        .replace("__USERS_MORE__", more_link(names, "admin_users", "مشاهده مشتریان")))
    admin_base = (ADMIN_BASE_TEMPLATE
        .replace("__DASHBOARD_ASSETS__", dashboard_assets())
        .replace("__NAV__", make_nav(names))
        .replace("__USER_MENU__", make_user_menu(names)))

    write(ADMIN_CSS, ADMIN_CSS_TEXT)
    write(ADMIN_JS, ADMIN_JS_TEXT)
    write(ADMIN_BASE, admin_base)
    write(OWNER_PANEL, owner)
    write(ADMIN_DASHBOARD, owner)
    write(ADMIN_ADD_PRODUCT, ADD_PRODUCT_TEMPLATE)
    sweep_palette()

    for rel, before in snapshot.items():
        path = ROOT / rel
        if path.exists() and path.read_bytes() != before:
            fail(f"Protected backend file changed unexpectedly: {rel}")
    if ANALYTICS_VIEWS.exists():
        ast.parse(ANALYTICS_VIEWS.read_text(encoding="utf-8"))
        print("[PYTHON OK]", ANALYTICS_VIEWS.relative_to(ROOT).as_posix())

    run(sys.executable, "manage.py", "check")
    run(sys.executable, "manage.py", "makemigrations", "--check", "--dry-run")
    run(sys.executable, "manage.py", "shell", "-c", "from django.template.loader import get_template; [get_template(x) for x in ['dashboard/perfume_admin_base.html','dashboard/owner_panel.html','dashboard/admin_dashboard.html','dashboard/admin_add_product.html']]; print('PHASE 11 TEMPLATES OK')")

    print("\n" + "=" * 88)
    print(" PHASE 11 READY")
    print("=" * 88)
    print("✓ پنل مالک و /admin-panel/ یکدست و لوکس شد")
    print("✓ داشبورد قدیمی از ناوبری حذف شد")
    print("✓ افزودن محصول جدید مخصوص فروشگاه عطر شد")
    print("✓ رنگ‌های صورتی/بنفش/رنگارنگ به قهوه‌ای، طلایی، مشکی و سفید گرم تبدیل شد")
    print("✓ منوی کلیک روی نام کاربر اضافه شد: پنل مالکیت، پروفایل، طراحی بصری، مشاهده سایت، خروج")
    print("✓ دیتابیس، مدل‌ها، URLها و منطق اصلی دست نخورده ماند")
    print("Backup:", BACKUP.relative_to(ROOT))
    print("\nRun: python manage.py runserver")
    print("Then: Ctrl + F5")


if __name__ == "__main__":
    main()
