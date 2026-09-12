#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import shutil
import subprocess
import sys
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / ".perfume_frontend_phase08_backup"

BASE = ROOT / "first/templates/perfume_base.html"
CSS = ROOT / "static/css/perfume-phase08.css"

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


def patch_base():
    if not BASE.exists():
        raise RuntimeError("first/templates/perfume_base.html not found.")

    text = BASE.read_text(encoding="utf-8")
    original = text
    css_link = '<link rel="stylesheet" href="{% static \'css/perfume-phase08.css\' %}">'

    if "perfume-phase08.css" not in text:
        if "{% block extra_css %}" in text:
            text = text.replace(
                "{% block extra_css %}",
                css_link + "\n    {% block extra_css %}",
                1,
            )
        else:
            text = text.replace(
                "</head>",
                "    " + css_link + "\n</head>",
                1,
            )

    if text != original:
        backup(BASE)
        BASE.write_text(text, encoding="utf-8")
        print("[PATCH] first/templates/perfume_base.html -> Phase 08 CSS")


CART_TEMPLATE = r'''
{% extends 'perfume_base.html' %}
{% load custom_filters %}
{% block title %}سبد خرید | {{ settings.site_name|default:'فروشگاه عطر' }}{% endblock %}
{% block content %}
<section class="p8-page">
  <div class="p8-wrap">

    <header class="p8-page-head">
      <div>
        <span class="p8-kicker">YOUR SELECTION</span>
        <h1>سبد خرید</h1>
        <p>رایحه‌های انتخاب‌شده را مرور کنید و برای ثبت سفارش ادامه دهید.</p>
      </div>
      <div class="p8-head-mark"><i class="fa-solid fa-bag-shopping"></i></div>
    </header>

    {% if items %}
    <div class="p8-cart-layout">

      <div class="p8-cart-list">
        {% for item in items %}
        <article class="p8-cart-item">
          <a class="p8-cart-image" href="{% url 'first:product_detail' item.product.slug %}">
            {% if item.product.main_image %}
            <img src="{{ item.product.main_image.url }}" alt="{{ item.item_name }}">
            {% else %}
            <i class="fa-solid fa-spray-can-sparkles"></i>
            {% endif %}
          </a>

          <div class="p8-cart-copy">
            <small>{{ item.product.brand.name|default:'PERFUME HOUSE' }}</small>
            <h3>{{ item.item_name }}</h3>
            {% if item.variant %}<span>{{ item.variant }}</span>{% endif %}
            <strong>{{ item.final_price|price_format }} <em>تومان</em></strong>
          </div>

          <form class="p8-cart-qty" method="post" action="{% url 'first:update_cart_item' item.id %}">
            {% csrf_token %}
            <label>تعداد</label>
            <div>
              <input type="number" name="quantity" min="0" value="{{ item.quantity }}">
              <button type="submit">به‌روزرسانی</button>
            </div>
          </form>

          <form method="post" action="{% url 'first:remove_from_cart' item.id %}">
            {% csrf_token %}
            <button class="p8-remove" type="submit" aria-label="حذف">
              <i class="fa-regular fa-trash-can"></i>
            </button>
          </form>
        </article>
        {% endfor %}
      </div>

      <aside class="p8-summary">
        <span class="p8-kicker">ORDER SUMMARY</span>
        <h2>خلاصه سفارش</h2>

        <div class="p8-summary-row">
          <span>تعداد کالا</span>
          <b>{{ total_items|default:cart.total_items|default:0 }}</b>
        </div>

        <div class="p8-summary-row">
          <span>جمع محصولات</span>
          <b>{{ total_price|default:cart.total_price|price_format }} تومان</b>
        </div>

        <div class="p8-summary-row">
          <span>تخفیف</span>
          <b>{{ total_discount|default:cart.total_discount|price_format }} تومان</b>
        </div>

        <div class="p8-summary-total">
          <span>مبلغ نهایی</span>
          <strong>{{ final_price|default:cart.final_price|price_format }} <em>تومان</em></strong>
        </div>

        <a class="p8-primary full" href="{% url 'first:checkout' %}">
          ادامه و ثبت سفارش
          <i class="fa-solid fa-arrow-left"></i>
        </a>

        <a class="p8-secondary full" href="{% url 'first:product_list' %}">ادامه خرید</a>
      </aside>

    </div>
    {% else %}
    <div class="p8-empty-card">
      <div class="p8-empty-icon"><i class="fa-solid fa-bag-shopping"></i></div>
      <span class="p8-kicker">YOUR BAG IS EMPTY</span>
      <h2>سبد خرید شما خالی است.</h2>
      <p>از کالکشن عطرها، رایحه موردنظرتان را انتخاب کنید.</p>
      <a class="p8-primary" href="{% url 'first:product_list' %}">
        مشاهده محصولات
        <i class="fa-solid fa-arrow-left"></i>
      </a>
    </div>
    {% endif %}

  </div>
</section>
{% endblock %}
'''


