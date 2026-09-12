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
BACKUP = ROOT / ".perfume_frontend_phase09_backup"

URLS = ROOT / "first/urls.py"
BASE = ROOT / "first/templates/perfume_base.html"
INDEX = ROOT / "first/templates/index.html"
DASHBOARD = ROOT / "first/templates/dashboard"

ADMIN_BASE = DASHBOARD / "perfume_admin_base.html"
OWNER_PANEL = DASHBOARD / "owner_panel.html"
CUSTOMIZER = DASHBOARD / "customizer.html"

ADMIN_CSS = ROOT / "static/css/perfume-admin-v1.css"
ADMIN_JS = ROOT / "static/js/perfume-admin-v1.js"
RUNTIME_JS = ROOT / "static/js/perfume-visual-runtime.js"
STUDIO_JS = ROOT / "static/js/perfume-visual-studio.js"

BACKEND_GUARD = [
    "first/views.py",
    "first/models.py",
    "first/urls.py",
    "first/forms.py",
    "first/decorators.py",
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
    if not dst.exists():
        shutil.copy2(path, dst)


def write(path: Path, content: str):
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    print("[WRITE]", path.relative_to(ROOT).as_posix())


def route_names():
    source = URLS.read_text(encoding="utf-8", errors="ignore")
    return set(re.findall(r"name\s*=\s*['\"]([A-Za-z0-9_:-]+)['\"]", source))


def dashboard_assets():
    if (ROOT / "static/css/tailwind.min.css").exists():
        return '<link rel="stylesheet" href="{% static \'css/tailwind.min.css\' %}">'
    if (ROOT / "static/vendor/tailwind/tailwindcss.js").exists():
        return '<script src="{% static \'vendor/tailwind/tailwindcss.js\' %}"></script>'
    return ""


def make_nav(names):
    candidates = [
        ("owner_panel", "نمای کلی", "fa-gauge-high"),
        ("admin_dashboard", "داشبورد مدیریت", "fa-chart-pie"),
        ("admin_products", "محصولات", "fa-box-open"),
        ("admin_orders", "سفارش‌ها", "fa-receipt"),
        ("admin_users", "کاربران", "fa-users"),
        ("admin_reviews", "نظرات", "fa-star"),
        ("warehouse", "انبار", "fa-warehouse"),
        ("warehouse_products", "موجودی محصولات", "fa-boxes-stacked"),
        ("analytics_dashboard", "آمار و گزارش", "fa-chart-line"),
        ("site_settings", "تنظیمات سایت", "fa-sliders"),
        ("number_format_settings", "فرمت اعداد", "fa-hashtag"),
        ("customizer", "طراحی بصری", "fa-wand-magic-sparkles"),
    ]
    parts = []
    for name, label, icon in candidates:
        if name not in names:
            continue
        parts.append(
            f'<a class="pa-nav-link {{% if request.resolver_match.url_name == \'{name}\' %}}active{{% endif %}}" '
            f'href="{{% url \'first:{name}\' %}}">'
            f'<i class="fa-solid {icon}"></i><span>{label}</span></a>'
        )
    return "\n".join(parts)


def make_quick_actions(names):
    candidates = [
        ("customizer", "طراحی بصری سایت", "ظاهر فروشگاه را با پیش‌نمایش زنده ویرایش کنید", "fa-wand-magic-sparkles", "gold"),
        ("admin_products", "مدیریت محصولات", "محصولات، قیمت‌ها و کالکشن‌های فروشگاه", "fa-box-open", ""),
        ("admin_orders", "سفارش‌ها", "بررسی سفارش‌های جدید و وضعیت ارسال", "fa-receipt", ""),
        ("warehouse", "انبار", "کنترل موجودی و کالاهای رو به اتمام", "fa-warehouse", ""),
        ("site_settings", "تنظیمات فروشگاه", "لوگو، اسلایدر، تماس و تنظیمات عمومی", "fa-sliders", ""),
        ("analytics_dashboard", "آمار فروش", "گزارش‌ها و عملکرد فروشگاه", "fa-chart-line", ""),
        ("admin_users", "کاربران", "مشتریان و حساب‌های مدیریتی", "fa-users", ""),
        ("admin_reviews", "نظرات", "مدیریت بازخورد و امتیاز محصولات", "fa-star", ""),
    ]
    parts = []
    for name, title, desc, icon, cls in candidates:
        if name not in names:
            continue
        parts.append(
            f'<a class="pa-action-card {cls}" href="{{% url \'first:{name}\' %}}">'
            f'<span class="pa-action-icon"><i class="fa-solid {icon}"></i></span>'
            f'<span class="pa-action-copy"><strong>{title}</strong><small>{desc}</small></span>'
            '<i class="fa-solid fa-arrow-left pa-action-arrow"></i></a>'
        )
    return "\n".join(parts)


def patch_dashboard_children():
    changed = []
    skipped = []
    for path in sorted(DASHBOARD.glob("*.html")):
        if path in {ADMIN_BASE, OWNER_PANEL, CUSTOMIZER}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        original = text
        extends = re.search(r"{%\s*extends\s+['\"][^'\"]+['\"]\s*%}", text)
        content_block = re.search(r"{%\s*block\s+content\s*%}", text)
        if not extends or not content_block:
            skipped.append(path.name)
            continue
        text = text[:extends.start()] + "{% extends 'dashboard/perfume_admin_base.html' %}" + text[extends.end():]
        text = re.sub(r"{%\s*block\s+content\s*%}", "{% block admin_content %}", text, count=1)
        if text != original:
            backup(path)
            path.write_text(text, encoding="utf-8")
            changed.append(path.name)
    print("[PATCH] Themed dashboard child templates:", len(changed))
    for name in changed:
        print("  -", name)
    if skipped:
        print("[INFO] Dashboard templates skipped because their structure is different:")
        for name in skipped:
            print("  -", name)


def inject_first_tag(text, tag, attrs):
    pattern = re.compile(rf"<{tag}\b([^>]*)>", flags=re.I)
    m = pattern.search(text)
    if not m:
        return text
    opening = m.group(0)
    if "data-bsg-edit=" in opening:
        return text
    return text[:m.start()] + opening[:-1] + " " + attrs + ">" + text[m.end():]


def patch_storefront_markers():
    text = BASE.read_text(encoding="utf-8")
    original = text

    text = inject_first_tag(text, "header", 'data-bsg-edit="site-header" data-bsg-name="هدر سایت" data-bsg-kind="box"')
    text = inject_first_tag(text, "main", 'data-bsg-edit="main-content" data-bsg-name="محتوای اصلی" data-bsg-kind="box"')
    text = inject_first_tag(text, "footer", 'data-bsg-edit="site-footer" data-bsg-name="فوتر سایت" data-bsg-kind="box"')

    visual_data = "{{ settings.customizer_rules|default:'[]'|json_script:'perfume-visual-rules' }}"
    theme_data = (
        '<div id="perfume-theme-values" hidden '
        'data-primary="{{ settings.primary_color|default:\'#C9954D\' }}" '
        'data-secondary="{{ settings.secondary_color|default:\'#75471F\' }}" '
        'data-accent="{{ settings.accent_color|default:\'#E3C286\' }}" '
        'data-bg="{{ settings.background_color|default:\'#090706\' }}" '
        'data-text="{{ settings.text_color|default:\'#F7F0E7\' }}"></div>'
    )
    runtime = '<script src="{% static \'js/perfume-visual-runtime.js\' %}"></script>'

    if "perfume-visual-rules" not in text:
        text = text.replace("</body>", "    " + visual_data + "\n</body>", 1)
    if 'id="perfume-theme-values"' not in text:
        text = text.replace("</body>", "    " + theme_data + "\n</body>", 1)
    if "perfume-visual-runtime.js" not in text:
        text = text.replace("</body>", "    " + runtime + "\n</body>", 1)

    if text != original:
        backup(BASE)
        BASE.write_text(text, encoding="utf-8")
        print("[PATCH] perfume_base.html -> visual runtime + editable regions")

    if not INDEX.exists():
        return

    text = INDEX.read_text(encoding="utf-8")
    original = text
    section_counter = 0
    used = {}

    def unique(base):
        used[base] = used.get(base, 0) + 1
        return base if used[base] == 1 else f"{base}-{used[base]}"

    def section_repl(match):
        nonlocal section_counter
        opening = match.group(0)
        if "data-bsg-edit=" in opening:
            return opening
        section_counter += 1
        attrs = match.group(1) or ""
        cm = re.search(r"class\s*=\s*['\"]([^'\"]+)['\"]", attrs, flags=re.I)
        classes = cm.group(1).lower() if cm else ""
        if "hero" in classes and "product" not in classes:
            base_id, label = "home-hero", "هرو صفحه اصلی"
        elif "categor" in classes:
            base_id, label = "home-categories", "دسته‌بندی‌های صفحه اصلی"
        elif "promo" in classes:
            base_id, label = "home-promotions", "پیشنهادهای صفحه اصلی"
        elif "guide" in classes:
            base_id, label = "home-guide", "راهنمای خرید"
        elif "brand" in classes:
            base_id, label = "home-brands", "برندها"
        elif "finder" in classes:
            base_id, label = "home-finder", "راهنمای رایحه"
        elif "product" in classes or "signature" in classes or "collection" in classes:
            base_id, label = "home-products", "بخش محصولات"
        else:
            base_id, label = "home-section", f"بخش {section_counter} صفحه اصلی"
        rid = unique(base_id)
        return opening[:-1] + f' data-bsg-edit="{rid}" data-bsg-name="{label}" data-bsg-kind="box">'

    text = re.sub(r"<section\b([^>]*)>", section_repl, text, flags=re.I)

    if 'data-bsg-edit="home-hero-title"' not in text:
        text = re.sub(
            r"<h1\b([^>]*)>",
            r'<h1\1 data-bsg-edit="home-hero-title" data-bsg-name="عنوان اصلی" data-bsg-kind="text">',
            text,
            count=1,
            flags=re.I,
        )

    h2_counter = 0
    def h2_repl(match):
        nonlocal h2_counter
        opening = match.group(0)
        if "data-bsg-edit=" in opening:
            return opening
        h2_counter += 1
        return opening[:-1] + f' data-bsg-edit="home-heading-{h2_counter}" data-bsg-name="عنوان بخش {h2_counter}" data-bsg-kind="text">'
    text = re.sub(r"<h2\b([^>]*)>", h2_repl, text, flags=re.I)

    image_counter = 0
    def img_repl(match):
        nonlocal image_counter
        opening = match.group(0)
        if "data-bsg-edit=" in opening or image_counter >= 8:
            return opening
        image_counter += 1
        return opening[:-1] + f' data-bsg-edit="home-image-{image_counter}" data-bsg-name="تصویر {image_counter}" data-bsg-kind="image">'
    text = re.sub(r"<img\b([^>]*)>", img_repl, text, flags=re.I)

    if text != original:
        backup(INDEX)
        INDEX.write_text(text, encoding="utf-8")
        print("[PATCH] index.html -> visual edit targets")


ADMIN_BASE_TEMPLATE = r"""
{% load static %}
<!doctype html>
<html lang="fa" dir="rtl" data-perfume-theme="night">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <title>{% block admin_title %}مدیریت فروشگاه{% endblock %} | {{ settings.site_name|default:'فروشگاه عطر' }}</title>
  <script>
  try{
    const t=localStorage.getItem("velora-theme")||localStorage.getItem("perfume-theme")||"night";
    document.documentElement.dataset.perfumeTheme=(t==="day"||t==="night")?t:"night";
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
    <button class="pa-sidebar-close" type="button" data-pa-close><i class="fa-solid fa-xmark"></i></button>
    <nav class="pa-nav">__NAV__</nav>
    <div class="pa-sidebar-foot">
      <a href="{% url 'first:home' %}"><i class="fa-solid fa-arrow-up-right-from-square"></i><span>مشاهده فروشگاه</span></a>
      <div class="pa-owner-mini">
        <span class="pa-owner-avatar">{{ user.username|first|upper }}</span>
        <span><strong>{{ user.username }}</strong><small>{% if user.is_superuser %}مالک فروشگاه{% else %}مدیر{% endif %}</small></span>
      </div>
    </div>
  </aside>

  <div class="pa-main">
    <header class="pa-topbar">
      <div class="pa-topbar-start">
        <button class="pa-menu-button" type="button" data-pa-open><i class="fa-solid fa-bars"></i></button>
        <div><span>MAISON DE PARFUM</span><strong>{% block admin_heading %}مدیریت فروشگاه{% endblock %}</strong></div>
      </div>
      <div class="pa-topbar-actions">
        <a class="pa-studio-link" href="{% url 'first:customizer' %}"><i class="fa-solid fa-wand-magic-sparkles"></i><span>طراحی بصری</span></a>
        <button class="pa-icon-button" type="button" data-pa-theme title="حالت روز/شب"><i class="fa-solid fa-circle-half-stroke"></i></button>
        <a class="pa-icon-button" href="{% url 'first:home' %}" title="فروشگاه"><i class="fa-solid fa-store"></i></a>
      </div>
    </header>

    {% if messages %}
    <div class="pa-messages">
      {% for message in messages %}
      <div class="pa-message {{ message.tags|default:'info' }}"><i class="fa-solid fa-circle-info"></i><span>{{ message }}</span><button type="button" data-pa-message-close><i class="fa-solid fa-xmark"></i></button></div>
      {% endfor %}
    </div>
    {% endif %}

    <main class="pa-content">{% block admin_content %}{% endblock %}</main>
  </div>
</section>
<div class="pa-overlay" data-pa-overlay></div>
<script src="{% static 'js/perfume-admin-v1.js' %}"></script>
{% block extra_js %}{% endblock %}
</body>
</html>
"""

OWNER_PANEL_TEMPLATE = r"""
{% extends 'dashboard/perfume_admin_base.html' %}
{% load custom_filters %}
{% block admin_title %}پنل مالک{% endblock %}
{% block admin_heading %}پنل مالک{% endblock %}
{% block admin_content %}
<div class="pa-owner-dashboard">
  <section class="pa-dashboard-hero">
    <div><span class="pa-eyebrow">OWNER OVERVIEW</span><h1>سلام {{ user.username }}،</h1><p>وضعیت فروشگاه عطر، سفارش‌ها، مشتریان و ظاهر سایت را از اینجا مدیریت کنید.</p></div>
    <div class="pa-owner-seal"><i class="fa-solid fa-crown"></i><span>OWNER</span></div>
  </section>

  <section class="pa-metrics">
    <article><span><i class="fa-solid fa-box-open"></i></span><small>محصولات</small><strong>{{ total_products|default:0 }}</strong></article>
    <article><span><i class="fa-solid fa-users"></i></span><small>کاربران</small><strong>{{ total_users|default:0 }}</strong></article>
    <article><span><i class="fa-solid fa-receipt"></i></span><small>سفارش‌ها</small><strong>{{ total_orders|default:0 }}</strong></article>
    <article class="gold"><span><i class="fa-solid fa-coins"></i></span><small>درآمد تاییدشده</small><strong>{{ total_revenue|default_if_none:0|price_format }}</strong><em>تومان</em></article>
  </section>

  <section class="pa-secondary-metrics">
    <div><i class="fa-regular fa-clock"></i><span><small>سفارش در انتظار</small><strong>{{ pending_orders|default:0 }}</strong></span></div>
    <div><i class="fa-regular fa-star"></i><span><small>نظر ثبت‌شده</small><strong>{{ total_reviews|default:0 }}</strong></span></div>
    <div><i class="fa-regular fa-heart"></i><span><small>علاقه‌مندی‌ها</small><strong>{{ total_wishlist|default:0 }}</strong></span></div>
  </section>

  <section class="pa-panel-section">
    <div class="pa-section-title"><div><span class="pa-eyebrow">MANAGEMENT</span><h2>مدیریت فروشگاه</h2></div><p>همه ابزارهای مدیریت در یکجا.</p></div>
    <div class="pa-action-grid">__QUICK_ACTIONS__</div>
  </section>

  <div class="pa-dashboard-columns">
    <section class="pa-panel-card">
      <div class="pa-card-head"><div><span class="pa-eyebrow">RECENT ORDERS</span><h2>آخرین سفارش‌ها</h2></div>__ORDERS_MORE__</div>
      <div class="pa-list">
        {% for order in recent_orders %}
        <article class="pa-list-row"><span class="pa-list-icon"><i class="fa-solid fa-bag-shopping"></i></span><span class="pa-list-copy"><strong>#{{ order.order_number }}</strong><small>{{ order.created_at|date:'Y/m/d H:i' }} · {{ order.get_status_display }}</small></span><strong class="pa-row-value">{{ order.total|price_format }} <small>تومان</small></strong></article>
        {% empty %}<div class="pa-empty"><i class="fa-solid fa-bag-shopping"></i><p>هنوز سفارشی ثبت نشده است.</p></div>{% endfor %}
      </div>
    </section>

    <section class="pa-panel-card">
      <div class="pa-card-head"><div><span class="pa-eyebrow">BEST SELLERS</span><h2>پرفروش‌ترین محصولات</h2></div>__PRODUCTS_MORE__</div>
      <div class="pa-list">
        {% for product in best_products %}
        <article class="pa-list-row"><span class="pa-product-thumb">{% if product.main_image %}<img src="{{ product.main_image.url }}" alt="{{ product.name }}">{% else %}<i class="fa-solid fa-spray-can-sparkles"></i>{% endif %}</span><span class="pa-list-copy"><strong>{{ product.name }}</strong><small>{{ product.sales_count|default:0 }} فروش</small></span><strong class="pa-row-value">{{ product.final_price|price_format }} <small>تومان</small></strong></article>
        {% empty %}<div class="pa-empty"><i class="fa-solid fa-box-open"></i><p>هنوز فروش محصولی ثبت نشده است.</p></div>{% endfor %}
      </div>
    </section>
  </div>

  <section class="pa-panel-card">
    <div class="pa-card-head"><div><span class="pa-eyebrow">NEW MEMBERS</span><h2>آخرین کاربران</h2></div>__USERS_MORE__</div>
    <div class="pa-user-grid">
      {% for member in recent_users %}
      <article><span class="pa-user-avatar">{{ member.username|first|upper }}</span><span><strong>{{ member.username }}</strong><small>{{ member.email|default:'بدون ایمیل' }}</small></span><time>{{ member.date_joined|date:'Y/m/d' }}</time></article>
      {% empty %}<div class="pa-empty"><p>کاربری وجود ندارد.</p></div>{% endfor %}
    </div>
  </section>
</div>
{% endblock %}
"""

CUSTOMIZER_TEMPLATE = r"""
{% load static %}
<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>استودیو طراحی | {{ settings.site_name|default:'فروشگاه عطر' }}</title>
  <link rel="stylesheet" href="{% static 'vendor/vazir/font-face.css' %}">
  <link rel="stylesheet" href="{% static 'vendor/fontawesome/css/all.min.css' %}">
  <link rel="stylesheet" href="{% static 'css/perfume-admin-v1.css' %}">
</head>
<body class="pa-studio-body">
<form class="pa-hidden-csrf">{% csrf_token %}</form>
<div class="pa-studio" data-studio data-save-url="{% url 'first:customizer_save' %}" data-upload-url="__UPLOAD_URL__">
  <header class="pa-studio-top">
    <div class="pa-studio-brand"><a href="{% url 'first:owner_panel' %}" title="بازگشت"><i class="fa-solid fa-arrow-right"></i></a><span class="pa-monogram">V</span><span><strong>استودیو طراحی بصری</strong><small>PERFUME VISUAL STUDIO</small></span></div>
    <div class="pa-device-switch"><button class="active" type="button" data-device="desktop"><i class="fa-solid fa-desktop"></i></button><button type="button" data-device="tablet"><i class="fa-solid fa-tablet-screen-button"></i></button><button type="button" data-device="mobile"><i class="fa-solid fa-mobile-screen"></i></button></div>
    <div class="pa-studio-actions"><button class="pa-secondary" type="button" data-studio-reset><i class="fa-solid fa-arrow-rotate-left"></i> بازنشانی</button><button class="pa-primary" type="button" data-studio-save><i class="fa-solid fa-floppy-disk"></i> ذخیره تغییرات</button></div>
  </header>

  <div class="pa-studio-grid">
    <aside class="pa-studio-panel">
      <section>
        <span class="pa-eyebrow">SITE PALETTE</span><h2>رنگ‌های برند</h2>
        <div class="pa-color-list"><label><span>طلایی اصلی</span><input type="color" data-theme-field="primary"></label><label><span>قهوه‌ای</span><input type="color" data-theme-field="secondary"></label><label><span>طلایی روشن</span><input type="color" data-theme-field="accent"></label><label><span>پس‌زمینه پایه</span><input type="color" data-theme-field="bg"></label><label><span>رنگ متن</span><input type="color" data-theme-field="text"></label></div>
      </section>

      <section>
        <span class="pa-eyebrow">SELECTED AREA</span><h2 data-selected-name>یک بخش را انتخاب کنید</h2><p class="pa-studio-help">در پیش‌نمایش روی بخش‌هایی که کادر طلایی دارند کلیک کنید.</p>
        <div class="pa-editor-fields" data-editor-fields hidden>
          <label data-text-field><span>متن</span><textarea rows="4" data-rule-text></textarea></label>
          <label data-image-field hidden><span>آدرس تصویر</span><input type="text" data-rule-src placeholder="/media/..."></label>
          <div class="pa-upload-box" data-upload-box hidden><input type="file" accept="image/*" data-rule-file><button type="button" class="pa-secondary full" data-rule-upload><i class="fa-solid fa-cloud-arrow-up"></i> آپلود تصویر</button></div>
          <div class="pa-field-pair"><label><span>رنگ متن</span><input type="color" data-style="color"></label><label><span>پس‌زمینه</span><input type="color" data-style="backgroundColor"></label></div>
          <div class="pa-field-pair"><label><span>اندازه متن</span><input type="text" placeholder="32px" data-style="fontSize"></label><label><span>گردی گوشه</span><input type="text" placeholder="18px" data-style="borderRadius"></label></div>
          <div class="pa-field-pair"><label><span>فاصله داخلی</span><input type="text" placeholder="24px" data-style="padding"></label><label><span>شفافیت</span><input type="number" min="0" max="1" step=".05" data-style="opacity"></label></div>
          <label><span>سایه</span><input type="text" placeholder="0 20px 60px rgba(0,0,0,.2)" data-style="boxShadow"></label>
          <label class="pa-check-row"><input type="checkbox" data-rule-hidden><span>مخفی کردن این بخش</span></label>
          <button class="pa-danger-soft" type="button" data-rule-clear>حذف تغییرات این بخش</button>
        </div>
      </section>

      <section><span class="pa-eyebrow">EDITABLE AREAS</span><div class="pa-region-list" data-region-list></div></section>
    </aside>

    <main class="pa-preview-shell"><div class="pa-preview-toolbar"><span><i class="fa-solid fa-circle"></i> پیش‌نمایش زنده فروشگاه</span><button type="button" data-preview-refresh><i class="fa-solid fa-rotate"></i></button></div><div class="pa-preview-frame desktop" data-preview-frame><iframe title="پیش‌نمایش فروشگاه" src="{% url 'first:home' %}?visual_preview=1" data-preview></iframe></div></main>
  </div>
  <div class="pa-studio-toast" data-studio-toast></div>
</div>
{{ customizer_payload|json_script:"pa-customizer-payload" }}
<script src="{% static 'js/perfume-visual-studio.js' %}"></script>
</body>
</html>
"""

ADMIN_CSS_TEXT = r"""
:root{--pa-bg:#0b0806;--pa-bg2:#100b08;--pa-panel:#17110d;--pa-panel2:#21160f;--pa-text:#f7efe6;--pa-muted:#aa9d90;--pa-gold:#c9954d;--pa-gold2:#e3c286;--pa-line:rgba(218,178,112,.18);--pa-line2:rgba(218,178,112,.38);--pa-shadow:0 28px 70px rgba(0,0,0,.28)}
html[data-perfume-theme="day"]{--pa-bg:#e8dacb;--pa-bg2:#dcc6ad;--pa-panel:#fffaf4;--pa-panel2:#f1e3d2;--pa-text:#19130f;--pa-muted:#75675b;--pa-gold:#9f6d2f;--pa-gold2:#b9853d;--pa-line:rgba(104,65,31,.14);--pa-line2:rgba(126,77,34,.32);--pa-shadow:0 24px 60px rgba(84,49,19,.12)}
*{box-sizing:border-box}.pa-body{margin:0;min-height:100vh;background:var(--pa-bg);color:var(--pa-text);font-family:Vazir,Tahoma,Arial,sans-serif}.pa-body a{text-decoration:none}.pa-body button,.pa-body input,.pa-body select,.pa-body textarea{font-family:inherit}
.pa-shell{min-height:100vh;display:grid;grid-template-columns:270px minmax(0,1fr);direction:rtl;background:radial-gradient(circle at 84% 7%,rgba(185,115,48,.08),transparent 24%),linear-gradient(180deg,var(--pa-bg),var(--pa-bg2))}
.pa-sidebar{min-height:100vh;position:sticky;top:0;z-index:35;padding:22px 16px;border-left:1px solid var(--pa-line);background:radial-gradient(circle at 30% 10%,rgba(193,126,58,.08),transparent 18%),var(--pa-panel);display:flex;flex-direction:column}.pa-sidebar-brand{min-height:72px;padding:0 8px 18px;display:flex;align-items:center;gap:11px;border-bottom:1px solid var(--pa-line)}.pa-monogram{width:48px;height:48px;border:1px solid var(--pa-line2);display:grid;place-items:center;color:var(--pa-gold2);font:700 25px Georgia,serif;background:linear-gradient(145deg,var(--pa-panel2),var(--pa-bg))}.pa-sidebar-brand strong,.pa-sidebar-brand small{display:block}.pa-sidebar-brand strong{font-size:13px}.pa-sidebar-brand small{margin-top:2px;color:var(--pa-gold);font-size:7px;letter-spacing:.18em}.pa-sidebar-close{display:none}
.pa-nav{margin-top:22px;display:grid;gap:5px}.pa-nav-link{min-height:47px;padding:0 13px;border:1px solid transparent;display:grid;grid-template-columns:29px 1fr;gap:9px;align-items:center;color:var(--pa-muted)!important;font-size:11px;transition:.2s}.pa-nav-link i{color:var(--pa-gold);text-align:center}.pa-nav-link:hover,.pa-nav-link.active{color:var(--pa-text)!important;border-color:var(--pa-line);background:linear-gradient(110deg,rgba(201,149,77,.13),transparent)}
.pa-sidebar-foot{margin-top:auto;padding-top:16px;border-top:1px solid var(--pa-line);display:grid;gap:10px}.pa-sidebar-foot>a{min-height:40px;padding:0 10px;display:flex;align-items:center;gap:9px;color:var(--pa-muted)!important;font-size:10px}.pa-owner-mini{padding:11px;border:1px solid var(--pa-line);display:flex;align-items:center;gap:9px}.pa-owner-avatar{width:36px;height:36px;border-radius:50%;display:grid;place-items:center;background:var(--pa-gold);color:#171008;font-weight:800}.pa-owner-mini strong,.pa-owner-mini small{display:block}.pa-owner-mini strong{font-size:11px}.pa-owner-mini small{color:var(--pa-muted);font-size:8px}
.pa-main{min-width:0}.pa-topbar{min-height:82px;padding:0 28px;position:sticky;top:0;z-index:28;border-bottom:1px solid var(--pa-line);background:var(--pa-panel);display:flex;align-items:center;justify-content:space-between;gap:20px}.pa-topbar-start{display:flex;align-items:center;gap:13px}.pa-topbar-start span,.pa-topbar-start strong{display:block}.pa-topbar-start span{color:var(--pa-gold);font-size:7px;letter-spacing:.2em}.pa-topbar-start strong{font-size:17px}.pa-menu-button,.pa-icon-button{width:42px;height:42px;border:1px solid var(--pa-line);background:var(--pa-panel2);color:var(--pa-text)!important;display:grid;place-items:center;cursor:pointer}.pa-menu-button{display:none}.pa-topbar-actions{display:flex;align-items:center;gap:7px}.pa-studio-link{min-height:42px;padding:0 14px;border:1px solid var(--pa-line2);background:linear-gradient(120deg,rgba(201,149,77,.16),rgba(117,71,31,.16));color:var(--pa-gold2)!important;display:flex;align-items:center;gap:8px;font-size:10px}
.pa-messages{width:min(1440px,calc(100% - 48px));margin:18px auto 0;display:grid;gap:7px}.pa-message{min-height:46px;padding:0 13px;border:1px solid var(--pa-line);background:var(--pa-panel);display:grid;grid-template-columns:22px 1fr 30px;align-items:center;gap:8px;font-size:10px}.pa-message>i{color:var(--pa-gold)}.pa-message button{border:0;background:none;color:var(--pa-muted);cursor:pointer}.pa-content{width:min(1440px,calc(100% - 48px));margin:auto;padding:34px 0 80px}.pa-content>*{max-width:none!important}
.pa-content .bg-white,.pa-content .bg-gray-50,.pa-content .bg-gray-100,.pa-content .bg-slate-50,.pa-content .bg-slate-100{background:var(--pa-panel)!important}.pa-content .text-gray-400,.pa-content .text-gray-500,.pa-content .text-gray-600,.pa-content .text-slate-400,.pa-content .text-slate-500,.pa-content .text-slate-600{color:var(--pa-muted)!important}.pa-content .text-gray-700,.pa-content .text-gray-800,.pa-content .text-gray-900,.pa-content .text-slate-700,.pa-content .text-slate-800,.pa-content .text-slate-900{color:var(--pa-text)!important}.pa-content .border,.pa-content [class*="border-gray"],.pa-content [class*="border-slate"],.pa-content table,.pa-content th,.pa-content td{border-color:var(--pa-line)!important}.pa-content [class*="bg-pink"],.pa-content [class*="bg-purple"],.pa-content [class*="from-pink"],.pa-content [class*="to-purple"]{background:linear-gradient(120deg,var(--pa-gold),var(--pa-gold2))!important;color:#171008!important}.pa-content input:not([type=checkbox]):not([type=radio]),.pa-content select,.pa-content textarea{border:1px solid var(--pa-line)!important;background:var(--pa-bg)!important;color:var(--pa-text)!important;box-shadow:none!important}.pa-content input:focus,.pa-content select:focus,.pa-content textarea:focus{border-color:var(--pa-line2)!important;outline:none!important;box-shadow:0 0 0 4px rgba(201,149,77,.07)!important}.pa-content table{width:100%;background:var(--pa-panel)!important}.pa-content th{background:var(--pa-panel2)!important;color:var(--pa-gold2)!important}.pa-content td{color:var(--pa-text)!important}
.pa-owner-dashboard{display:grid;gap:18px}.pa-dashboard-hero{min-height:220px;padding:34px 38px;border:1px solid var(--pa-line);background:radial-gradient(circle at 80% 25%,rgba(201,149,77,.14),transparent 22%),linear-gradient(120deg,var(--pa-panel2),var(--pa-panel));display:flex;align-items:flex-end;justify-content:space-between;gap:30px;box-shadow:var(--pa-shadow)}.pa-eyebrow{color:var(--pa-gold);font-size:8px;letter-spacing:.19em;font-weight:700}.pa-dashboard-hero h1{margin:8px 0!important;color:var(--pa-text)!important;font-size:clamp(38px,4.5vw,64px)!important;line-height:1.1!important}.pa-dashboard-hero p{margin:0;color:var(--pa-muted)!important}.pa-owner-seal{width:112px;height:112px;flex:none;border:1px solid var(--pa-line2);border-radius:50%;display:grid;place-items:center;align-content:center;gap:6px;color:var(--pa-gold2);background:var(--pa-bg)}.pa-owner-seal i{font-size:27px}.pa-owner-seal span{font-size:8px;letter-spacing:.17em}
.pa-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.pa-metrics article{min-height:145px;padding:19px;border:1px solid var(--pa-line);background:linear-gradient(145deg,var(--pa-panel),var(--pa-panel2));display:flex;flex-direction:column}.pa-metrics article>span{width:40px;height:40px;margin-bottom:auto;border:1px solid var(--pa-line);border-radius:50%;display:grid;place-items:center;color:var(--pa-gold)}.pa-metrics small{color:var(--pa-muted);font-size:9px}.pa-metrics strong{font-size:28px;line-height:1.2}.pa-metrics em{color:var(--pa-muted);font-size:8px;font-style:normal}.pa-metrics article.gold{background:radial-gradient(circle at 80% 20%,rgba(231,193,130,.15),transparent 24%),linear-gradient(145deg,#5a371d,#24170f);color:#fff3df}html[data-perfume-theme="day"] .pa-metrics article.gold{background:radial-gradient(circle at 80% 20%,rgba(255,255,255,.3),transparent 24%),linear-gradient(145deg,#d4ac76,#9a652e)}
.pa-secondary-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.pa-secondary-metrics>div{min-height:76px;padding:14px 16px;border:1px solid var(--pa-line);background:var(--pa-panel);display:flex;align-items:center;gap:12px}.pa-secondary-metrics i{width:42px;height:42px;border:1px solid var(--pa-line);border-radius:50%;color:var(--pa-gold);display:grid;place-items:center}.pa-secondary-metrics small,.pa-secondary-metrics strong{display:block}.pa-secondary-metrics small{color:var(--pa-muted);font-size:8px}.pa-secondary-metrics strong{font-size:19px}
.pa-panel-section,.pa-panel-card{padding:26px;border:1px solid var(--pa-line);background:linear-gradient(145deg,var(--pa-panel),var(--pa-panel2))}.pa-section-title,.pa-card-head{margin-bottom:20px;display:flex;align-items:flex-end;justify-content:space-between;gap:20px}.pa-section-title h2,.pa-card-head h2{margin:5px 0 0!important;color:var(--pa-text)!important;font-size:25px!important}.pa-section-title p{margin:0;color:var(--pa-muted)!important;font-size:10px}.pa-action-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}.pa-action-card{min-height:135px;padding:16px;border:1px solid var(--pa-line);background:var(--pa-bg);display:grid;grid-template-columns:46px 1fr 18px;gap:11px;align-items:center;color:var(--pa-text)!important;transition:.2s}.pa-action-card:hover{border-color:var(--pa-line2);transform:translateY(-3px)}.pa-action-card.gold{background:radial-gradient(circle at 75% 30%,rgba(201,149,77,.17),transparent 25%),var(--pa-bg);border-color:var(--pa-line2)}.pa-action-icon{width:46px;height:46px;border:1px solid var(--pa-line2);border-radius:50%;display:grid;place-items:center;color:var(--pa-gold)}.pa-action-copy strong,.pa-action-copy small{display:block}.pa-action-copy strong{font-size:12px}.pa-action-copy small{margin-top:4px;color:var(--pa-muted);font-size:8px;line-height:1.8}.pa-action-arrow{color:var(--pa-gold);font-size:10px}
.pa-dashboard-columns{display:grid;grid-template-columns:1fr 1fr;gap:18px}.pa-card-head>a{color:var(--pa-gold)!important;font-size:9px}.pa-list{display:grid;gap:7px}.pa-list-row{min-height:72px;padding:10px;border:1px solid var(--pa-line);background:var(--pa-bg);display:grid;grid-template-columns:46px 1fr auto;gap:11px;align-items:center}.pa-list-icon,.pa-product-thumb{width:46px;height:46px;border:1px solid var(--pa-line);display:grid;place-items:center;color:var(--pa-gold);overflow:hidden}.pa-product-thumb img{width:100%;height:100%;object-fit:contain;padding:3px}.pa-list-copy strong,.pa-list-copy small{display:block}.pa-list-copy strong{font-size:11px}.pa-list-copy small{color:var(--pa-muted);font-size:8px}.pa-row-value{color:var(--pa-gold2);font-size:10px}.pa-row-value small{font-size:7px;color:var(--pa-muted)}
.pa-user-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px}.pa-user-grid article{min-height:102px;padding:13px;border:1px solid var(--pa-line);background:var(--pa-bg);display:grid;grid-template-columns:38px 1fr;gap:9px;align-items:center}.pa-user-avatar{width:38px;height:38px;border-radius:50%;display:grid;place-items:center;background:var(--pa-panel2);color:var(--pa-gold);border:1px solid var(--pa-line2)}.pa-user-grid strong,.pa-user-grid small,.pa-user-grid time{display:block}.pa-user-grid strong{font-size:10px}.pa-user-grid small{color:var(--pa-muted);font-size:7px;overflow-wrap:anywhere}.pa-user-grid time{grid-column:1/-1;border-top:1px solid var(--pa-line);padding-top:7px;color:var(--pa-muted);font-size:7px}.pa-empty{min-height:140px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:var(--pa-muted);text-align:center}.pa-empty i{margin-bottom:8px;color:var(--pa-gold);font-size:24px}
.pa-studio-body{margin:0;min-height:100vh;overflow:hidden;background:#090706;color:#f6eee4;font-family:Vazir,Tahoma,Arial,sans-serif}.pa-hidden-csrf{display:none}.pa-studio{height:100vh;display:grid;grid-template-rows:70px minmax(0,1fr);direction:rtl}.pa-studio-top{padding:0 15px;border-bottom:1px solid rgba(218,178,112,.18);background:#120d09;display:flex;align-items:center;justify-content:space-between;gap:15px}.pa-studio-brand,.pa-studio-actions,.pa-device-switch{display:flex;align-items:center;gap:7px}.pa-studio-brand>a{width:40px;height:40px;border:1px solid rgba(218,178,112,.18);display:grid;place-items:center;color:#e3c286;text-decoration:none}.pa-studio-brand .pa-monogram{width:40px;height:40px}.pa-studio-brand strong,.pa-studio-brand small{display:block}.pa-studio-brand strong{font-size:11px}.pa-studio-brand small{color:#c9954d;font-size:6px;letter-spacing:.17em}.pa-device-switch{padding:4px;border:1px solid rgba(218,178,112,.15);background:#090706}.pa-device-switch button,.pa-preview-toolbar button{width:38px;height:34px;border:0;background:transparent;color:#8f8378;cursor:pointer}.pa-device-switch button.active{background:#281a11;color:#e3c286}.pa-primary,.pa-secondary{min-height:42px;padding:0 14px;border:1px solid rgba(218,178,112,.26);display:inline-flex;align-items:center;justify-content:center;gap:8px;font-family:inherit;cursor:pointer}.pa-primary{background:linear-gradient(120deg,#e3c286,#9d672c);color:#171008}.pa-secondary{background:#15100c;color:#efe4d6}.pa-primary.full,.pa-secondary.full{width:100%}
.pa-studio-grid{min-height:0;display:grid;grid-template-columns:330px minmax(0,1fr)}.pa-studio-panel{overflow:auto;padding:20px 16px 80px;border-left:1px solid rgba(218,178,112,.16);background:#14100d}.pa-studio-panel section{padding:18px 0;border-bottom:1px solid rgba(218,178,112,.13)}.pa-studio-panel h2{margin:6px 0 15px;font-size:18px}.pa-color-list{display:grid;gap:7px}.pa-color-list label{min-height:43px;padding:5px 8px;border:1px solid rgba(218,178,112,.13);display:flex;align-items:center;justify-content:space-between;gap:10px;color:#b5a99e;font-size:9px}.pa-color-list input[type=color]{width:45px;height:30px;border:0;padding:0;background:none}.pa-studio-help{color:#8e8278;font-size:9px;line-height:1.9}.pa-editor-fields{display:grid;gap:9px}.pa-editor-fields[hidden],[data-text-field][hidden],[data-image-field][hidden],[data-upload-box][hidden]{display:none!important}.pa-editor-fields>label,.pa-field-pair label{display:grid;gap:5px;color:#a99d91;font-size:8px}.pa-editor-fields input:not([type=checkbox]),.pa-editor-fields textarea{width:100%;box-sizing:border-box;border:1px solid rgba(218,178,112,.16);background:#090706;color:#f7efe6;padding:9px;outline:none;font-family:inherit}.pa-field-pair{display:grid;grid-template-columns:1fr 1fr;gap:7px}.pa-check-row{min-height:42px;padding:0 9px;border:1px solid rgba(218,178,112,.13);display:flex!important;align-items:center;gap:8px!important}.pa-upload-box{display:grid;gap:6px}.pa-upload-box input{font-size:8px}.pa-danger-soft{min-height:40px;border:1px solid rgba(183,92,84,.3);background:rgba(183,92,84,.08);color:#d98a82;font-family:inherit;cursor:pointer}.pa-region-list{display:grid;gap:5px}.pa-region-list button{min-height:40px;padding:0 9px;border:1px solid rgba(218,178,112,.12);background:#0d0907;color:#a99d91;display:flex;justify-content:space-between;align-items:center;font-family:inherit;cursor:pointer}.pa-region-list button.active,.pa-region-list button:hover{color:#f7efe6;border-color:rgba(218,178,112,.36);background:#21160f}.pa-preview-shell{min-width:0;min-height:0;padding:14px;background:radial-gradient(circle at 50% 30%,rgba(201,149,77,.08),transparent 24%),#080605;display:grid;grid-template-rows:38px minmax(0,1fr)}.pa-preview-toolbar{padding:0 10px;border:1px solid rgba(218,178,112,.13);background:#120d09;display:flex;align-items:center;justify-content:space-between;color:#968a7e;font-size:8px}.pa-preview-toolbar span{display:flex;align-items:center;gap:7px}.pa-preview-toolbar span i{color:#62ad7b;font-size:6px}.pa-preview-frame{min-height:0;margin:auto;width:100%;height:100%;background:#fff;transition:.25s;overflow:hidden}.pa-preview-frame.tablet{width:min(820px,100%)}.pa-preview-frame.mobile{width:min(430px,100%)}.pa-preview-frame iframe{width:100%;height:100%;border:0;display:block;background:#fff}.pa-studio-toast{min-width:240px;max-width:420px;padding:12px 16px;position:fixed;z-index:999;left:24px;bottom:24px;transform:translateY(20px);opacity:0;pointer-events:none;border:1px solid rgba(98,173,123,.35);background:#15251b;color:#c9efd4;transition:.25s;font-size:10px}.pa-studio-toast.error{border-color:rgba(183,92,84,.35);background:#2b1513;color:#efbbb5}.pa-studio-toast.show{opacity:1;transform:none}.pa-overlay{display:none}
@media(max-width:1180px){.pa-action-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.pa-user-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:900px){.pa-shell{grid-template-columns:1fr}.pa-sidebar{width:min(310px,88vw);position:fixed;inset:0 0 0 auto;transform:translateX(105%);transition:.25s}.pa-sidebar.open{transform:none}.pa-sidebar-close{width:38px;height:38px;display:grid;place-items:center;position:absolute;left:12px;top:12px;border:1px solid var(--pa-line);background:var(--pa-bg);color:var(--pa-text)}.pa-overlay{display:block;position:fixed;z-index:34;inset:0;background:rgba(0,0,0,.55);opacity:0;pointer-events:none;transition:.25s}.pa-overlay.show{opacity:1;pointer-events:auto}.pa-menu-button{display:grid}.pa-dashboard-columns{grid-template-columns:1fr}.pa-metrics{grid-template-columns:1fr 1fr}.pa-studio-grid{grid-template-columns:285px minmax(0,1fr)}}
@media(max-width:680px){.pa-content{width:calc(100% - 24px);padding:20px 0 55px}.pa-topbar{padding:0 12px}.pa-studio-link span{display:none}.pa-dashboard-hero{padding:25px 20px;min-height:190px}.pa-owner-seal{display:none}.pa-metrics,.pa-secondary-metrics,.pa-action-grid,.pa-user-grid{grid-template-columns:1fr}.pa-panel-section,.pa-panel-card{padding:18px}.pa-section-title,.pa-card-head{align-items:flex-start;flex-direction:column}.pa-list-row{grid-template-columns:42px 1fr}.pa-row-value{grid-column:2}.pa-studio-body{overflow:auto}.pa-studio{height:auto;min-height:100vh;grid-template-rows:auto auto}.pa-studio-top{padding:10px;flex-wrap:wrap}.pa-studio-grid{display:block}.pa-studio-panel{border-left:0;border-bottom:1px solid rgba(218,178,112,.15)}.pa-preview-shell{height:76vh}}
"""

ADMIN_JS_TEXT = r"""
(() => {
  "use strict";
  const sidebar=document.querySelector("[data-pa-sidebar]");
  const overlay=document.querySelector("[data-pa-overlay]");
  function open(){sidebar?.classList.add("open");overlay?.classList.add("show");document.body.style.overflow="hidden"}
  function close(){sidebar?.classList.remove("open");overlay?.classList.remove("show");document.body.style.overflow=""}
  function toggleTheme(){const r=document.documentElement;const next=(r.dataset.perfumeTheme||"night")==="night"?"day":"night";r.dataset.perfumeTheme=next;try{localStorage.setItem("velora-theme",next);localStorage.setItem("perfume-theme",next);localStorage.setItem("theme",next)}catch(_){}}
  document.addEventListener("click",e=>{if(e.target.closest("[data-pa-open]")){open();return}if(e.target.closest("[data-pa-close]")||e.target.closest("[data-pa-overlay]")){close();return}if(e.target.closest("[data-pa-theme]")){toggleTheme();return}const c=e.target.closest("[data-pa-message-close]");if(c)c.closest(".pa-message")?.remove()});
  document.addEventListener("keydown",e=>{if(e.key==="Escape")close()});
})();
"""

RUNTIME_JS_TEXT = r"""
(() => {
  "use strict";
  const node=document.getElementById("perfume-visual-rules");
  const themeNode=document.getElementById("perfume-theme-values");
  const validHex=v=>/^#[0-9a-f]{6}$/i.test(v||"");
  if(themeNode){const r=document.documentElement;const p=validHex(themeNode.dataset.primary)?themeNode.dataset.primary:"#C9954D";const s=validHex(themeNode.dataset.secondary)?themeNode.dataset.secondary:"#75471F";const a=validHex(themeNode.dataset.accent)?themeNode.dataset.accent:"#E3C286";r.style.setProperty("--p-gold",p);r.style.setProperty("--p-gold-deep",s);r.style.setProperty("--p-gold-pale",a);r.style.setProperty("--site-primary",p);r.style.setProperty("--site-secondary",s);r.style.setProperty("--site-accent",a)}
  if(!node)return;
  let raw;try{raw=JSON.parse(node.textContent||'"[]"')}catch(_){return}
  let rules=[];if(Array.isArray(raw))rules=raw;else if(typeof raw==="string"){try{const p=JSON.parse(raw||"[]");if(Array.isArray(p))rules=p}catch(_){}}
  const bp=()=>innerWidth<=620?"mobile":innerWidth<=1024?"tablet":"desktop";
  function apply(){const b=bp();for(const rule of rules){if(!rule||!rule.id)continue;const el=document.querySelector(`[data-bsg-edit="${CSS.escape(rule.id)}"]`)||document.getElementById(rule.id);if(!el)continue;const kind=el.dataset.bsgKind||rule.kind||"box";if(rule.hidden)el.style.display="none";if(kind==="text"&&rule.text)el.textContent=rule.text;if(kind==="image"&&rule.src&&el.tagName==="IMG")el.src=rule.src;Object.entries(rule.styles||{}).forEach(([k,v])=>{if(v!==""&&v!=null){try{el.style[k]=v}catch(_){}}});const pos=rule.responsive?.[b];if(pos){if(Number(pos.width)>0)el.style.width=`${Number(pos.width)}px`;if(Number(pos.height)>0)el.style.height=`${Number(pos.height)}px`;if(Number(pos.x)||Number(pos.y))el.style.transform=`translate(${Number(pos.x)||0}px,${Number(pos.y)||0}px)`;if(Number.isFinite(Number(pos.zIndex)))el.style.zIndex=String(Number(pos.zIndex))}}}
  apply();let timer;addEventListener("resize",()=>{clearTimeout(timer);timer=setTimeout(apply,120)},{passive:true});
})();
"""

STUDIO_JS_TEXT = r"""
(() => {
  "use strict";
  const root=document.querySelector("[data-studio]");
  const iframe=document.querySelector("[data-preview]");
  const frame=document.querySelector("[data-preview-frame]");
  const payloadNode=document.getElementById("pa-customizer-payload");
  const csrf=document.querySelector(".pa-hidden-csrf input[name=csrfmiddlewaretoken]")?.value||"";
  const defaults={primary:"#C9954D",secondary:"#75471F",accent:"#E3C286",bg:"#090706",text:"#F7F0E7"};
  let payload={rules:[],theme:{...defaults}};try{const p=JSON.parse(payloadNode?.textContent||"{}");if(p&&typeof p==="object")payload=p}catch(_){}
  payload.rules=Array.isArray(payload.rules)?payload.rules:[];payload.theme={...defaults,...(payload.theme||{})};
  let selectedId=null,selectedEl=null;
  const qs=(s,p=document)=>p.querySelector(s),qsa=(s,p=document)=>[...p.querySelectorAll(s)];
  const doc=()=>{try{return iframe.contentDocument}catch(_){return null}};
  function toast(message,ok=true){const el=qs("[data-studio-toast]");el.textContent=message;el.classList.toggle("error",!ok);el.classList.add("show");setTimeout(()=>el.classList.remove("show"),2600)}
  function findRule(id){return payload.rules.find(x=>x.id===id)||null}
  function ensureRule(id,name,kind){let r=findRule(id);if(!r){r={id,name:name||id,created:false,kind:["text","image","box"].includes(kind)?kind:"box",text:"",src:"",href:"",hidden:false,styles:{},parent:"main-content",responsive:{desktop:{x:0,y:0,width:0,height:0,zIndex:0},tablet:{x:0,y:0,width:0,height:0,zIndex:0},mobile:{x:0,y:0,width:0,height:0,zIndex:0}}};payload.rules.push(r)}r.styles||={};return r}
  function applyTheme(d){if(!d)return;const r=d.documentElement;r.style.setProperty("--p-gold",payload.theme.primary);r.style.setProperty("--p-gold-deep",payload.theme.secondary);r.style.setProperty("--p-gold-pale",payload.theme.accent);r.style.setProperty("--site-primary",payload.theme.primary);r.style.setProperty("--site-secondary",payload.theme.secondary);r.style.setProperty("--site-accent",payload.theme.accent)}
  function applyRule(el,r){if(!el||!r)return;const kind=el.dataset.bsgKind||r.kind||"box";if(kind==="text"&&r.text)el.textContent=r.text;if(kind==="image"&&r.src&&el.tagName==="IMG")el.src=r.src;el.style.display=r.hidden?"none":"";Object.entries(r.styles||{}).forEach(([k,v])=>{if(v!==""&&v!=null){try{el.style[k]=v}catch(_){}}})}
  function applyAll(){const d=doc();if(!d)return;applyTheme(d);payload.rules.forEach(r=>{const el=d.querySelector(`[data-bsg-edit="${CSS.escape(r.id)}"]`)||d.getElementById(r.id);if(el)applyRule(el,r)})}
  function injectStyle(d){if(d.getElementById("pa-visual-editor-style"))return;const s=d.createElement("style");s.id="pa-visual-editor-style";s.textContent='[data-bsg-edit]{outline:1px dashed rgba(201,149,77,.58)!important;outline-offset:-2px!important;cursor:pointer!important}[data-bsg-edit]:hover{outline:2px solid #c9954d!important}[data-bsg-edit].pa-visual-selected{outline:3px solid #e3c286!important;box-shadow:inset 0 0 0 9999px rgba(201,149,77,.035)!important}';d.head.appendChild(s)}
  function buildList(){const d=doc(),list=qs("[data-region-list]");if(!d||!list)return;list.innerHTML="";qsa("[data-bsg-edit]",d).forEach(el=>{const id=el.dataset.bsgEdit,name=el.dataset.bsgName||id,b=document.createElement("button");b.type="button";b.dataset.selectRegion=id;b.innerHTML=`<span>${name}</span><i class="fa-solid fa-arrow-left"></i>`;b.addEventListener("click",()=>select(el));list.appendChild(b)})}
  function rgbToHex(v){if(/^#[0-9a-f]{6}$/i.test(v||""))return v;const a=String(v||"").match(/\d+/g);if(!a||a.length<3)return"#c9954d";return"#"+a.slice(0,3).map(n=>Number(n).toString(16).padStart(2,"0")).join("")}
  function syncFields(r,el){const kind=el.dataset.bsgKind||r.kind||"box";qs("[data-selected-name]").textContent=el.dataset.bsgName||r.name||"بخش انتخاب‌شده";qs("[data-editor-fields]").hidden=false;qs("[data-text-field]").hidden=kind!=="text";qs("[data-image-field]").hidden=kind!=="image";qs("[data-upload-box]").hidden=kind!=="image"||!root.dataset.uploadUrl;qs("[data-rule-text]").value=r.text||(kind==="text"?el.textContent.trim():"");qs("[data-rule-src]").value=r.src||(kind==="image"?(el.getAttribute("src")||""):"");qsa("[data-style]").forEach(input=>{const k=input.dataset.style;let v=r.styles?.[k]||"";if(input.type==="color")v=rgbToHex(v||getComputedStyle(el)[k]);if(input.type==="number"&&v==="")v="1";input.value=v});qs("[data-rule-hidden]").checked=!!r.hidden}
  function select(el){const d=doc();if(!d||!el)return;qsa(".pa-visual-selected",d).forEach(x=>x.classList.remove("pa-visual-selected"));el.classList.add("pa-visual-selected");selectedEl=el;selectedId=el.dataset.bsgEdit;const kind=el.dataset.bsgKind||(el.tagName==="IMG"?"image":"box"),r=ensureRule(selectedId,el.dataset.bsgName||selectedId,kind);syncFields(r,el);qsa("[data-select-region]").forEach(b=>b.classList.toggle("active",b.dataset.selectRegion===selectedId))}
  function prepare(){const d=doc();if(!d)return;injectStyle(d);applyAll();buildList();d.addEventListener("click",e=>{const el=e.target.closest("[data-bsg-edit]");if(!el)return;e.preventDefault();e.stopPropagation();select(el)},true);d.addEventListener("submit",e=>{e.preventDefault();e.stopPropagation()},true)}
  iframe.addEventListener("load",()=>{selectedId=null;selectedEl=null;qs("[data-editor-fields]").hidden=true;qs("[data-selected-name]").textContent="یک بخش را انتخاب کنید";setTimeout(prepare,80)});
  qsa("[data-theme-field]").forEach(input=>{const k=input.dataset.themeField;input.value=payload.theme[k]||defaults[k];input.addEventListener("input",()=>{payload.theme[k]=input.value;applyTheme(doc())})});
  qsa("[data-style]").forEach(input=>input.addEventListener("input",()=>{if(!selectedId||!selectedEl)return;const r=ensureRule(selectedId,selectedEl.dataset.bsgName,selectedEl.dataset.bsgKind);r.styles[input.dataset.style]=input.value;selectedEl.style[input.dataset.style]=input.value}));
  qs("[data-rule-text]").addEventListener("input",e=>{if(!selectedId||!selectedEl||selectedEl.dataset.bsgKind!=="text")return;const r=ensureRule(selectedId,selectedEl.dataset.bsgName,"text");r.text=e.target.value;selectedEl.textContent=r.text;selectedEl.dataset.bsgEdit=selectedId;selectedEl.dataset.bsgName=r.name;selectedEl.dataset.bsgKind="text";selectedEl.classList.add("pa-visual-selected")});
  qs("[data-rule-src]").addEventListener("input",e=>{if(!selectedId||!selectedEl||selectedEl.tagName!=="IMG")return;const r=ensureRule(selectedId,selectedEl.dataset.bsgName,"image");r.src=e.target.value.trim();if(r.src)selectedEl.src=r.src});
  qs("[data-rule-hidden]").addEventListener("change",e=>{if(!selectedId||!selectedEl)return;const r=ensureRule(selectedId,selectedEl.dataset.bsgName,selectedEl.dataset.bsgKind);r.hidden=e.target.checked;selectedEl.style.display=r.hidden?"none":""});
  qs("[data-rule-clear]").addEventListener("click",()=>{if(!selectedId)return;payload.rules=payload.rules.filter(x=>x.id!==selectedId);iframe.contentWindow.location.reload();toast("تغییرات این بخش حذف شد")});
  qs("[data-rule-upload]").addEventListener("click",async()=>{const file=qs("[data-rule-file]").files?.[0];if(!file||!selectedId||!selectedEl||!root.dataset.uploadUrl){toast("ابتدا یک تصویر انتخاب کنید",false);return}const fd=new FormData();fd.append("file",file);try{const response=await fetch(root.dataset.uploadUrl,{method:"POST",headers:{"X-CSRFToken":csrf,"X-Requested-With":"XMLHttpRequest"},body:fd}),result=await response.json();if(!response.ok||result.success===false)throw new Error(result.error||"آپلود انجام نشد");const r=ensureRule(selectedId,selectedEl.dataset.bsgName,"image");r.src=result.url;selectedEl.src=result.url;qs("[data-rule-src]").value=result.url;toast("تصویر آپلود شد")}catch(err){toast(err.message||"آپلود انجام نشد",false)}});
  qsa("[data-device]").forEach(b=>b.addEventListener("click",()=>{qsa("[data-device]").forEach(x=>x.classList.remove("active"));b.classList.add("active");frame.className="pa-preview-frame "+b.dataset.device}));
  qs("[data-preview-refresh]").addEventListener("click",()=>iframe.contentWindow.location.reload());
  async function post(url,data){const response=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json","X-CSRFToken":csrf,"X-Requested-With":"XMLHttpRequest"},body:JSON.stringify(data)});let json={};try{json=await response.json()}catch(_){}if(!response.ok||json.success===false)throw new Error(json.error||"درخواست انجام نشد");return json}
  qs("[data-studio-save]").addEventListener("click",async()=>{const b=qs("[data-studio-save]");b.disabled=true;try{const r=await post(root.dataset.saveUrl,payload);if(Array.isArray(r.rules))payload.rules=r.rules;if(r.theme)payload.theme={...payload.theme,...r.theme};toast("تغییرات ظاهری ذخیره شد")}catch(err){toast(err.message||"ذخیره انجام نشد",false)}finally{b.disabled=false}});
  qs("[data-studio-reset]").addEventListener("click",async()=>{if(!confirm("همه تغییرات بصری به تم عطر پیش‌فرض برگردد؟"))return;const b=qs("[data-studio-reset]");b.disabled=true;try{payload={rules:[],theme:{...defaults}};await post(root.dataset.saveUrl,payload);qsa("[data-theme-field]").forEach(input=>input.value=payload.theme[input.dataset.themeField]);iframe.contentWindow.location.reload();toast("تم عطر به حالت پیش‌فرض برگشت")}catch(err){toast(err.message||"بازنشانی انجام نشد",false)}finally{b.disabled=false}});
})();
"""


def main():
    print("=" * 86)
    print(" PHASE 09 — PERFUME OWNER PANEL + VISUAL STUDIO")
    print("=" * 86)

    required = [ROOT / "manage.py", URLS, BASE, DASHBOARD]
    missing = [p for p in required if not p.exists()]
    if missing:
        raise SystemExit("Missing required paths:\n" + "\n".join("  - " + str(p) for p in missing))

    if BACKUP.exists():
        raise SystemExit(
            f"Backup already exists: {BACKUP}\n"
            "Rename/delete it only if you intentionally want to rerun Phase 09."
        )

    names = route_names()
    must_have = {"owner_panel", "customizer", "customizer_save"}
    missing_routes = must_have - names
    if missing_routes:
        raise SystemExit(
            "Required existing management routes are missing: "
            + ", ".join(sorted(missing_routes))
            + "\nNo files were changed."
        )

    BACKUP.mkdir(parents=True)

    backend_snapshot = {
        rel: (ROOT / rel).read_bytes()
        for rel in BACKEND_GUARD
        if (ROOT / rel).exists()
    }

    admin_base = (
        ADMIN_BASE_TEMPLATE
        .replace("__NAV__", make_nav(names))
        .replace("__DASHBOARD_ASSETS__", dashboard_assets())
    )

    owner = (
        OWNER_PANEL_TEMPLATE
        .replace("__QUICK_ACTIONS__", make_quick_actions(names))
        .replace(
            "__ORDERS_MORE__",
            '<a href="{% url \'first:admin_orders\' %}">مشاهده همه ←</a>' if "admin_orders" in names else "",
        )
        .replace(
            "__PRODUCTS_MORE__",
            '<a href="{% url \'first:admin_products\' %}">مدیریت محصولات ←</a>' if "admin_products" in names else "",
        )
        .replace(
            "__USERS_MORE__",
            '<a href="{% url \'first:admin_users\' %}">همه کاربران ←</a>' if "admin_users" in names else "",
        )
    )

    upload_url = "{% url 'first:customizer_upload' %}" if "customizer_upload" in names else ""
    customizer = CUSTOMIZER_TEMPLATE.replace("__UPLOAD_URL__", upload_url)

    write(ADMIN_CSS, ADMIN_CSS_TEXT)
    write(ADMIN_JS, ADMIN_JS_TEXT)
    write(RUNTIME_JS, RUNTIME_JS_TEXT)
    write(STUDIO_JS, STUDIO_JS_TEXT)
    write(ADMIN_BASE, admin_base)
    write(OWNER_PANEL, owner)
    write(CUSTOMIZER, customizer)

    patch_dashboard_children()
    patch_storefront_markers()

    for rel, before in backend_snapshot.items():
        if (ROOT / rel).read_bytes() != before:
            raise RuntimeError("Backend changed unexpectedly: " + rel)

    print("\n[CHECK] Django")
    run(sys.executable, "manage.py", "check")

    print("\n[CHECK] No migration drift")
    run(sys.executable, "manage.py", "makemigrations", "--check", "--dry-run")

    print("\n[CHECK] Main templates")
    run(
        sys.executable,
        "manage.py",
        "shell",
        "-c",
        (
            "from django.template.loader import get_template; "
            "[get_template(x) for x in ["
            "'dashboard/perfume_admin_base.html',"
            "'dashboard/owner_panel.html',"
            "'dashboard/customizer.html'"
            "]]; print('TEMPLATES OK')"
        ),
    )

    print("\n" + "=" * 86)
    print(" PHASE 09 READY")
    print("=" * 86)
    print("✓ Owner panel redesigned for the perfume store")
    print("✓ Dashboard pages share one luxury admin shell")
    print("✓ Black / espresso / champagne-gold / warm-ivory palette")
    print("✓ Day/night switch included in management panel")
    print("✓ Existing visual-customizer backend reused")
    print("✓ Live desktop/tablet/mobile Visual Studio")
    print("✓ Text/image/color/background/spacing/radius/opacity/shadow controls")
    print("✓ Saved visual rules are applied on the storefront")
    print("✓ No views/models/urls/migrations/shop-core files changed")
    if "customizer_upload" in names:
        print("✓ Image upload is enabled in Visual Studio")
    else:
        print("• Image URL editing enabled; no customizer_upload route was found")
    print("\nRun:")
    print("  python manage.py runserver")
    print("Then hard refresh the browser with Ctrl+F5")


if __name__ == "__main__":
    main()
