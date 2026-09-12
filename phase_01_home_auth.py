#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations
import shutil, subprocess, sys, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / ".perfume_frontend_phase01_backup"
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
    p = ROOT / rel
    backup(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    print("[WRITE]", rel)

FILES["first/templates/perfume_base.html"] = r"""
{% load static %}
<!doctype html>
<html lang="fa" dir="rtl" data-perfume-theme="night">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#080705">
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
<link rel="stylesheet" href="{% static 'css/perfume-phase01.css' %}">
{% block extra_css %}{% endblock %}
</head>
<body class="velora-body">
<div class="page-grain"></div><div class="scroll-progress" data-progress></div>

<div class="top-lux-bar">
  <span>ارسال مطمئن و بسته‌بندی حرفه‌ای</span><i>✦</i>
  <span>تضمین اصالت کالا</span><i>✦</i>
  <span>مشاوره انتخاب رایحه</span>
</div>

<header class="pro-header" data-header>
  <div class="pro-header-main">
    <a class="pro-logo" href="{% url 'first:home' %}">
      <span class="logo-mark">{% if settings.logo %}<img src="{{ settings.logo.url }}" alt="">{% else %}V{% endif %}</span>
      <span class="logo-copy"><b>{{ settings.site_name|default:"VÉLORA" }}</b><small>MAISON DE PARFUM</small></span>
    </a>

    <form class="header-search" method="get" action="{% url 'first:search_products' %}">
      <button type="submit"><i class="fa-solid fa-magnifying-glass"></i></button>
      <input name="q" type="search" placeholder="نام عطر، برند، رایحه یا نت موردنظر..." autocomplete="off">
      <span>SEARCH</span>
    </form>

    <div class="header-actions">
      <button type="button" data-theme-toggle title="روز / شب"><i class="fa-regular fa-moon night-icon"></i><i class="fa-regular fa-sun day-icon"></i></button>
      {% if user.is_authenticated %}<a href="{% url 'first:profile' %}"><i class="fa-regular fa-user"></i></a>{% else %}<a href="{% url 'first:login' %}"><i class="fa-regular fa-user"></i></a>{% endif %}
      <a href="{% url 'first:wishlist' %}"><i class="fa-regular fa-heart"></i></a>
      <a class="cart-link" href="{% url 'first:cart' %}"><i class="fa-solid fa-bag-shopping"></i><span>سبد خرید</span></a>
      <button class="menu-trigger" type="button" data-menu-open><i></i><i></i></button>
    </div>
  </div>

  <div class="pro-header-nav">
    <nav>
      <a href="{% url 'first:home' %}">خانه</a>
      <a href="{% url 'first:product_list' %}">همه عطرها</a>
      <a href="{% url 'first:best_sellers' %}">پرفروش‌ترین‌ها</a>
      <a href="{% url 'first:discounts' %}">پیشنهاد ویژه</a>
      <a href="{% url 'first:customer_service' 'shopping-guide' %}">راهنمای انتخاب عطر</a>
      <a href="{% url 'customer_care:order_tracking' %}">پیگیری سفارش</a>
    </nav>
    <a class="header-support" href="{% url 'customer_care:support_home' %}"><i class="fa-solid fa-headset"></i> پشتیبانی</a>
  </div>
</header>

<aside class="mobile-drawer" data-menu>
  <div><span>VÉLORA / MENU</span><button data-menu-close>×</button></div>
  <nav>
    <a href="{% url 'first:home' %}"><small>01</small>خانه</a>
    <a href="{% url 'first:product_list' %}"><small>02</small>کالکشن عطرها</a>
    <a href="{% url 'first:best_sellers' %}"><small>03</small>پرفروش‌ها</a>
    <a href="{% url 'first:discounts' %}"><small>04</small>پیشنهادها</a>
    <a href="{% url 'first:wishlist' %}"><small>05</small>علاقه‌مندی‌ها</a>
    {% if user.is_authenticated %}
    <a href="{% url 'first:user_orders' %}"><small>06</small>سفارش‌های من</a>
    <a href="{% url 'first:profile' %}"><small>07</small>حساب کاربری</a>
    {% else %}
    <a href="{% url 'first:login' %}"><small>06</small>ورود</a>
    <a href="{% url 'first:signup' %}"><small>07</small>ثبت‌نام</a>
    {% endif %}
  </nav>
</aside>

{% if messages %}<div class="phase-toasts">{% for message in messages %}<div><span>{{ message }}</span><button data-toast-close>×</button></div>{% endfor %}</div>{% endif %}

<main>{% block content %}{% endblock %}</main>

<footer class="phase-footer">
  <div class="footer-grid">
    <div><span class="eyebrow-x">A HOUSE OF SCENT</span><h2>{{ settings.site_name|default:"VÉLORA" }}</h2><p>رایحه‌ای که فقط انتخاب نمی‌شود؛ بخشی از هویت شما می‌شود.</p></div>
    <div><b>DISCOVER</b><a href="{% url 'first:product_list' %}">همه عطرها</a><a href="{% url 'first:best_sellers' %}">پرفروش‌ها</a><a href="{% url 'first:discounts' %}">پیشنهادها</a></div>
    <div><b>SERVICE</b><a href="{% url 'customer_care:support_home' %}">پشتیبانی</a><a href="{% url 'customer_care:order_tracking' %}">پیگیری سفارش</a><a href="{% url 'first:customer_service' 'shipping-returns' %}">ارسال و مرجوعی</a></div>
    <div><b>PRIVATE NOTES</b><p>خبر کالکشن‌های تازه و پیشنهادهای محدود.</p><div class="newsletter"><input placeholder="ایمیل شما"><button>←</button></div></div>
  </div>
  <div class="footer-bottom"><span>{{ settings.footer_text|default:"© 2026 VÉLORA PARFUMS" }}</span><span>SCENT / MEMORY / IDENTITY</span></div>
</footer>

<script src="{% static 'js/perfume-phase01.js' %}"></script>
{% block extra_js %}{% endblock %}
</body></html>
"""

FILES["first/templates/index.html"] = r"""
{% extends 'perfume_base.html' %}
{% load custom_filters %}
{% block title %}{{ settings.site_title|default:"VÉLORA — رایحه‌ای فراتر از زمان" }}{% endblock %}
{% block content %}
{% firstof featured_products.0 best_sellers.0 new_products.0 as hero_product %}

<section class="lux-home-hero">
  {% for slider in sliders %}{% if forloop.first %}<img class="hero-bg" src="{{ slider.image.url }}" alt="">{% endif %}{% endfor %}
  <div class="hero-shade"></div><div class="hero-grid"></div><div class="hero-arch"></div>

  <div class="hero-copy">
    <div class="hero-kicker"><span>01</span><i></i><small>THE NEW OLFACTIVE EDIT</small></div>
    <h1><span>رایحه‌ای برای</span><em>حضورهای ماندگار</em></h1>
    <p>مجموعه‌ای از عطرهای انتخاب‌شده برای کسانی که عطر را آخرین جزئیات استایل نمی‌دانند؛ اولین نشانه حضور می‌دانند.</p>
    <div class="hero-actions">
      <a class="gold-btn-x" href="{% url 'first:product_list' %}">کشف کالکشن <i class="fa-solid fa-arrow-left"></i></a>
      <a class="ghost-btn-x" href="#finder"><span><i class="fa-solid fa-play"></i></span> پیدا کردن رایحه من</a>
    </div>
    <div class="hero-note"><small>CURATED</small><b>برای انتخاب‌های شخصی‌تر</b><span>FRESH · WOODY · FLORAL · AMBER</span></div>
  </div>

  <div class="hero-object">
    <div class="orbit oa"></div><div class="orbit ob"></div><div class="hero-glow"></div>
    {% if hero_product %}
      <a href="{% url 'first:product_detail' hero_product.slug %}" class="hero-product">
        {% if hero_product.main_image %}<img src="{{ hero_product.main_image.url }}" alt="{{ hero_product.name }}">{% else %}<div class="css-bottle"><b>VÉLORA</b><small>EXTRAIT DE PARFUM</small></div>{% endif %}
      </a>
      <div class="hero-product-info"><small>FEATURED SCENT</small><b>{{ hero_product.name }}</b><span>{{ hero_product.final_price|price_format }} تومان</span></div>
    {% else %}
      <div class="css-bottle"><b>VÉLORA</b><small>EXTRAIT DE PARFUM</small></div>
    {% endif %}
  </div>

  <aside class="hero-side">
    <div><span>01</span><i class="fa-regular fa-gem"></i><p><b>اصالت تضمین‌شده</b><small>انتخاب مطمئن و معتبر</small></p></div>
    <div><span>02</span><i class="fa-regular fa-clock"></i><p><b>رایحه ماندگار</b><small>برای حضور طولانی‌تر</small></p></div>
    <div><span>03</span><i class="fa-regular fa-heart"></i><p><b>انتخاب شخصی</b><small>متناسب با حال‌وهوای شما</small></p></div>
  </aside>
</section>

<section class="trust-rail">
  <div><i class="fa-solid fa-shield-halved"></i><p><b>تضمین اصالت</b><span>خرید مطمئن</span></p></div>
  <div><i class="fa-solid fa-truck-fast"></i><p><b>ارسال حرفه‌ای</b><span>بسته‌بندی ایمن</span></p></div>
  <div><i class="fa-solid fa-gift"></i><p><b>هدیه لوکس</b><span>برای لحظه‌های خاص</span></p></div>
  <div><i class="fa-solid fa-headset"></i><p><b>مشاوره رایحه</b><span>انتخاب دقیق‌تر</span></p></div>
</section>

<section class="signature-home">
  <div class="section-head-x reveal">
    <div><span class="eyebrow-x">SIGNATURE SELECTION</span><h2>عطرهایی که<br>امضا می‌شوند.</h2></div>
    <div><p>از رایحه‌های روشن و تمیز برای روز تا نت‌های عمیق، چوبی و گرم برای شب.</p><a href="{% url 'first:product_list' %}">مشاهده همه کالکشن ←</a></div>
  </div>

  <div class="home-product-grid">
    {% for product in best_sellers|slice:":4" %}
    <article class="home-product reveal">
      <a class="home-product-media" href="{% url 'first:product_detail' product.slug %}">
        <span class="seq">0{{ forloop.counter }}</span>
        {% if product.is_best_seller %}<small class="badge-x">ICON</small>{% endif %}
        {% if product.main_image %}<img src="{{ product.main_image.url }}" alt="{{ product.name }}" loading="lazy">{% else %}<div class="mini-bottle">V</div>{% endif %}
      </a>
      <div class="home-product-copy">
        <div><small>{{ product.brand.name|default:"VÉLORA" }}</small><a href="{% url 'first:product_detail' product.slug %}">{{ product.name }}</a></div>
        <div><strong>{{ product.final_price|price_format }}</strong><span>تومان</span></div>
      </div>
    </article>
    {% empty %}
      {% for product in featured_products|slice:":4" %}
      <article class="home-product reveal">
        <a class="home-product-media" href="{% url 'first:product_detail' product.slug %}"><span class="seq">0{{ forloop.counter }}</span>{% if product.main_image %}<img src="{{ product.main_image.url }}" alt="{{ product.name }}">{% else %}<div class="mini-bottle">V</div>{% endif %}</a>
        <div class="home-product-copy"><div><small>{{ product.brand.name|default:"VÉLORA" }}</small><a href="{% url 'first:product_detail' product.slug %}">{{ product.name }}</a></div><div><strong>{{ product.final_price|price_format }}</strong><span>تومان</span></div></div>
      </article>
      {% endfor %}
    {% endfor %}
  </div>
</section>

<section class="scent-finder" id="finder">
  <div class="finder-art reveal"><div class="face-art"></div><span>FIND<br>YOUR<br>SIGNATURE</span><small>02 / SCENT PROFILE</small></div>
  <div class="finder-copy reveal">
    <span class="eyebrow-x">PERFUME FINDER</span><h2>عطر مناسب تو،<br>از حس شروع می‌شود.</h2><p>به‌جای گشتن بین صدها محصول، از خانواده رایحه‌ای که دوست داری شروع کن.</p>
    <div class="finder-links">
      <a href="{% url 'first:search_products' %}?q=خنک"><span>01</span><b>FRESH</b><small>مرکباتی / تمیز / روزانه</small><i>↗</i></a>
      <a href="{% url 'first:search_products' %}?q=چوبی"><span>02</span><b>WOODY</b><small>چوبی / خشک / عمیق</small><i>↗</i></a>
      <a href="{% url 'first:search_products' %}?q=گلی"><span>03</span><b>FLORAL</b><small>گلی / نرم / روشن</small><i>↗</i></a>
      <a href="{% url 'first:search_products' %}?q=گرم"><span>04</span><b>AMBER</b><small>گرم / شبانه / ماندگار</small><i>↗</i></a>
    </div>
  </div>
</section>

<section class="editorial-grid-x">
  <a class="panel-x panel-new reveal" href="{% url 'first:product_list' %}?sort=-created_at"><span>03 / NEW ARRIVALS</span><h3>تازه وارد<br>آرشیو</h3><p>رایحه‌هایی که همین حالا وارد کالکشن شده‌اند.</p><b>DISCOVER ↗</b><div class="panel-bottle"></div></a>
  <a class="panel-x panel-icons reveal" href="{% url 'first:best_sellers' %}"><span>04 / ICONS</span><h3>محبوب‌ترین<br>انتخاب‌ها</h3><b>VIEW ICONS ↗</b><div class="panel-rings"></div></a>
  <a class="panel-x panel-gift reveal" href="{% url 'first:product_list' %}"><span>05 / GIFTING</span><h3>هنر<br>هدیه دادن</h3><p>انتخابی ماندگار برای یک لحظه خاص.</p><b>SELECT A GIFT ↗</b><div class="gift-box-x"></div></a>
</section>

{% if categories %}
<section class="category-home">
  <div class="section-head-x reveal"><div><span class="eyebrow-x">SHOP BY MOOD</span><h2>از حس انتخاب کن.</h2></div><a href="{% url 'first:product_list' %}">همه دسته‌ها ←</a></div>
  <div class="category-grid-x">
    {% for category in categories|slice:":6" %}{% if category.slug %}
    <a class="category-card-x reveal" href="{% url 'first:category_products' category.slug %}">
      <span>0{{ forloop.counter }}</span>
      <div>{% if category.image %}<img src="{{ category.image.url }}" alt="{{ category.name }}">{% else %}<i class="fa-solid fa-spray-can-sparkles"></i>{% endif %}</div>
      <b>{{ category.name }}</b><small>DISCOVER</small>
    </a>
    {% endif %}{% endfor %}
  </div>
</section>
{% endif %}

<section class="craft-home reveal">
  <div><span class="eyebrow-x">THE ART OF PERFUMERY</span><h2>یک عطر خوب<br>فقط خوشبو نیست.</h2><p>شروع، قلب و پایه هر رایحه باید مثل یک داستان کنار هم قرار بگیرند؛ چیزی که حس می‌شود و در حافظه می‌ماند.</p><a class="outline-btn-x" href="{% url 'first:customer_service' 'shopping-guide' %}">راهنمای انتخاب عطر ←</a></div>
  <aside><i class="craft-ring cr1"></i><i class="craft-ring cr2"></i><i class="petal pet1"></i><i class="petal pet2"></i><i class="petal pet3"></i><span>NATURE<br>TO MEMORY</span></aside>
</section>

{% if brands %}<section class="brand-rail-x"><span>CURATED HOUSES</span><div>{% for brand in brands %}{% if brand.slug %}<a href="{% url 'first:brand_products' brand.slug %}">{{ brand.name }}</a>{% endif %}{% endfor %}</div></section>{% endif %}
<section class="quote-home"><span>06</span><blockquote>“Perfume is the most intense form of memory.”</blockquote><small>JEAN-PAUL GUERLAIN</small></section>
{% endblock %}
"""

FILES["first/templates/login.html"] = r"""
{% extends 'perfume_base.html' %}
{% block title %}ورود | {{ settings.site_name|default:"VÉLORA" }}{% endblock %}
{% block content %}
<section class="auth-x">
  <div class="auth-art">
    <div class="auth-grid"></div><div class="auth-number">01</div><div class="auth-orbit a1"></div><div class="auth-orbit a2"></div>
    <div class="auth-bottle"><div class="auth-cap"></div><div class="auth-glass"><b>VÉLORA</b><small>MAISON DE PARFUM</small></div></div>
    <div class="auth-art-copy"><span>MEMBER ACCESS</span><h2>به دنیای<br>رایحه‌ها برگرد.</h2><p>سفارش‌ها، علاقه‌مندی‌ها و انتخاب‌های شخصی شما در یکجا.</p></div>
  </div>

  <div class="auth-form-side">
    <div class="auth-card">
      <div class="auth-diamond"><i class="fa-solid fa-spray-can-sparkles"></i></div>
      <span class="eyebrow-x">WELCOME BACK</span><h1>خوش آمدید</h1><p class="auth-lead">برای ادامه خرید و دسترسی به حساب کاربری وارد شوید.</p>

      {% if form.non_field_errors %}<div class="auth-errors">{% for error in form.non_field_errors %}<span>{{ error }}</span>{% endfor %}</div>{% endif %}

      <form method="POST" class="auth-form" novalidate>
        {% csrf_token %}
        <label class="auth-field">شماره تلفن
          <span><i class="fa-solid fa-mobile-screen-button"></i><input type="text" name="phone" id="id_phone" placeholder="09123456789" value="{{ form.phone.value|default:'' }}" autocomplete="tel" required></span>
          {% if form.phone.errors %}<small>{{ form.phone.errors.0 }}</small>{% endif %}
        </label>

        <label class="auth-field">رمز عبور
          <span><i class="fa-solid fa-lock"></i><input type="password" name="password" id="id_password" placeholder="رمز عبور" autocomplete="current-password" required><button type="button" data-password-toggle="id_password"><i class="fa-regular fa-eye"></i></button></span>
          {% if form.password.errors %}<small>{{ form.password.errors.0 }}</small>{% endif %}
        </label>

        <div class="auth-options">
          <label class="checkbox-x"><input type="checkbox" name="remember"><i></i>مرا به خاطر بسپار</label>
          <a href="{% url 'first:forgot_password' %}">فراموشی رمز عبور</a>
        </div>

        <button class="auth-submit" type="submit"><span>ورود به حساب</span><i class="fa-solid fa-arrow-left"></i></button>
      </form>

      <div class="auth-switch"><span>حساب کاربری ندارید؟</span><a href="{% url 'first:signup' %}">ایجاد حساب جدید</a></div>
      <div class="auth-secure"><i class="fa-solid fa-shield-halved"></i> اطلاعات حساب شما به‌صورت امن نگهداری می‌شود.</div>
    </div>
  </div>
</section>
{% endblock %}
"""

FILES["first/templates/signup.html"] = r"""
{% extends 'perfume_base.html' %}
{% block title %}ثبت‌نام | {{ settings.site_name|default:"VÉLORA" }}{% endblock %}
{% block content %}
<section class="auth-x">
  <div class="auth-art">
    <div class="auth-grid"></div><div class="auth-number">02</div><div class="auth-orbit a1"></div><div class="auth-orbit a2"></div>
    <div class="auth-bottle alt"><div class="auth-cap"></div><div class="auth-glass"><b>VÉLORA</b><small>PRIVATE MEMBER</small></div></div>
    <div class="auth-art-copy"><span>JOIN THE HOUSE</span><h2>رایحه‌هایت را<br>شخصی‌تر انتخاب کن.</h2><p>حساب بساز، عطرها را ذخیره کن و سفارش‌هایت را راحت‌تر دنبال کن.</p></div>
  </div>

  <div class="auth-form-side">
    <div class="auth-card signup-card">
      <div class="auth-diamond"><i class="fa-regular fa-gem"></i></div>
      <span class="eyebrow-x">JOIN VÉLORA</span><h1>ساخت حساب</h1><p class="auth-lead">چند اطلاعات کوتاه و حساب شما آماده است.</p>

      {% if form.errors %}<div class="auth-errors"><b>لطفاً خطاها را بررسی کنید:</b>{% for field in form %}{% for error in field.errors %}<span>{{ field.label }}: {{ error }}</span>{% endfor %}{% endfor %}{% for error in form.non_field_errors %}<span>{{ error }}</span>{% endfor %}</div>{% endif %}

      <form method="POST" class="auth-form signup-grid" novalidate>
        {% csrf_token %}
        <label class="auth-field wide">نام کاربری
          <span><i class="fa-regular fa-user"></i><input type="text" name="username" id="id_username" placeholder="نام کاربری" value="{{ form.username.value|default:'' }}" required></span>
        </label>
        <label class="auth-field">ایمیل
          <span><i class="fa-regular fa-envelope"></i><input type="email" name="email" id="id_email" placeholder="name@example.com" value="{{ form.email.value|default:'' }}" required></span>
        </label>
        <label class="auth-field">شماره تلفن
          <span><i class="fa-solid fa-mobile-screen-button"></i><input type="tel" name="phone" id="id_phone" placeholder="09123456789" value="{{ form.phone.value|default:'' }}" required></span>
        </label>
        <label class="auth-field">رمز عبور
          <span><i class="fa-solid fa-lock"></i><input type="password" name="password1" id="id_password1" placeholder="حداقل ۸ کاراکتر" required><button type="button" data-password-toggle="id_password1"><i class="fa-regular fa-eye"></i></button></span>
        </label>
        <label class="auth-field">تکرار رمز عبور
          <span><i class="fa-solid fa-shield-halved"></i><input type="password" name="password2" id="id_password2" placeholder="تکرار رمز عبور" required><button type="button" data-password-toggle="id_password2"><i class="fa-regular fa-eye"></i></button></span>
        </label>

        <label class="checkbox-x terms wide">
          <input type="checkbox" name="agree_terms" id="agree_terms" {% if form.agree_terms.value %}checked{% endif %} required><i></i>
          <b>با <a href="{% url 'first:customer_service' 'terms' %}" target="_blank">قوانین و مقررات</a> و <a href="{% url 'first:customer_service' 'privacy' %}" target="_blank">حریم خصوصی</a> موافقم.</b>
        </label>
        <button class="auth-submit wide" type="submit"><span>ایجاد حساب کاربری</span><i class="fa-solid fa-arrow-left"></i></button>
      </form>
      <div class="auth-switch"><span>قبلاً حساب ساخته‌اید؟</span><a href="{% url 'first:login' %}">ورود به حساب</a></div>
    </div>
  </div>
</section>
{% endblock %}
"""

FILES["static/css/perfume-phase01.css"] = r"""
:root{--xbg:#080705;--xbg2:#100d0a;--xsurface:#15110d;--xsurface2:#1c1711;--xtext:#f7f0e7;--xmuted:#a99d8e;--xgold:#d8b36d;--xgold2:#9f7033;--xgoldp:#efd4a0;--xline:rgba(216,179,109,.18);--xline2:rgba(216,179,109,.43);--xserif:Georgia,"Times New Roman",serif;--xshadow:0 35px 110px rgba(0,0,0,.42);--xmax:1540px}
html[data-perfume-theme="day"]{--xbg:#f4eee5;--xbg2:#fffaf4;--xsurface:#fffaf3;--xsurface2:#eadfd2;--xtext:#17130f;--xmuted:#6d6359;--xgold:#986b2f;--xgold2:#7d5524;--xgoldp:#8b6128;--xline:rgba(116,86,49,.17);--xline2:rgba(137,96,42,.38);--xshadow:0 35px 90px rgba(73,50,25,.13)}
.velora-body{background:var(--xbg)!important;color:var(--xtext)!important}.page-grain{position:fixed;z-index:9999;inset:0;pointer-events:none;opacity:.025;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.82' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}.scroll-progress{position:fixed;z-index:1200;top:0;left:0;height:2px;width:0;background:var(--xgold)}
.top-lux-bar{height:34px;display:flex;align-items:center;justify-content:center;gap:25px;background:#080705;color:#d9c7ac;border-bottom:1px solid rgba(216,179,109,.12);font-size:8px;position:relative;z-index:110}.top-lux-bar i{color:#c99b54}
.pro-header{position:sticky;top:0;z-index:100;background:color-mix(in srgb,var(--xbg) 92%,transparent);border-bottom:1px solid var(--xline);backdrop-filter:blur(24px);box-shadow:0 18px 50px rgba(0,0,0,.08)}
.pro-header-main{max-width:var(--xmax);min-height:92px;margin:auto;padding:0 28px;display:grid;grid-template-columns:255px minmax(340px,1fr) auto;gap:30px;align-items:center}.pro-logo{display:flex;align-items:center;gap:12px;width:max-content}.logo-mark{width:52px;height:52px;border:1px solid var(--xline2);display:grid;place-items:center;overflow:hidden;font-family:var(--xserif);font-size:27px;color:var(--xgoldp);background:linear-gradient(145deg,var(--xsurface2),var(--xbg))}.logo-mark img{width:100%;height:100%;object-fit:contain;padding:5px}.logo-copy{display:flex;flex-direction:column;direction:ltr;line-height:1.15}.logo-copy b{font-family:var(--xserif);font-size:23px;font-weight:400;letter-spacing:.28em;color:var(--xgoldp)}.logo-copy small{margin-top:5px;font-size:6px;letter-spacing:.31em;color:var(--xmuted)}
.header-search{height:54px;display:grid;grid-template-columns:52px 1fr auto;align-items:center;border:1px solid var(--xline);background:color-mix(in srgb,var(--xsurface) 87%,transparent);transition:.25s}.header-search:focus-within{border-color:var(--xline2);box-shadow:0 0 0 4px rgba(216,179,109,.055)}.header-search>button{height:100%;border:0;border-left:1px solid var(--xline);background:none;color:var(--xgold)}.header-search input{width:100%;height:100%;border:0;outline:none;background:none;color:var(--xtext);padding:0 16px;font-size:11px}.header-search>span{padding:0 15px;direction:ltr;font-size:6px;letter-spacing:.2em;color:var(--xmuted)}
.header-actions{display:flex;align-items:center;justify-content:flex-end;direction:ltr}.header-actions>*{min-width:44px;height:44px;border:1px solid transparent;background:none;color:var(--xtext);display:flex;align-items:center;justify-content:center;gap:8px}.header-actions>*:hover{border-color:var(--xline);color:var(--xgold)}.cart-link{padding:0 12px;border-color:var(--xline)!important}.cart-link span{font-size:9px}.day-icon{display:none}html[data-perfume-theme="day"] .night-icon{display:none}html[data-perfume-theme="day"] .day-icon{display:block}.menu-trigger{display:none}.menu-trigger i{width:18px;height:1px;background:currentColor;margin:2px}
.pro-header-nav{max-width:var(--xmax);min-height:48px;margin:auto;padding:0 28px;border-top:1px solid var(--xline);display:flex;align-items:center;justify-content:space-between}.pro-header-nav nav{display:flex;gap:31px}.pro-header-nav nav a{font-size:9px;position:relative;padding:14px 0}.pro-header-nav nav a:after{content:"";position:absolute;right:0;left:100%;bottom:8px;height:1px;background:var(--xgold);transition:.2s}.pro-header-nav nav a:hover{color:var(--xgold)}.pro-header-nav nav a:hover:after{left:0}.header-support{font-size:8px;color:var(--xmuted)}.header-support i{color:var(--xgold);margin-left:6px}
.mobile-drawer{position:fixed;z-index:300;inset:0;padding:28px 7vw;background:#080705;color:#f4eee5;transform:translateX(105%);transition:.45s}.mobile-drawer.open{transform:none}.mobile-drawer>div{display:flex;justify-content:space-between;color:#d0a45f}.mobile-drawer>div button{border:0;background:none;color:#fff;font-size:40px}.mobile-drawer nav{display:grid;margin-top:55px}.mobile-drawer nav a{display:grid;grid-template-columns:40px 1fr;border-bottom:1px solid rgba(216,179,109,.18);padding:11px 0;font-family:var(--xserif);font-size:clamp(27px,7vw,48px)}.mobile-drawer nav small{font-family:Vazir;font-size:7px;color:#cda662}
.phase-toasts{position:fixed;z-index:350;top:185px;right:22px;width:min(420px,calc(100vw - 44px));display:grid;gap:7px}.phase-toasts>div{display:flex;justify-content:space-between;padding:13px 15px;background:var(--xsurface);border:1px solid var(--xline);box-shadow:var(--xshadow);font-size:10px}.phase-toasts button{border:0;background:none;color:var(--xmuted)}
.eyebrow-x{display:block;direction:ltr;color:var(--xgold);font-size:7px;font-weight:700;letter-spacing:.28em}.gold-btn-x,.outline-btn-x,.ghost-btn-x{min-height:50px;display:inline-flex;align-items:center;justify-content:center;gap:14px;padding:0 24px;border:1px solid transparent;font-size:10px}.gold-btn-x{background:linear-gradient(120deg,var(--xgoldp),var(--xgold2));color:#181008}.outline-btn-x{border-color:var(--xline2)}.ghost-btn-x{padding:0}.ghost-btn-x>span{width:40px;height:40px;border:1px solid var(--xline2);border-radius:50%;display:grid;place-items:center;color:var(--xgold);font-size:7px}
.lux-home-hero{min-height:750px;height:calc(100vh - 174px);max-height:930px;position:relative;display:grid;grid-template-columns:1.03fr 1.08fr .64fr;align-items:center;padding:65px max(4.5vw,24px) 55px;overflow:hidden}.hero-bg{position:absolute;z-index:-6;inset:0;width:100%;height:100%;object-fit:cover;opacity:.42}.hero-shade{position:absolute;z-index:-5;inset:0;background:linear-gradient(90deg,rgba(5,4,3,.97),rgba(5,4,3,.77) 30%,rgba(5,4,3,.26) 62%,rgba(5,4,3,.88))}html[data-perfume-theme="day"] .hero-shade{background:linear-gradient(90deg,rgba(248,243,236,.99),rgba(248,243,236,.84),rgba(248,243,236,.31),rgba(248,243,236,.94))}.hero-grid{position:absolute;z-index:-4;inset:0;opacity:.45;background-image:linear-gradient(var(--xline) 1px,transparent 1px),linear-gradient(90deg,var(--xline) 1px,transparent 1px);background-size:90px 90px}.hero-arch{position:absolute;z-index:-3;width:39%;height:78%;left:31%;top:8%;border:1px solid var(--xline);border-radius:48% 48% 0 0/32% 32% 0 0}.hero-kicker{display:flex;align-items:center;gap:10px;direction:ltr;color:var(--xgold);font-size:7px}.hero-kicker i{width:55px;height:1px;background:var(--xline2)}.hero-copy h1{font-family:var(--xserif);font-weight:400;line-height:.92;margin:20px 0}.hero-copy h1 span,.hero-copy h1 em{display:block}.hero-copy h1 span{font-size:clamp(52px,5.9vw,92px)}.hero-copy h1 em{font-size:clamp(43px,5.1vw,78px);font-style:normal;color:var(--xgoldp)}.hero-copy>p{max-width:560px;color:var(--xmuted);font-size:13px}.hero-actions{display:flex;gap:14px;margin-top:30px}.hero-note{margin-top:36px;padding-right:13px;border-right:1px solid var(--xline2);display:flex;flex-direction:column}.hero-note small{font-size:6px;color:var(--xgold)}.hero-note b{font-size:9px}.hero-note span{font-size:6px;color:var(--xmuted)}
.hero-object{height:600px;position:relative;display:grid;place-items:center}.hero-product{z-index:4;width:74%;height:500px}.hero-product img{width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 48px 38px rgba(0,0,0,.66));animation:floatx 5.5s ease-in-out infinite}.orbit{position:absolute;border:1px solid rgba(227,166,78,.53);border-radius:50%}.oa{width:75%;height:34%;transform:rotate(-18deg);z-index:5}.ob{width:52%;height:62%;transform:rotate(38deg);opacity:.36}.hero-glow{position:absolute;width:55%;height:55%;border-radius:50%;background:#814718;filter:blur(90px);opacity:.18}.css-bottle{z-index:3;width:230px;height:340px;border:2px solid rgba(218,171,99,.68);border-radius:27px;background:linear-gradient(90deg,#0c0907,#69401e 37%,#100b08 62%,#69401e);display:flex;flex-direction:column;align-items:center;justify-content:center;color:#d6ac68}.css-bottle b{font-family:var(--xserif);letter-spacing:.2em}.css-bottle small{font-size:6px}.hero-product-info{position:absolute;left:0;bottom:20px;display:flex;flex-direction:column}.hero-product-info small{font-size:6px;color:var(--xgold)}.hero-product-info b{font-family:var(--xserif);font-weight:400}.hero-product-info span{font-size:8px;color:var(--xmuted)}
.hero-side{display:grid;gap:28px}.hero-side>div{display:grid;grid-template-columns:22px 44px 1fr;gap:10px}.hero-side>div>span{font-size:6px;color:var(--xgold)}.hero-side i{width:42px;height:42px;border:1px solid var(--xline2);border-radius:50%;display:grid;place-items:center;color:var(--xgold)}.hero-side p{margin:0}.hero-side b{display:block;font-size:10px}.hero-side small{font-size:7px;color:var(--xmuted)}
.trust-rail{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--xline);border-bottom:1px solid var(--xline);background:var(--xsurface)}.trust-rail>div{min-height:86px;padding:0 3vw;display:flex;align-items:center;justify-content:center;gap:12px;border-left:1px solid var(--xline)}.trust-rail i{color:var(--xgold)}.trust-rail p{margin:0}.trust-rail b{display:block;font-size:9px}.trust-rail span{font-size:7px;color:var(--xmuted)}
.signature-home,.category-home{max-width:var(--xmax);margin:auto;padding:90px 4.5vw}.section-head-x{display:grid;grid-template-columns:1fr .82fr;gap:90px;align-items:end;margin-bottom:38px}.section-head-x h2,.finder-copy h2,.craft-home h2{font-family:var(--xserif);font-size:clamp(42px,5vw,68px);font-weight:400;line-height:1}.section-head-x p,.finder-copy p,.craft-home p{color:var(--xmuted)}.section-head-x a{color:var(--xgold)}
.home-product-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.home-product{border:1px solid var(--xline);background:linear-gradient(145deg,var(--xsurface),var(--xsurface2));overflow:hidden;transition:.3s}.home-product:hover{transform:translateY(-7px);box-shadow:var(--xshadow)}.home-product-media{height:370px;display:grid;place-items:center;position:relative;overflow:hidden}.home-product-media img{width:100%;height:100%;object-fit:contain;padding:28px}.seq{position:absolute;left:12px;bottom:1px;font-family:var(--xserif);font-size:63px;color:rgba(216,179,109,.08)}.badge-x{position:absolute;right:12px;top:12px;padding:3px 7px;background:var(--xgoldp);color:#171008}.mini-bottle{width:78px;height:145px;border:1px solid var(--xgold);display:grid;place-items:center}.home-product-copy{padding:14px;display:flex;justify-content:space-between}.home-product-copy small{display:block;color:var(--xgold)}.home-product-copy a{font-family:var(--xserif);font-size:17px}.home-product-copy>div:last-child{text-align:left}.home-product-copy strong{display:block;font-size:10px}.home-product-copy span{font-size:7px;color:var(--xmuted)}
.scent-finder{min-height:610px;display:grid;grid-template-columns:.9fr 1.1fr;border-top:1px solid var(--xline);border-bottom:1px solid var(--xline)}.finder-art{position:relative;overflow:hidden;background:radial-gradient(circle at 43% 38%,#866047 0 7%,#54392b 23%,#1b120e 50%,#070605 73%)}.face-art{position:absolute;width:47%;height:80%;left:24%;top:7%;border-radius:47%;background:radial-gradient(ellipse at 56% 27%,#9d6d51 0 12%,#654334 29%,#1a100c 61%,transparent 62%)}.finder-art>span{position:absolute;left:32px;bottom:35px;font-family:var(--xserif);font-size:27px;color:#e4c8a0}.finder-art>small{position:absolute;right:28px;top:25px;color:#cfa461}.finder-copy{padding:75px 8vw;display:flex;flex-direction:column;justify-content:center}.finder-links{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid var(--xline)}.finder-links a{padding:18px 0;display:grid;grid-template-columns:27px 1fr 18px;grid-template-rows:auto auto;border-bottom:1px solid var(--xline)}.finder-links a:nth-child(odd){padding-left:18px;border-left:1px solid var(--xline)}.finder-links span{grid-row:1/3;color:var(--xgold)}.finder-links b{font-family:var(--xserif);font-weight:400}.finder-links small{color:var(--xmuted)}
.editorial-grid-x{display:grid;grid-template-columns:1.3fr 1fr 1fr}.panel-x{position:relative;overflow:hidden;min-height:430px;padding:45px 4vw;display:flex;flex-direction:column;justify-content:flex-end;color:#f4ede4}.panel-new{background:radial-gradient(circle at 76% 30%,#9b6639 0 9%,transparent 25%),#21130b}.panel-icons{background:#15130f}.panel-gift{background:#614227}.panel-x>span{font-size:7px;color:#d9b273}.panel-x h3{font-family:var(--xserif);font-size:36px;font-weight:400;line-height:1.05}.panel-x p{color:#c9b9a9}.panel-x>b{color:#d9b273}.panel-bottle{position:absolute;left:14%;top:22%;width:90px;height:170px;border:1px solid #bd8d52;background:#3d220f;border-radius:8px}.panel-rings{position:absolute;left:12%;top:16%;width:230px;height:230px;border:1px solid rgba(217,178,115,.25);border-radius:50%}.gift-box-x{position:absolute;left:14%;top:28%;width:125px;height:120px;border:1px solid #c2965e;background:#0c0907}
.category-grid-x{display:grid;grid-template-columns:repeat(6,1fr);gap:18px}.category-card-x{text-align:center}.category-card-x>span{color:var(--xgold)}.category-card-x>div{aspect-ratio:1;border:1px solid var(--xline);border-radius:50%;overflow:hidden;display:grid;place-items:center;background:var(--xsurface)}.category-card-x img{width:100%;height:100%;object-fit:cover}.category-card-x>div>i{font-size:32px;color:var(--xgold)}.category-card-x>b{display:block;margin-top:10px;font-family:var(--xserif);font-weight:400}.category-card-x>small{color:var(--xmuted)}
.craft-home{min-height:560px;display:grid;grid-template-columns:1fr 1fr;border-top:1px solid var(--xline);border-bottom:1px solid var(--xline)}.craft-home>div{padding:80px 8vw;display:flex;flex-direction:column;justify-content:center}.craft-home aside{position:relative;overflow:hidden;display:grid;place-items:center;background:radial-gradient(circle at 50% 50%,#d6c1a0 0 7%,#96734d 11%,#3a2b1f 34%,#080706 70%)}.craft-home aside>span{z-index:3;font-family:var(--xserif);font-size:29px;color:#e2c69c}.craft-ring{position:absolute;border:1px solid rgba(223,186,127,.19);border-radius:50%}.cr1{width:58%;height:58%}.cr2{width:77%;height:34%;transform:rotate(22deg)}.petal{position:absolute;border-radius:55% 45% 55% 45%;background:linear-gradient(135deg,#e2d0b1,#9a7852);opacity:.62}.pet1{width:240px;height:100px;left:12%;top:20%}.pet2{width:190px;height:85px;right:9%;top:28%}.pet3{width:260px;height:105px;right:18%;bottom:10%}
.brand-rail-x{max-width:var(--xmax);margin:auto;padding:45px 4.5vw;text-align:center}.brand-rail-x>span{color:var(--xgold);font-size:7px}.brand-rail-x>div{display:flex;justify-content:center;gap:38px;flex-wrap:wrap;margin-top:18px}.brand-rail-x a{font-family:var(--xserif);font-size:20px;color:var(--xmuted)}.quote-home{max-width:var(--xmax);margin:auto;padding:65px 4.5vw 80px;display:grid;grid-template-columns:80px 1fr auto;align-items:center;border-top:1px solid var(--xline)}.quote-home>span{font-family:var(--xserif);font-size:72px;color:rgba(216,179,109,.13)}.quote-home blockquote{font-family:var(--xserif);font-size:29px;font-style:italic}.quote-home small{color:var(--xgold)}
.auth-x{min-height:calc(100vh - 174px);display:grid;grid-template-columns:1fr 1fr}.auth-art{position:relative;overflow:hidden;min-height:690px;background:radial-gradient(circle at 50% 42%,rgba(152,89,40,.47),transparent 25%),linear-gradient(145deg,#2a1b12,#080605 72%);color:#f5eee5;display:grid;place-items:center}.auth-grid{position:absolute;inset:0;opacity:.2;background-image:linear-gradient(rgba(217,178,111,.13) 1px,transparent 1px),linear-gradient(90deg,rgba(217,178,111,.13) 1px,transparent 1px);background-size:78px 78px}.auth-number{position:absolute;top:20px;right:30px;font-family:var(--xserif);font-size:150px;color:rgba(255,255,255,.035)}.auth-orbit{position:absolute;border:1px solid rgba(224,172,91,.47);border-radius:50%}.a1{width:52%;height:22%;transform:rotate(-18deg)}.a2{width:31%;height:52%;transform:rotate(35deg);opacity:.35}.auth-bottle{position:relative;width:230px;height:390px}.auth-glass{position:absolute;bottom:0;width:100%;height:295px;border:2px solid #b98b50;border-radius:30px;background:linear-gradient(90deg,#0c0907,#70421e 35%,#120b07 63%,#603617);display:flex;align-items:center;justify-content:center;flex-direction:column}.auth-cap{position:absolute;top:0;left:58px;width:114px;height:78px;border:1px solid #9f7541;border-radius:14px;background:#2c2116}.auth-glass b{font-family:var(--xserif);letter-spacing:.2em;color:#d8ae6b}.auth-glass small{color:#b69365;font-size:6px}.auth-art-copy{position:absolute;right:7%;bottom:7%}.auth-art-copy>span{color:#d2a864;font-size:7px}.auth-art-copy h2{font-family:var(--xserif);font-weight:400;font-size:42px;line-height:1}.auth-art-copy p{color:#b9aa99}
.auth-form-side{min-height:690px;padding:70px 7vw;display:flex;align-items:center;justify-content:center;background:var(--xbg)}.auth-card{position:relative;width:min(510px,100%);padding:48px 44px 38px;border:1px solid var(--xline);background:linear-gradient(145deg,var(--xsurface),var(--xbg));box-shadow:var(--xshadow)}.auth-diamond{position:absolute;top:-31px;right:42px;width:62px;height:62px;transform:rotate(45deg);display:grid;place-items:center;border:1px solid var(--xline2);background:linear-gradient(145deg,var(--xgold2),#382311)}.auth-diamond i{transform:rotate(-45deg);color:#f4deba}.auth-card h1{font-family:var(--xserif);font-weight:400;font-size:46px}.auth-lead{color:var(--xmuted)}.auth-form{display:grid;gap:15px}.signup-grid{grid-template-columns:1fr 1fr}.wide{grid-column:1/-1}.auth-field{display:grid;gap:6px;color:var(--xmuted);font-size:8px}.auth-field>span{height:50px;display:grid;grid-template-columns:42px 1fr auto;align-items:center;border:1px solid var(--xline);background:var(--xsurface)}.auth-field>span>i{height:100%;display:grid;place-items:center;border-left:1px solid var(--xline);color:var(--xgold)}.auth-field input{width:100%;height:100%;border:0;outline:none;background:none;color:var(--xtext);padding:0 12px}.auth-field button{width:42px;height:100%;border:0;border-right:1px solid var(--xline);background:none;color:var(--xmuted)}.auth-field>small{color:#cf7470}.auth-options{display:flex;justify-content:space-between;align-items:center}.auth-options>a{color:var(--xgold);font-size:8px}.checkbox-x{display:flex;align-items:center;gap:8px;color:var(--xmuted);font-size:8px;cursor:pointer}.checkbox-x input{position:absolute;opacity:0}.checkbox-x>i{width:16px;height:16px;border:1px solid var(--xline2)}.checkbox-x input:checked+i{background:var(--xgold)}.terms{align-items:flex-start}.terms b{font-weight:400}.terms a{color:var(--xgold)}.auth-submit{width:100%;height:53px;border:0;padding:0 18px;display:flex;justify-content:space-between;align-items:center;background:linear-gradient(120deg,var(--xgoldp),var(--xgold2));color:#171008}.auth-switch{margin-top:20px;padding-top:17px;border-top:1px solid var(--xline);text-align:center;color:var(--xmuted);font-size:8px}.auth-switch a{color:var(--xgold);margin-right:6px}.auth-secure{text-align:center;margin-top:17px;color:var(--xmuted);font-size:7px}.auth-secure i{color:var(--xgold)}.auth-errors{display:grid;gap:4px;padding:11px;border:1px solid rgba(207,116,112,.3);color:#cf7470;font-size:8px;margin-bottom:15px}
.phase-footer{border-top:1px solid var(--xline);background:var(--xsurface);padding:65px 4.5vw 20px}.footer-grid{max-width:var(--xmax);margin:auto;display:grid;grid-template-columns:1.35fr .7fr .7fr 1.05fr;gap:42px}.footer-grid h2{font-family:var(--xserif);font-size:48px;font-weight:400}.footer-grid>div:not(:first-child){display:flex;flex-direction:column;gap:7px}.footer-grid b{color:var(--xgold);font-size:7px}.footer-grid p,.footer-grid a{color:var(--xmuted);font-size:9px}.newsletter{display:flex;height:44px;border:1px solid var(--xline)}.newsletter input{flex:1;min-width:0;border:0;background:none;padding:0 10px;color:var(--xtext)}.newsletter button{width:45px;border:0;background:none;color:var(--xgold)}.footer-bottom{max-width:var(--xmax);margin:40px auto 0;padding-top:16px;border-top:1px solid var(--xline);display:flex;justify-content:space-between;color:var(--xmuted);font-size:7px}
@keyframes floatx{50%{transform:translateY(-12px)}}
@media(max-width:1200px){.pro-header-main{grid-template-columns:210px minmax(280px,1fr) auto;gap:18px}.pro-header-nav nav{gap:19px}.lux-home-hero{grid-template-columns:1fr 1.05fr}.hero-side{display:none}.home-product-grid{grid-template-columns:repeat(3,1fr)}.home-product-grid>*:nth-child(4){display:none}.category-grid-x{grid-template-columns:repeat(4,1fr)}}
@media(max-width:950px){.pro-header-main{grid-template-columns:1fr auto;padding:0 18px}.header-search{grid-column:1/-1;grid-row:2;margin-bottom:12px;height:47px}.header-search>span{display:none}.header-actions{grid-column:2;grid-row:1}.pro-header-nav{display:none}.menu-trigger{display:grid}.cart-link span{display:none}.lux-home-hero{height:auto;min-height:900px;display:flex;flex-direction:column;padding:45px 20px}.hero-object{order:0;width:100%;height:420px}.hero-copy{order:1}.hero-arch{width:70%;height:45%;left:15%;top:6%}.hero-product{height:350px;width:65%}.trust-rail{grid-template-columns:1fr 1fr}.section-head-x{grid-template-columns:1fr;gap:8px}.home-product-grid{grid-template-columns:1fr 1fr}.home-product-grid>*:nth-child(4){display:block}.scent-finder{grid-template-columns:1fr}.finder-art{height:380px}.finder-copy{padding:55px 24px}.editorial-grid-x{grid-template-columns:1fr}.panel-x{min-height:300px}.category-grid-x{grid-template-columns:repeat(3,1fr)}.craft-home{grid-template-columns:1fr}.craft-home>div{padding:55px 24px}.craft-home aside{height:390px}.quote-home{grid-template-columns:1fr}.auth-x{grid-template-columns:1fr}.auth-art{display:none}.auth-form-side{min-height:calc(100vh - 150px);padding:70px 22px}.footer-grid{grid-template-columns:1fr 1fr}.footer-grid>div:first-child{grid-column:1/-1}}
@media(max-width:600px){.top-lux-bar{display:none}.logo-mark{width:42px;height:42px}.logo-copy b{font-size:18px}.header-actions>a:nth-of-type(2){display:none}.lux-home-hero{min-height:840px}.hero-object{height:340px}.hero-product{width:80%;height:300px}.hero-copy h1 span{font-size:47px}.hero-copy h1 em{font-size:39px}.hero-actions{flex-wrap:wrap}.hero-note{display:none}.trust-rail{grid-template-columns:1fr}.signature-home,.category-home{padding:60px 20px}.home-product-grid{grid-template-columns:1fr}.home-product-media{height:410px}.finder-links{grid-template-columns:1fr}.finder-links a:nth-child(odd){border-left:0;padding-left:0}.category-grid-x{grid-template-columns:1fr 1fr}.auth-form-side{padding:60px 16px}.auth-card{padding:45px 20px 30px}.signup-grid{grid-template-columns:1fr}.wide{grid-column:auto}.auth-options{align-items:flex-start;flex-direction:column}.footer-grid{grid-template-columns:1fr}.footer-grid>div:first-child{grid-column:auto}.footer-bottom{flex-direction:column;gap:5px}}
"""

FILES["static/js/perfume-phase01.js"] = r"""
(() => {
 const root=document.documentElement,$=(s,c=document)=>c.querySelector(s),$$=(s,c=document)=>[...c.querySelectorAll(s)];
 const setTheme=t=>{root.dataset.perfumeTheme=t;try{localStorage.setItem("velora-theme",t)}catch(e){}};

 document.addEventListener("click",e=>{
  if(e.target.closest("[data-theme-toggle]")){setTheme(root.dataset.perfumeTheme==="night"?"day":"night");return}
  if(e.target.closest("[data-menu-open]")){$("[data-menu]")?.classList.add("open");document.body.style.overflow="hidden";return}
  if(e.target.closest("[data-menu-close]")){$("[data-menu]")?.classList.remove("open");document.body.style.overflow="";return}
  const tc=e.target.closest("[data-toast-close]");if(tc){tc.closest(".phase-toasts>div")?.remove();return}
  const pt=e.target.closest("[data-password-toggle]");if(pt){const input=document.getElementById(pt.dataset.passwordToggle),icon=pt.querySelector("i");if(input){const show=input.type==="password";input.type=show?"text":"password";icon?.classList.toggle("fa-eye",!show);icon?.classList.toggle("fa-eye-slash",show)}return}
  const th=e.target.closest("[data-image],[data-detail-image]");if(th){const m=$("#detailMainImage,#mainProductImage");if(m)m.src=th.dataset.image||th.dataset.detailImage||"";return}
  const v=e.target.closest("[data-variant],[data-variant-id]");if(v){$$("[data-variant],[data-variant-id]").forEach(x=>x.classList.remove("selected"));v.classList.add("selected");const id=v.dataset.variant||v.dataset.variantId||"",price=v.dataset.price||v.dataset.variantPrice||"",img=v.dataset.vimage||v.dataset.variantImage||"",stock=Number(v.dataset.stock||v.dataset.variantStock||0),hid=$("#variantInput,#selectedVariantInput"),pe=$("#detailPrice,#detailFinalPrice"),mi=$("#detailMainImage,#mainProductImage"),q=$("#qty,#detailQty");if(hid)hid.value=id;if(pe&&price)pe.textContent=new Intl.NumberFormat("fa-IR").format(Number(price));if(mi&&img)mi.src=img;if(q&&stock>0)q.max=String(stock);return}
  if(e.target.closest("[data-minus],[data-qty-minus]")){const q=$("#qty,#detailQty");if(q)q.value=Math.max(1,Number(q.value||1)-1);return}
  if(e.target.closest("[data-plus],[data-qty-plus]")){const q=$("#qty,#detailQty");if(q)q.value=Math.min(Number(q.max||9999),Number(q.value||1)+1)}
 });

 document.addEventListener("change",e=>{const s=e.target.closest("[data-sort],[data-sort-select]");if(!s)return;const u=new URL(location.href);u.searchParams.set("sort",s.value);u.searchParams.delete("page");location.href=u});

 const progress=$("[data-progress]");
 const sync=()=>{if(progress){const max=document.documentElement.scrollHeight-innerHeight;progress.style.width=(max>0?(scrollY/max)*100:0)+"%"}};
 sync();addEventListener("scroll",sync,{passive:true});

 if("IntersectionObserver" in window){const items=$$(".reveal");items.forEach(x=>{x.style.opacity="0";x.style.transform="translateY(20px)";x.style.transition="opacity .65s ease,transform .65s ease"});const io=new IntersectionObserver(es=>es.forEach(en=>{if(en.isIntersecting){en.target.style.opacity="1";en.target.style.transform="translateY(0)";io.unobserve(en.target)}}),{threshold:.08});items.forEach(x=>io.observe(x))}
})();
"""

def main():
    print("="*76)
    print(" PHASE 01 — HEADER + HOME + LOGIN + SIGNUP")
    print("="*76)

    if not (ROOT/"manage.py").exists():
        raise SystemExit("Put this file beside manage.py inside perfume-shop.")

    backend = [
        "first/views.py","first/models.py","first/urls.py","first/forms.py",
        "first/context_processors.py","customer_care/views.py",
        "customer_care/models.py","customer_care/urls.py",
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
    print(" PHASE 01 READY")
    print("="*76)
    print("Backend remained byte-for-byte unchanged.")
    print("Run: python manage.py runserver")
    print("Check only: / , /login/ , /signup/")
    print("Do not commit yet. Send screenshots first.")

if __name__=="__main__":
    main()