WISHLIST_TEMPLATE = r'''
{% extends 'perfume_base.html' %}
{% load custom_filters %}
{% block title %}علاقه‌مندی‌ها | {{ settings.site_name|default:'فروشگاه عطر' }}{% endblock %}
{% block content %}
<section class="p8-page">
  <div class="p8-wrap">

    <header class="p8-page-head">
      <div>
        <span class="p8-kicker">SAVED SCENTS</span>
        <h1>علاقه‌مندی‌های من</h1>
        <p>رایحه‌هایی که برای مقایسه یا خرید بعدی ذخیره کرده‌اید.</p>
      </div>
      <div class="p8-head-mark"><i class="fa-regular fa-heart"></i></div>
    </header>

    {% if wishlist_items %}
    <div class="p8-wishlist-grid">
      {% for item in wishlist_items %}
      <article class="p8-wish-card">
        <a class="p8-wish-image" href="{% url 'first:product_detail' item.product.slug %}">
          {% if item.product.main_image %}
          <img src="{{ item.product.main_image.url }}" alt="{{ item.product.name }}">
          {% else %}
          <i class="fa-solid fa-spray-can-sparkles"></i>
          {% endif %}
        </a>

        <div class="p8-wish-copy">
          <small>{{ item.product.brand.name|default:'PERFUME HOUSE' }}</small>
          <a class="p8-wish-title" href="{% url 'first:product_detail' item.product.slug %}">
            {{ item.product.name }}
          </a>

          <div class="p8-wish-bottom">
            <strong>{{ item.product.final_price|price_format }} <em>تومان</em></strong>
            <form method="post" action="{% url 'first:remove_from_wishlist' item.product.id %}">
              {% csrf_token %}
              <button type="submit" class="p8-remove">
                <i class="fa-regular fa-trash-can"></i>
              </button>
            </form>
          </div>
        </div>
      </article>
      {% endfor %}
    </div>
    {% else %}
    <div class="p8-empty-card">
      <div class="p8-empty-icon"><i class="fa-regular fa-heart"></i></div>
      <span class="p8-kicker">NO SAVED SCENTS</span>
      <h2>هنوز عطری ذخیره نکرده‌اید.</h2>
      <p>محصولات موردعلاقه را ذخیره کنید تا بعداً سریع‌تر به آن‌ها برگردید.</p>
      <a class="p8-primary" href="{% url 'first:product_list' %}">
        مشاهده عطرها
        <i class="fa-solid fa-arrow-left"></i>
      </a>
    </div>
    {% endif %}

  </div>
</section>
{% endblock %}
'''


PROFILE_TEMPLATE = r'''
{% extends 'perfume_base.html' %}
{% block title %}حساب کاربری | {{ settings.site_name|default:'فروشگاه عطر' }}{% endblock %}
{% block content %}
<section class="p8-page">
  <div class="p8-wrap">

    <header class="p8-page-head">
      <div>
        <span class="p8-kicker">PRIVATE ACCOUNT</span>
        <h1>حساب کاربری</h1>
        <p>اطلاعات حساب، سفارش‌ها و انتخاب‌های ذخیره‌شده شما.</p>
      </div>
      <div class="p8-head-mark"><i class="fa-regular fa-user"></i></div>
    </header>

    <div class="p8-profile-layout">

      <aside class="p8-profile-card">
        <div class="p8-avatar">
          {% if user.profile_image %}
          <img src="{{ user.profile_image.url }}" alt="{{ user.username }}">
          {% else %}
          <span>{{ user.username|first|upper }}</span>
          {% endif %}
        </div>

        <span class="p8-kicker">MEMBER</span>
        <h2>{{ user.username }}</h2>
        <p>{{ user.email|default:'ایمیل ثبت نشده' }}</p>

        <div class="p8-user-badges">
          {% if user.is_superuser %}
          <span><i class="fa-solid fa-crown"></i> مالک فروشگاه</span>
          {% elif user.is_staff %}
          <span><i class="fa-solid fa-shield-halved"></i> مدیر</span>
          {% else %}
          <span><i class="fa-regular fa-user"></i> کاربر</span>
          {% endif %}

          {% if user.is_active %}
          <span><i class="fa-solid fa-check"></i> حساب فعال</span>
          {% endif %}
        </div>

        <a class="p8-secondary full" href="{% url 'first:edit_profile' %}">ویرایش اطلاعات</a>

        {% if user.is_superuser %}
        <a class="p8-primary full" href="{% url 'first:owner_panel' %}">
          پنل مالک
          <i class="fa-solid fa-arrow-left"></i>
        </a>
        {% endif %}
      </aside>

      <div class="p8-profile-main">

        <div class="p8-profile-actions">
          <a href="{% url 'first:user_orders' %}">
            <i class="fa-solid fa-box"></i>
            <span><strong>سفارش‌های من</strong><small>مشاهده و پیگیری خریدها</small></span>
            <b>←</b>
          </a>

          <a href="{% url 'first:wishlist' %}">
            <i class="fa-regular fa-heart"></i>
            <span><strong>علاقه‌مندی‌ها</strong><small>رایحه‌های ذخیره‌شده</small></span>
            <b>←</b>
          </a>

          <a href="{% url 'first:cart' %}">
            <i class="fa-solid fa-bag-shopping"></i>
            <span><strong>سبد خرید</strong><small>انتخاب‌های فعلی شما</small></span>
            <b>←</b>
          </a>

          <a href="{% url 'customer_care:support_home' %}">
            <i class="fa-solid fa-headset"></i>
            <span><strong>پشتیبانی</strong><small>تیکت‌ها و درخواست‌ها</small></span>
            <b>←</b>
          </a>
        </div>

        <section class="p8-details-card">
          <div class="p8-section-head">
            <div>
              <span class="p8-kicker">PERSONAL DETAILS</span>
              <h2>اطلاعات شخصی</h2>
            </div>
          </div>

          <div class="p8-detail-grid">
            <div><small>نام کاربری</small><strong>{{ user.username }}</strong></div>
            <div><small>ایمیل</small><strong>{{ user.email|default:'—' }}</strong></div>
            <div><small>شماره تلفن</small><strong>{{ user.phone|default:'ثبت نشده' }}</strong></div>
            <div>
              <small>نوع حساب</small>
              <strong>
                {% if user.is_superuser %}مالک{% elif user.is_staff %}مدیر{% else %}کاربر{% endif %}
              </strong>
            </div>
            <div><small>تاریخ عضویت</small><strong>{{ user.date_joined|date:'Y/m/d' }}</strong></div>
            <div><small>وضعیت</small><strong>{% if user.is_active %}فعال{% else %}غیرفعال{% endif %}</strong></div>
          </div>
        </section>

      </div>
    </div>

  </div>
</section>
{% endblock %}
'''


SUPPORT_HOME_TEMPLATE = r'''
{% extends 'perfume_base.html' %}
{% block title %}پشتیبانی | {{ settings.site_name|default:'فروشگاه عطر' }}{% endblock %}
{% block content %}
<section class="p8-page">
  <div class="p8-wrap">

    <header class="p8-page-head">
      <div>
        <span class="p8-kicker">CLIENT SERVICE</span>
        <h1>پشتیبانی</h1>
        <p>پیام‌ها، درخواست‌ها و وضعیت تیکت‌های شما در یکجا.</p>
      </div>
      <a class="p8-primary" href="{% url 'customer_care:support_create' %}">
        تیکت جدید
        <i class="fa-solid fa-plus"></i>
      </a>
    </header>

    <div class="p8-support-layout">

      <aside class="p8-support-side">
        <i class="fa-solid fa-headset"></i>
        <span class="p8-kicker">PRIVATE SERVICE</span>
        <h2>چطور می‌توانیم کمک کنیم؟</h2>
        <p>برای سوال درباره سفارش، ارسال، محصول یا هر درخواست دیگر یک تیکت ثبت کنید.</p>

        <div>
          <span><b>01</b> ثبت درخواست</span>
          <span><b>02</b> بررسی توسط پشتیبانی</span>
          <span><b>03</b> دریافت پاسخ</span>
        </div>
      </aside>

      <section class="p8-ticket-list">
        <div class="p8-section-head">
          <div>
            <span class="p8-kicker">YOUR TICKETS</span>
            <h2>درخواست‌های شما</h2>
          </div>
          <span>{{ tickets|length }} تیکت</span>
        </div>

        {% for ticket in tickets %}
        <a class="p8-ticket-row" href="{% url 'customer_care:support_detail' ticket.reference %}">
          <div>
            <small>{{ ticket.reference }}</small>
            <strong>{{ ticket.subject }}</strong>
            {% if ticket.order %}<span>سفارش #{{ ticket.order.order_number }}</span>{% endif %}
          </div>
          <div class="p8-ticket-status">
            <span>{{ ticket.get_status_display }}</span>
            <i class="fa-solid fa-arrow-left"></i>
          </div>
        </a>
        {% empty %}
        <div class="p8-empty-card compact">
          <div class="p8-empty-icon"><i class="fa-regular fa-message"></i></div>
          <h3>هنوز تیکتی ثبت نکرده‌اید.</h3>
          <p>برای شروع یک درخواست جدید، از دکمه تیکت جدید استفاده کنید.</p>
        </div>
        {% endfor %}
      </section>

    </div>
  </div>
</section>
{% endblock %}
'''


SUPPORT_CREATE_TEMPLATE = r'''
{% extends 'perfume_base.html' %}
{% block title %}تیکت جدید | {{ settings.site_name|default:'فروشگاه عطر' }}{% endblock %}
{% block content %}
<section class="p8-page">
  <div class="p8-wrap">

    <header class="p8-page-head">
      <div>
        <span class="p8-kicker">NEW REQUEST</span>
        <h1>تیکت پشتیبانی جدید</h1>
        <p>موضوع و جزئیات درخواست را بنویسید تا پشتیبانی آن را بررسی کند.</p>
      </div>
      <div class="p8-head-mark"><i class="fa-regular fa-message"></i></div>
    </header>

    <div class="p8-form-layout">

      <aside class="p8-form-aside">
        <span class="p8-kicker">BEFORE YOU SEND</span>
        <h2>برای پاسخ دقیق‌تر</h2>

        <div class="p8-form-tip">
          <b>01</b>
          <span><strong>موضوع واضح</strong><small>خلاصه درخواست را کوتاه و مشخص بنویسید.</small></span>
        </div>

        <div class="p8-form-tip">
          <b>02</b>
          <span><strong>سفارش مرتبط</strong><small>اگر درخواست درباره سفارش است، سفارش را انتخاب کنید.</small></span>
        </div>

        <div class="p8-form-tip">
          <b>03</b>
          <span><strong>توضیح کامل</strong><small>جزئیات کافی باعث پاسخ سریع‌تر می‌شود.</small></span>
        </div>
      </aside>

      <div class="p8-form-card">
        <div class="p8-section-head">
          <div>
            <span class="p8-kicker">SUPPORT FORM</span>
            <h2>اطلاعات درخواست</h2>
          </div>
        </div>

        <form method="post" class="p8-form">
          {% csrf_token %}
          {{ form.as_p }}
          {{ message_form.as_p }}

          <button class="p8-primary full" type="submit">
            ارسال تیکت
            <i class="fa-solid fa-arrow-left"></i>
          </button>
        </form>
      </div>

    </div>
  </div>
</section>
{% endblock %}
'''


SUPPORT_DETAIL_TEMPLATE = r'''
{% extends 'perfume_base.html' %}
{% block title %}{{ ticket.reference }} | پشتیبانی{% endblock %}
{% block content %}
<section class="p8-page">
  <div class="p8-wrap">

    <header class="p8-page-head">
      <div>
        <span class="p8-kicker">{{ ticket.reference }}</span>
        <h1>{{ ticket.subject }}</h1>
        <p>
          وضعیت: {{ ticket.get_status_display }}
          {% if ticket.order %} · سفارش #{{ ticket.order.order_number }}{% endif %}
        </p>
      </div>
      <a class="p8-secondary" href="{% url 'customer_care:support_home' %}">بازگشت به تیکت‌ها</a>
    </header>

    <div class="p8-thread-layout">

      <section class="p8-thread">
        {% for message in ticket.messages.all %}
        <article class="p8-message {% if message.is_staff_reply %}staff{% else %}customer{% endif %}">
          <div class="p8-message-meta">
            <span>
              {% if message.is_staff_reply %}
              <i class="fa-solid fa-headset"></i> پشتیبانی
              {% else %}
              <i class="fa-regular fa-user"></i> شما
              {% endif %}
            </span>
            <small>{{ message.created_at|date:'Y/m/d H:i' }}</small>
          </div>
          <p>{{ message.body|linebreaksbr }}</p>
        </article>
        {% empty %}
        <div class="p8-empty-card compact"><p>هنوز پیامی برای این تیکت ثبت نشده است.</p></div>
        {% endfor %}
      </section>

      <aside class="p8-thread-side">
        <span class="p8-kicker">TICKET STATUS</span>
        <h2>{{ ticket.get_status_display }}</h2>

        {% if ticket.order %}
        <div class="p8-thread-order">
          <small>سفارش مرتبط</small>
          <strong>#{{ ticket.order.order_number }}</strong>
        </div>
        {% endif %}

        {% if ticket.status != 'closed' %}
        <form method="post" action="{% url 'customer_care:support_reply' ticket.reference %}" class="p8-form">
          {% csrf_token %}
          {{ message_form.as_p }}
          <button class="p8-primary full" type="submit">
            ارسال پاسخ
            <i class="fa-solid fa-arrow-left"></i>
          </button>
        </form>
        {% else %}
        <div class="p8-closed-note">این تیکت بسته شده است.</div>
        {% endif %}
      </aside>

    </div>
  </div>
</section>
{% endblock %}
'''


CSS_TEXT = r'''
/* PHASE 08 — centered layouts for cart/wishlist/profile/support */

.p8-page{
  width:100%;
  padding:42px 0 88px;
  background:
    radial-gradient(circle at 82% 3%,rgba(174,107,46,.08),transparent 23%),
    var(--p-bg);
}

.p8-wrap{
  width:min(1320px,calc(100% - 48px));
  margin-inline:auto;
}

.p8-page-head{
  min-height:190px;
  padding:34px 38px;
  margin-bottom:18px;
  display:flex;
  align-items:flex-end;
  justify-content:space-between;
  gap:30px;
  border:1px solid var(--p-line);
  background:
    radial-gradient(circle at 88% 16%,rgba(185,118,52,.11),transparent 22%),
    linear-gradient(130deg,var(--p-surface),var(--p-surface-2));
  box-shadow:0 18px 45px rgba(0,0,0,.05);
}

.p8-page-head h1{
  margin:8px 0 8px!important;
  font-size:clamp(38px,4.2vw,64px)!important;
  line-height:1.05!important;
  font-weight:800!important;
}

.p8-page-head p{
  margin:0;
  color:var(--p-muted)!important;
  line-height:1.9;
}

.p8-kicker{
  color:var(--p-gold);
  letter-spacing:.19em;
  font-size:9px;
  font-weight:700;
}

.p8-head-mark{
  width:86px;
  height:86px;
  flex:none;
  border:1px solid var(--p-line-strong);
  border-radius:50%;
  display:grid;
  place-items:center;
  color:var(--p-gold);
  background:var(--p-bg);
  font-size:27px;
}

.p8-primary,.p8-secondary{
  min-height:48px;
  padding:0 18px;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  gap:10px;
  border:1px solid var(--p-line-strong);
  transition:.22s;
}

.p8-primary{
  border-color:transparent;
  background:linear-gradient(120deg,var(--p-gold-pale),var(--p-gold-deep));
  color:#171008!important;
}

.p8-secondary{
  background:transparent;
  color:var(--p-text)!important;
}

.p8-primary:hover,.p8-secondary:hover{transform:translateY(-2px)}
.p8-primary.full,.p8-secondary.full{width:100%}

.p8-empty-card{
  min-height:420px;
  padding:55px 28px;
  border:1px solid var(--p-line);
  background:
    radial-gradient(circle at 50% 42%,rgba(165,99,40,.10),transparent 24%),
    linear-gradient(145deg,var(--p-surface),var(--p-surface-2));
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  text-align:center;
}

.p8-empty-card.compact{min-height:260px}

.p8-empty-icon{
  width:82px;
  height:82px;
  margin-bottom:18px;
  border:1px solid var(--p-line-strong);
  border-radius:50%;
  display:grid;
  place-items:center;
  color:var(--p-gold);
  font-size:27px;
}

.p8-empty-card h2,.p8-empty-card h3{margin:9px 0 7px!important}
.p8-empty-card h2{font-size:31px!important}
.p8-empty-card p{max-width:560px;color:var(--p-muted)!important;line-height:1.9}
.p8-empty-card .p8-primary{margin-top:16px}

/* cart */
.p8-cart-layout{
  display:grid;
  grid-template-columns:minmax(0,1fr) 340px;
  gap:18px;
  align-items:start;
}

.p8-cart-list{display:grid;gap:10px}

.p8-cart-item{
  min-height:150px;
  padding:16px;
  display:grid;
  grid-template-columns:120px minmax(0,1fr) 190px 44px;
  gap:18px;
  align-items:center;
  border:1px solid var(--p-line);
  background:linear-gradient(145deg,var(--p-surface),var(--p-surface-2));
}

.p8-cart-image{
  height:116px;
  display:grid;
  place-items:center;
  background:var(--p-bg);
  border:1px solid var(--p-line);
  color:var(--p-gold)!important;
  font-size:28px;
}

.p8-cart-image img{width:100%;height:100%;object-fit:contain;padding:8px}
.p8-cart-copy small{color:var(--p-gold)!important;font-size:9px}
.p8-cart-copy h3{margin:4px 0 7px!important;font-size:18px!important}
.p8-cart-copy>span{display:block;color:var(--p-muted)!important;font-size:11px}
.p8-cart-copy strong{display:block;margin-top:11px;font-size:14px}

.p8-cart-copy em,.p8-wish-bottom em,.p8-summary-total em{
  color:var(--p-muted);
  font-size:9px;
  font-style:normal;
  font-weight:400;
}

.p8-cart-qty{display:grid;gap:6px}
.p8-cart-qty>label{color:var(--p-muted);font-size:10px}
.p8-cart-qty>div{display:grid;grid-template-columns:62px 1fr}

.p8-cart-qty input{
  min-width:0;
  height:42px;
  padding:0 7px;
  border:1px solid var(--p-line)!important;
  background:var(--p-bg)!important;
  color:var(--p-text)!important;
  text-align:center;
}

.p8-cart-qty button{
  border:0;
  background:var(--p-gold);
  color:#171008;
  cursor:pointer;
  font-size:10px;
}

.p8-remove{
  width:42px;
  height:42px;
  border:1px solid var(--p-line);
  background:transparent;
  color:var(--p-muted);
  display:grid;
  place-items:center;
  cursor:pointer;
}

.p8-remove:hover{border-color:#9c5148;color:#d77c72}

.p8-summary{
  position:sticky;
  top:220px;
  padding:25px;
  border:1px solid var(--p-line);
  background:linear-gradient(145deg,var(--p-surface),var(--p-surface-2));
  box-shadow:var(--p-shadow);
}

.p8-summary h2{margin:8px 0 20px!important;font-size:27px!important}

.p8-summary-row,.p8-summary-total{
  display:flex;
  justify-content:space-between;
  gap:15px;
}

.p8-summary-row{
  padding:11px 0;
  border-bottom:1px solid var(--p-line);
  color:var(--p-muted);
  font-size:11px;
}

.p8-summary-total{padding:19px 0;align-items:end}
.p8-summary-total strong{color:var(--p-gold);font-size:19px}
.p8-summary .p8-secondary{margin-top:8px}

/* wishlist */
.p8-wishlist-grid{
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:12px;
}

.p8-wish-card{
  overflow:hidden;
  border:1px solid var(--p-line);
  background:linear-gradient(145deg,var(--p-surface),var(--p-surface-2));
  transition:.25s;
}

.p8-wish-card:hover{
  transform:translateY(-4px);
  border-color:var(--p-line-strong);
  box-shadow:var(--p-shadow);
}

.p8-wish-image{
  height:280px;
  display:grid;
  place-items:center;
  background:
    radial-gradient(circle at 50% 72%,rgba(158,95,39,.11),transparent 42%),
    var(--p-bg);
  color:var(--p-gold)!important;
  font-size:34px;
}

.p8-wish-image img{width:100%;height:100%;object-fit:contain;padding:19px}
.p8-wish-copy{padding:16px}
.p8-wish-copy>small{color:var(--p-gold)!important;font-size:9px}

.p8-wish-title{
  min-height:47px;
  margin-top:4px;
  display:block;
  color:var(--p-text)!important;
  font-size:14px;
  font-weight:700;
  line-height:1.75;
}

.p8-wish-bottom{
  margin-top:13px;
  padding-top:12px;
  border-top:1px solid var(--p-line);
  display:flex;
  align-items:end;
  justify-content:space-between;
  gap:10px;
}

/* profile */
.p8-profile-layout{
  display:grid;
  grid-template-columns:310px minmax(0,1fr);
  gap:18px;
  align-items:start;
}

.p8-profile-card,.p8-details-card{
  border:1px solid var(--p-line);
  background:linear-gradient(145deg,var(--p-surface),var(--p-surface-2));
}

.p8-profile-card{padding:30px 24px;text-align:center}

.p8-avatar{
  width:104px;
  height:104px;
  margin:0 auto 20px;
  overflow:hidden;
  border:1px solid var(--p-line-strong);
  border-radius:50%;
  background:var(--p-bg);
  display:grid;
  place-items:center;
  color:var(--p-gold);
  font-size:38px;
  font-family:Georgia,"Times New Roman",serif!important;
}

.p8-avatar img{width:100%;height:100%;object-fit:cover}
.p8-profile-card h2{margin:7px 0 3px!important;font-size:27px!important}
.p8-profile-card>p{margin:0 0 19px;color:var(--p-muted)!important;overflow-wrap:anywhere}

.p8-user-badges{display:grid;gap:7px;margin:0 0 20px}

.p8-user-badges span{
  min-height:38px;
  padding:0 11px;
  border:1px solid var(--p-line);
  display:flex;
  align-items:center;
  justify-content:center;
  gap:8px;
  color:var(--p-muted);
  font-size:10px;
}

.p8-user-badges i{color:var(--p-gold)}
.p8-profile-card .p8-primary{margin-top:8px}
.p8-profile-main{display:grid;gap:18px}

.p8-profile-actions{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:10px;
}

.p8-profile-actions>a{
  min-height:112px;
  padding:19px;
  display:grid;
  grid-template-columns:50px 1fr 20px;
  gap:14px;
  align-items:center;
  border:1px solid var(--p-line);
  background:linear-gradient(145deg,var(--p-surface),var(--p-surface-2));
  transition:.22s;
}

.p8-profile-actions>a:hover{
  border-color:var(--p-line-strong);
  transform:translateY(-3px);
}

.p8-profile-actions>a>i{
  width:50px;
  height:50px;
  border:1px solid var(--p-line-strong);
  border-radius:50%;
  display:grid;
  place-items:center;
  color:var(--p-gold);
  font-size:18px;
}

.p8-profile-actions strong{display:block;color:var(--p-text)}
.p8-profile-actions small{color:var(--p-muted)!important}
.p8-profile-actions b{color:var(--p-gold)}

.p8-details-card{padding:28px}

.p8-section-head{
  margin-bottom:21px;
  display:flex;
  align-items:end;
  justify-content:space-between;
  gap:20px;
}

.p8-section-head h2{margin:6px 0 0!important;font-size:28px!important}

.p8-detail-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:9px;
}

.p8-detail-grid>div{
  min-height:88px;
  padding:16px;
  border:1px solid var(--p-line);
  background:var(--p-bg);
}

.p8-detail-grid small{
  display:block;
  margin-bottom:5px;
  color:var(--p-muted)!important;
  font-size:9px;
}

.p8-detail-grid strong{overflow-wrap:anywhere;font-size:13px}

/* support */
.p8-support-layout{
  display:grid;
  grid-template-columns:330px minmax(0,1fr);
  gap:18px;
}

.p8-support-side,.p8-ticket-list,.p8-form-aside,.p8-form-card,.p8-thread,.p8-thread-side{
  border:1px solid var(--p-line);
  background:linear-gradient(145deg,var(--p-surface),var(--p-surface-2));
}

.p8-support-side{
  min-height:480px;
  padding:35px 28px;
  position:relative;
  overflow:hidden;
}

.p8-support-side>i{
  width:72px;
  height:72px;
  margin-bottom:28px;
  border:1px solid var(--p-line-strong);
  border-radius:50%;
  display:grid;
  place-items:center;
  color:var(--p-gold);
  font-size:25px;
}

.p8-support-side h2{margin:8px 0 13px!important;font-size:32px!important;line-height:1.25!important}
.p8-support-side>p{color:var(--p-muted)!important;line-height:1.9}
.p8-support-side>div{margin-top:30px;display:grid;gap:8px}

.p8-support-side>div span{
  padding:10px 0;
  border-bottom:1px solid var(--p-line);
  color:var(--p-muted);
  font-size:11px;
}

.p8-support-side>div b{
  display:inline-block;
  width:32px;
  color:var(--p-gold);
  font-size:9px;
}

.p8-ticket-list{padding:28px}

.p8-ticket-row{
  min-height:90px;
  margin-top:8px;
  padding:16px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:20px;
  border:1px solid var(--p-line);
  background:var(--p-bg);
  transition:.22s;
}

.p8-ticket-row:hover{border-color:var(--p-line-strong);transform:translateX(-3px)}
.p8-ticket-row small{display:block;color:var(--p-gold)!important;font-size:9px}
.p8-ticket-row strong{display:block;margin:3px 0}
.p8-ticket-row span{color:var(--p-muted);font-size:10px}
.p8-ticket-status{display:flex;align-items:center;gap:13px}
.p8-ticket-status>span{padding:6px 9px;border:1px solid var(--p-line)}
.p8-ticket-status i{color:var(--p-gold)}

/* support create */
.p8-form-layout{
  display:grid;
  grid-template-columns:340px minmax(0,1fr);
  gap:18px;
}

.p8-form-aside,.p8-form-card{padding:30px}
.p8-form-aside h2{margin:8px 0 25px!important;font-size:31px!important}

.p8-form-tip{
  min-height:86px;
  padding:14px 0;
  display:grid;
  grid-template-columns:42px 1fr;
  gap:10px;
  border-bottom:1px solid var(--p-line);
}

.p8-form-tip>b{color:var(--p-gold);font-size:10px}
.p8-form-tip strong{display:block;margin-bottom:3px}
.p8-form-tip small{color:var(--p-muted)!important;line-height:1.8}

.p8-form{display:grid;gap:15px}

.p8-form p{
  margin:0!important;
  display:grid!important;
  gap:6px!important;
  color:var(--p-muted)!important;
  font-size:11px!important;
}

.p8-form label{color:var(--p-muted)!important}

.p8-form input:not([type="checkbox"]):not([type="radio"]),
.p8-form select,
.p8-form textarea{
  width:100%!important;
  min-width:0!important;
  border:1px solid var(--p-line)!important;
  background:var(--p-bg)!important;
  color:var(--p-text)!important;
  outline:none!important;
  box-shadow:none!important;
}

.p8-form input:not([type="checkbox"]):not([type="radio"]),
.p8-form select{
  min-height:50px!important;
  padding:0 12px!important;
}

.p8-form textarea{
  min-height:150px!important;
  padding:12px!important;
  resize:vertical;
}

.p8-form input:focus,.p8-form select:focus,.p8-form textarea:focus{
  border-color:var(--p-line-strong)!important;
  box-shadow:0 0 0 4px rgba(190,137,70,.06)!important;
}

.p8-form .helptext{color:var(--p-muted)!important;font-size:9px!important}

.p8-form ul.errorlist{
  margin:0!important;
  padding:9px 12px!important;
  list-style:none!important;
  border:1px solid rgba(194,90,78,.3);
  color:#e5968d;
  font-size:10px;
}

/* support detail */
.p8-thread-layout{
  display:grid;
  grid-template-columns:minmax(0,1fr) 340px;
  gap:18px;
  align-items:start;
}

.p8-thread{min-height:500px;padding:26px}

.p8-message{
  width:min(78%,760px);
  margin-bottom:12px;
  padding:18px;
  border:1px solid var(--p-line);
}

.p8-message.customer{margin-right:0;margin-left:auto;background:var(--p-bg)}
.p8-message.staff{margin-right:auto;margin-left:0;background:var(--p-surface-2)}

.p8-message-meta{
  margin-bottom:10px;
  display:flex;
  justify-content:space-between;
  gap:20px;
  color:var(--p-muted);
  font-size:9px;
}

.p8-message-meta i{margin-left:5px;color:var(--p-gold)}
.p8-message p{margin:0!important;color:var(--p-text)!important;line-height:2}

.p8-thread-side{
  position:sticky;
  top:220px;
  padding:25px;
}

.p8-thread-side h2{margin:8px 0 20px!important;font-size:28px!important}

.p8-thread-order{
  margin-bottom:20px;
  padding:15px;
  border:1px solid var(--p-line);
  background:var(--p-bg);
}

.p8-thread-order small{display:block;color:var(--p-muted)!important;margin-bottom:4px}
.p8-thread-order strong{color:var(--p-gold)}

.p8-closed-note{
  padding:16px;
  border:1px solid var(--p-line);
  color:var(--p-muted);
  text-align:center;
}

/* day */
html[data-perfume-theme="day"] .p8-page{
  background:
    radial-gradient(circle at 82% 2%,rgba(155,91,35,.08),transparent 22%),
    #e9dccd;
}

html[data-perfume-theme="day"] .p8-page-head,
html[data-perfume-theme="day"] .p8-cart-item,
html[data-perfume-theme="day"] .p8-summary,
html[data-perfume-theme="day"] .p8-wish-card,
html[data-perfume-theme="day"] .p8-profile-card,
html[data-perfume-theme="day"] .p8-details-card,
html[data-perfume-theme="day"] .p8-profile-actions>a,
html[data-perfume-theme="day"] .p8-support-side,
html[data-perfume-theme="day"] .p8-ticket-list,
html[data-perfume-theme="day"] .p8-form-aside,
html[data-perfume-theme="day"] .p8-form-card,
html[data-perfume-theme="day"] .p8-thread,
html[data-perfume-theme="day"] .p8-thread-side,
html[data-perfume-theme="day"] .p8-empty-card{
  background:linear-gradient(145deg,#fffdf9,#f2e5d6)!important;
}

html[data-perfume-theme="day"] .p8-cart-image,
html[data-perfume-theme="day"] .p8-wish-image,
html[data-perfume-theme="day"] .p8-detail-grid>div,
html[data-perfume-theme="day"] .p8-ticket-row,
html[data-perfume-theme="day"] .p8-thread-order,
html[data-perfume-theme="day"] .p8-form input:not([type="checkbox"]):not([type="radio"]),
html[data-perfume-theme="day"] .p8-form select,
html[data-perfume-theme="day"] .p8-form textarea{
  background:#f8efe5!important;
}

/* night */
html[data-perfume-theme="night"] .p8-page-head,
html[data-perfume-theme="night"] .p8-cart-item,
html[data-perfume-theme="night"] .p8-summary,
html[data-perfume-theme="night"] .p8-wish-card,
html[data-perfume-theme="night"] .p8-profile-card,
html[data-perfume-theme="night"] .p8-details-card,
html[data-perfume-theme="night"] .p8-profile-actions>a,
html[data-perfume-theme="night"] .p8-support-side,
html[data-perfume-theme="night"] .p8-ticket-list,
html[data-perfume-theme="night"] .p8-form-aside,
html[data-perfume-theme="night"] .p8-form-card,
html[data-perfume-theme="night"] .p8-thread,
html[data-perfume-theme="night"] .p8-thread-side,
html[data-perfume-theme="night"] .p8-empty-card{
  background:linear-gradient(145deg,#17110d,#21160f)!important;
}

html[data-perfume-theme="night"] .p8-cart-image,
html[data-perfume-theme="night"] .p8-wish-image,
html[data-perfume-theme="night"] .p8-detail-grid>div,
html[data-perfume-theme="night"] .p8-ticket-row,
html[data-perfume-theme="night"] .p8-thread-order,
html[data-perfume-theme="night"] .p8-form input:not([type="checkbox"]):not([type="radio"]),
html[data-perfume-theme="night"] .p8-form select,
html[data-perfume-theme="night"] .p8-form textarea{
  background:#0f0b09!important;
}

@media(max-width:1050px){
  .p8-cart-layout,
  .p8-profile-layout,
  .p8-support-layout,
  .p8-form-layout,
  .p8-thread-layout{
    grid-template-columns:1fr;
  }

  .p8-summary,.p8-thread-side{position:static}
  .p8-wishlist-grid{grid-template-columns:repeat(3,minmax(0,1fr))}
  .p8-profile-card{text-align:right}
  .p8-avatar{margin-right:0;margin-left:0}
}

@media(max-width:760px){
  .p8-wrap{width:calc(100% - 26px)}
  .p8-page{padding:25px 0 58px}

  .p8-page-head{
    min-height:auto;
    padding:27px 21px;
    align-items:flex-start;
    flex-direction:column;
  }

  .p8-head-mark{display:none}

  .p8-cart-item{
    grid-template-columns:90px minmax(0,1fr) 42px;
  }

  .p8-cart-image{height:100px}
  .p8-cart-qty{grid-column:1/-1}
  .p8-cart-item>form:last-child{grid-column:3;grid-row:1}
  .p8-wishlist-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .p8-profile-actions{grid-template-columns:1fr}
  .p8-detail-grid{grid-template-columns:1fr}
  .p8-message{width:92%}
}

@media(max-width:520px){
  .p8-wishlist-grid{grid-template-columns:1fr}
  .p8-wish-image{height:350px}

  .p8-cart-item{
    grid-template-columns:76px minmax(0,1fr) 38px;
    gap:11px;
    padding:12px;
  }

  .p8-cart-image{height:84px}
  .p8-page-head h1{font-size:40px!important}
}
'''


FILES = {
    "first/templates/cart/cart.html": CART_TEMPLATE,
    "first/templates/products/wishlist.html": WISHLIST_TEMPLATE,
    "first/templates/profile.html": PROFILE_TEMPLATE,
    "customer_care/templates/customer_care/support_home.html": SUPPORT_HOME_TEMPLATE,
    "customer_care/templates/customer_care/support_create.html": SUPPORT_CREATE_TEMPLATE,
    "customer_care/templates/customer_care/support_detail.html": SUPPORT_DETAIL_TEMPLATE,
}


def main():
    print("=" * 84)
    print(" PHASE 08 — ACCOUNT / CART / SUPPORT LAYOUT FIX")
    print("=" * 84)

    if not (ROOT / "manage.py").exists():
        raise SystemExit("Put this script beside manage.py.")

    if not BASE.exists():
        raise SystemExit("first/templates/perfume_base.html not found.")

    if BACKUP.exists():
        raise SystemExit(
            f"Backup already exists: {BACKUP}\n"
            "Rename/delete it only if you intentionally want to rerun Phase 08."
        )

    BACKUP.mkdir(parents=True)

    snapshot = {
        rel: (ROOT / rel).read_bytes()
        for rel in BACKEND_GUARD
        if (ROOT / rel).exists()
    }

    write(CSS, CSS_TEXT)
    patch_base()

    for rel, content in FILES.items():
        target = ROOT / rel
        if target.exists():
            write(target, content)
        else:
            print("[WARN] Missing template, skipped:", rel)

    for rel, before in snapshot.items():
        if (ROOT / rel).read_bytes() != before:
            raise RuntimeError("Backend changed unexpectedly: " + rel)

    print("\n[CHECK] Django")
    run(sys.executable, "manage.py", "check")

    print("\n[CHECK] No migration drift")
    run(
        sys.executable,
        "manage.py",
        "makemigrations",
        "--check",
        "--dry-run",
    )

    print("\n" + "=" * 84)
    print(" PHASE 08 READY")
    print("=" * 84)
    print("✓ Cart fixed and centered")
    print("✓ Wishlist fixed and centered")
    print("✓ Profile rebuilt as account dashboard")
    print("✓ Support home fixed")
    print("✓ New ticket page fixed")
    print("✓ Ticket detail/reply page fixed")
    print("✓ Day/night supported")
    print("✓ Shared header/footer preserved")
    print("✓ Backend unchanged")
    print("")
    print("Run:")
    print("  python manage.py runserver")
    print("Then hard refresh browser with Ctrl+F5")


if __name__ == "__main__":
    main()
