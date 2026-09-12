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
BACKUP = ROOT / ".perfume_frontend_phase11_backup"

ADMIN_BASE = ROOT / "first/templates/dashboard/perfume_admin_base.html"
ADD_PRODUCT = ROOT / "first/templates/dashboard/admin_add_product.html"
ADMIN_CSS = ROOT / "static/css/perfume-admin-v2.css"
ADMIN_JS = ROOT / "static/js/perfume-admin-v2.js"
ANALYTICS_VIEWS = ROOT / "first/analytics_views.py"
URLS = ROOT / "first/urls.py"

PROTECTED = [
    "first/models.py",
    "first/views.py",
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
    if not URLS.exists():
        return set()
    src = URLS.read_text(encoding="utf-8", errors="ignore")
    return set(re.findall(r"name\s*=\s*['\"]([^'\"]+)['\"]", src))

OWNER_MENU = r'''
<details class="pa-account" data-pa-account>
  <summary class="pa-account-trigger" aria-label="منوی حساب مالک">
    <span class="pa-account-avatar">{{ user.username|first|upper }}</span>
    <span class="pa-account-copy">
      <strong>{{ user.username }}</strong>
      <small>{% if user.is_superuser %}مالک فروشگاه{% else %}مدیر فروشگاه{% endif %}</small>
    </span>
    <i class="fa-solid fa-chevron-down pa-account-chevron"></i>
  </summary>

  <div class="pa-account-dropdown">
    <div class="pa-account-head">
      <span class="pa-account-avatar large">{{ user.username|first|upper }}</span>
      <span>
        <strong>{{ user.username }}</strong>
        <small>{{ user.email|default:'حساب مدیریت' }}</small>
      </span>
    </div>

    <div class="pa-account-links">
      <a href="{% url 'first:owner_panel' %}">
        <i class="fa-solid fa-crown"></i>
        <span>پنل مالک</span>
      </a>

      <a href="{% url 'first:profile' %}">
        <i class="fa-regular fa-user"></i>
        <span>حساب کاربری</span>
      </a>

      <a href="{% url 'first:customizer' %}">
        <i class="fa-solid fa-wand-magic-sparkles"></i>
        <span>طراحی بصری سایت</span>
      </a>

      <a href="{% url 'first:home' %}" target="_blank" rel="noopener">
        <i class="fa-solid fa-arrow-up-right-from-square"></i>
        <span>مشاهده فروشگاه</span>
      </a>
    </div>

    <form class="pa-account-logout" method="post" action="{% url 'first:logout' %}">
      {% csrf_token %}
      <button type="submit">
        <i class="fa-solid fa-arrow-right-from-bracket"></i>
        <span>خروج از حساب</span>
      </button>
    </form>
  </div>
</details>
'''

ADD_PRODUCT_TEMPLATE = r'''
{% extends 'dashboard/perfume_admin_base.html' %}
{% load static %}

{% block admin_title %}افزودن عطر جدید{% endblock %}
{% block admin_heading %}مدیریت عطرها{% endblock %}

{% block admin_content %}
<section class="pf-product-editor" data-perfume-product-editor>
  <header class="pf-editor-hero">
    <div>
      <span class="pf-eyebrow">NEW FRAGRANCE</span>
      <h1>افزودن عطر جدید</h1>
      <p>
        مشخصات رایحه، برند، غلظت، حجم‌ها، تصاویر و وضعیت فروش را
        برای محصول جدید ثبت کنید.
      </p>
    </div>
    <a class="pf-back" href="{% url 'first:admin_products' %}">
      <i class="fa-solid fa-arrow-right"></i>
      بازگشت به عطرها
    </a>
  </header>

  <form method="post" enctype="multipart/form-data" class="pf-editor-form">
    {% csrf_token %}

    <section class="pf-card">
      <div class="pf-card-title">
        <span class="pf-step">01</span>
        <div>
          <span class="pf-eyebrow">FRAGRANCE IDENTITY</span>
          <h2>هویت عطر</h2>
          <p>اطلاعات اصلی که مشتری در کارت و صفحه محصول می‌بیند.</p>
        </div>
        <i class="fa-solid fa-spray-can-sparkles"></i>
      </div>

      <div class="pf-grid two">
        <label class="pf-field wide">
          <span>نام کامل عطر <b>*</b></span>
          <input type="text" name="name" maxlength="200" required
                 value="{{ form_data.name|default:'' }}"
                 placeholder="مثلاً Dior Sauvage Eau de Parfum">
        </label>

        <label class="pf-field">
          <span>دسته‌بندی رایحه</span>
          <select name="category">
            <option value="">بدون دسته‌بندی</option>
            {% for item in categories %}
            <option value="{{ item.id }}">{{ item.name }}</option>
            {% endfor %}
          </select>
          <small>زنانه، مردانه، یونی‌سکس، سمپل و دکانت، ست هدیه و...</small>
        </label>

        <label class="pf-field">
          <span>برند عطر</span>
          <select name="brand">
            <option value="">بدون برند</option>
            {% for item in brands %}
            <option value="{{ item.id }}">{{ item.name }}</option>
            {% endfor %}
          </select>
          <small>خانه عطر یا برند سازنده.</small>
        </label>

        <label class="pf-field">
          <span>غلظت / نوع عطر</span>
          <select name="product_type">
            <option value="">انتخاب نشده</option>
            {% for item in product_types %}
            <option value="{{ item.id }}">{{ item.name }}</option>
            {% endfor %}
          </select>
          <small>Parfum، Eau de Parfum، Eau de Toilette و...</small>
        </label>

        <div class="pf-field">
          <span>خانواده رایحه و کاربرد</span>
          <div class="pf-tag-box">
            {% for tag in tags %}
            <label class="pf-tag">
              <input type="checkbox" name="tags" value="{{ tag.id }}">
              <span>{{ tag.name }}</span>
            </label>
            {% empty %}
            <p class="pf-empty-note">هنوز تگی تعریف نشده است.</p>
            {% endfor %}
          </div>
          <small>مثلاً گرم، خنک، چوبی، مرکباتی، گلی، رسمی یا روزمره.</small>
        </div>
      </div>
    </section>

    <section class="pf-card">
      <div class="pf-card-title">
        <span class="pf-step">02</span>
        <div>
          <span class="pf-eyebrow">PRICING & STOCK</span>
          <h2>قیمت و موجودی</h2>
          <p>اگر عطر چند حجم دارد، موجودی هر حجم را پایین‌تر جداگانه ثبت کنید.</p>
        </div>
        <i class="fa-solid fa-coins"></i>
      </div>

      <div class="pf-grid three">
        <label class="pf-field">
          <span>قیمت پایه <b>*</b></span>
          <div class="pf-money">
            <input type="number" name="price" min="0" step="1" required
                   value="{{ form_data.price|default:'' }}" placeholder="0">
            <small>تومان</small>
          </div>
        </label>

        <label class="pf-field">
          <span>قیمت ویژه</span>
          <div class="pf-money">
            <input type="number" name="discount_price" min="0" step="1"
                   value="{{ form_data.discount_price|default:'' }}" placeholder="اختیاری">
            <small>تومان</small>
          </div>
        </label>

        <label class="pf-field" data-base-stock>
          <span>موجودی محصول تک‌حجم</span>
          <input type="number" name="stock" min="0" step="1"
                 value="{{ form_data.stock|default:'0' }}">
          <small>برای محصول چندحجمی، موجودی از جدول حجم‌ها محاسبه می‌شود.</small>
        </label>
      </div>
    </section>

    <section class="pf-card">
      <div class="pf-card-title">
        <span class="pf-step">03</span>
        <div>
          <span class="pf-eyebrow">PRODUCT PHOTOGRAPHY</span>
          <h2>تصاویر عطر</h2>
          <p>تصاویر واضح شیشه و بسته‌بندی را بارگذاری کنید؛ اولین تصویر به‌صورت پیش‌فرض اصلی است.</p>
        </div>
        <i class="fa-regular fa-images"></i>
      </div>

      <label class="pf-upload">
        <input type="file" name="product_images"
               accept="image/jpeg,image/png,image/webp"
               multiple required data-product-images>
        <span class="pf-upload-icon"><i class="fa-solid fa-cloud-arrow-up"></i></span>
        <strong>انتخاب تصاویر محصول</strong>
        <small>حداکثر ۸ تصویر. JPG / PNG / WEBP</small>
      </label>

      <input type="hidden" name="main_image_index" value="0" data-main-image-index>
      <div class="pf-image-preview" data-image-preview></div>
      <p class="pf-preview-help" data-preview-help hidden>
        برای انتخاب تصویر اصلی روی تصویر موردنظر کلیک کنید.
      </p>
    </section>

    <section class="pf-card">
      <div class="pf-card-title">
        <span class="pf-step">04</span>
        <div>
          <span class="pf-eyebrow">BOTTLE SIZES</span>
          <h2>حجم‌ها و نسخه‌های قابل فروش</h2>
          <p>
            برای عطرهای ۳۰، ۵۰، ۷۵، ۱۰۰ میلی‌لیتر یا ادیشن‌های مختلف،
            هر گزینه را به‌عنوان یک تنوع ثبت کنید.
          </p>
        </div>
        <i class="fa-solid fa-flask"></i>
      </div>

      <label class="pf-switch-row">
        <span>
          <strong>این عطر چند حجم / نسخه دارد</strong>
          <small>با فعال‌کردن این گزینه، قیمت و موجودی هر حجم مستقل می‌شود.</small>
        </span>
        <input type="checkbox" name="has_variants" data-has-variants>
        <i></i>
      </label>

      <div class="pf-variants" data-variants hidden>
        <div class="pf-variant-head">
          <div>
            <span class="pf-eyebrow">AVAILABLE SIZES</span>
            <h3>حجم‌های عطر</h3>
          </div>
          <button type="button" class="pf-outline-btn" data-add-variant>
            <i class="fa-solid fa-plus"></i>
            افزودن حجم
          </button>
        </div>

        <div class="pf-variant-list" data-variant-list></div>

        <template data-variant-template>
          <article class="pf-variant-row" data-variant-row>
            <div class="pf-variant-number" data-variant-number>01</div>

            <label class="pf-field">
              <span>حجم شیشه (ml)</span>
              <input type="number" name="variant_volumes" min="1" step="1" placeholder="مثلاً 100">
            </label>

            <label class="pf-field">
              <span>نسخه / ادیشن</span>
              <input type="text" name="variant_sizes" maxlength="20" placeholder="مثلاً Refillable">
            </label>

            <label class="pf-field">
              <span>قیمت</span>
              <input type="number" name="variant_prices" min="0" step="1" placeholder="در صورت خالی، قیمت پایه">
            </label>

            <label class="pf-field">
              <span>قیمت ویژه</span>
              <input type="number" name="variant_discount_prices" min="0" step="1" placeholder="اختیاری">
            </label>

            <label class="pf-field">
              <span>موجودی</span>
              <input type="number" name="variant_stocks" min="0" step="1" value="0">
            </label>

            <label class="pf-default-variant">
              <input type="radio" name="variant_default" value="0" data-default-radio>
              <span>پیش‌فرض</span>
            </label>

            <button type="button" class="pf-remove-variant" data-remove-variant title="حذف این حجم">
              <i class="fa-regular fa-trash-can"></i>
            </button>
          </article>
        </template>
      </div>
    </section>

    <section class="pf-card">
      <div class="pf-card-title">
        <span class="pf-step">05</span>
        <div>
          <span class="pf-eyebrow">STORY & DETAILS</span>
          <h2>معرفی رایحه</h2>
          <p>توضیح کوتاه برای کارت محصول و متن کامل برای صفحه عطر.</p>
        </div>
        <i class="fa-regular fa-pen-to-square"></i>
      </div>

      <div class="pf-grid two">
        <label class="pf-field">
          <span>معرفی کوتاه</span>
          <textarea name="short_description" rows="5"
                    placeholder="حس کلی رایحه، مناسب چه موقعیت یا فصلی است و...">{{ form_data.short_description|default:'' }}</textarea>
        </label>

        <label class="pf-field">
          <span>توضیحات کامل</span>
          <textarea name="description" rows="8"
                    placeholder="داستان رایحه، شخصیت عطر، تجربه بویایی، نحوه استفاده و اطلاعات تکمیلی...">{{ form_data.description|default:'' }}</textarea>
        </label>
      </div>
    </section>

    <section class="pf-card">
      <div class="pf-card-title">
        <span class="pf-step">06</span>
        <div>
          <span class="pf-eyebrow">STORE PLACEMENT</span>
          <h2>نمایش در فروشگاه</h2>
          <p>مشخص کنید این عطر در کدام بخش‌های فروشگاه برجسته شود.</p>
        </div>
        <i class="fa-regular fa-eye"></i>
      </div>

      <div class="pf-status-grid">
        <label class="pf-status-option primary">
          <input type="checkbox" name="is_active" checked>
          <span><i class="fa-solid fa-check"></i></span>
          <div><strong>فعال و قابل فروش</strong><small>محصول در فروشگاه قابل مشاهده باشد.</small></div>
        </label>

        <label class="pf-status-option">
          <input type="checkbox" name="is_featured">
          <span><i class="fa-regular fa-gem"></i></span>
          <div><strong>انتخاب ویژه</strong><small>برای بخش عطرهای منتخب صفحه اصلی.</small></div>
        </label>

        <label class="pf-status-option">
          <input type="checkbox" name="is_new">
          <span><i class="fa-solid fa-sparkles"></i></span>
          <div><strong>رایحه جدید</strong><small>با نشان محصول جدید نمایش داده شود.</small></div>
        </label>

        <label class="pf-status-option">
          <input type="checkbox" name="is_best_seller">
          <span><i class="fa-solid fa-crown"></i></span>
          <div><strong>پرفروش</strong><small>در انتخاب‌های محبوب فروشگاه قرار بگیرد.</small></div>
        </label>
      </div>
    </section>

    <div class="pf-editor-actions">
      <a href="{% url 'first:admin_products' %}" class="pf-cancel">انصراف</a>
      <button type="submit" class="pf-submit">
        ثبت عطر
        <i class="fa-solid fa-arrow-left"></i>
      </button>
    </div>
  </form>
</section>
{% endblock %}

{% block extra_js %}
{{ block.super }}
<script>
(() => {
  "use strict";

  const root = document.querySelector("[data-perfume-product-editor]");
  if (!root) return;

  const hasVariants = root.querySelector("[data-has-variants]");
  const variants = root.querySelector("[data-variants]");
  const list = root.querySelector("[data-variant-list]");
  const tpl = root.querySelector("[data-variant-template]");
  const baseStock = root.querySelector("[data-base-stock]");

  function renumber() {
    [...list.querySelectorAll("[data-variant-row]")].forEach((row, index) => {
      const n = row.querySelector("[data-variant-number]");
      const radio = row.querySelector("[data-default-radio]");
      if (n) n.textContent = String(index + 1).padStart(2, "0");
      if (radio) radio.value = String(index);
    });
  }

  function addVariant() {
    const fragment = tpl.content.cloneNode(true);
    list.appendChild(fragment);
    renumber();
    const rows = list.querySelectorAll("[data-variant-row]");
    if (rows.length === 1) {
      const radio = rows[0].querySelector("[data-default-radio]");
      if (radio) radio.checked = true;
    }
  }

  function syncVariantMode() {
    const on = hasVariants.checked;
    variants.hidden = !on;
    if (baseStock) baseStock.classList.toggle("muted", on);
    if (on && !list.querySelector("[data-variant-row]")) addVariant();
  }

  root.addEventListener("click", (event) => {
    if (event.target.closest("[data-add-variant]")) {
      addVariant();
      return;
    }

    const remove = event.target.closest("[data-remove-variant]");
    if (remove) {
      remove.closest("[data-variant-row]")?.remove();
      renumber();
      if (!list.querySelector("[data-variant-row]") && hasVariants.checked) addVariant();
    }
  });

  hasVariants.addEventListener("change", syncVariantMode);
  syncVariantMode();

  const imageInput = root.querySelector("[data-product-images]");
  const preview = root.querySelector("[data-image-preview]");
  const mainIndex = root.querySelector("[data-main-image-index]");
  const help = root.querySelector("[data-preview-help]");

  imageInput?.addEventListener("change", () => {
    preview.innerHTML = "";
    mainIndex.value = "0";
    const files = [...(imageInput.files || [])].slice(0, 8);
    if (help) help.hidden = files.length === 0;

    files.forEach((file, index) => {
      const url = URL.createObjectURL(file);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "pf-preview-item" + (index === 0 ? " selected" : "");
      button.dataset.index = String(index);
      button.innerHTML = `<img alt=""><span>${index === 0 ? "تصویر اصلی" : "انتخاب اصلی"}</span>`;
      button.querySelector("img").src = url;

      button.addEventListener("click", () => {
        mainIndex.value = String(index);
        preview.querySelectorAll(".pf-preview-item").forEach((x, i) => {
          x.classList.toggle("selected", i === index);
          const label = x.querySelector("span");
          if (label) label.textContent = i === index ? "تصویر اصلی" : "انتخاب اصلی";
        });
      });

      preview.appendChild(button);
    });
  });
})();
</script>
{% endblock %}
'''

CSS_TEXT = r'''
:root{
  --pa-bg:#0c0907!important;
  --pa-panel:#15100c!important;
  --pa-panel-2:#1d150f!important;
  --pa-card:#19120d!important;
  --pa-card-2:#21170f!important;
  --pa-text:#f5eee4!important;
  --pa-muted:#a99b8a!important;
  --pa-gold:#c9a36a!important;
  --pa-gold-2:#95652f!important;
  --pa-gold-soft:#e1c595!important;
  --pa-olive:#7b8062!important;
  --pa-terra:#8e5e49!important;
  --pa-line:rgba(201,163,106,.17)!important;
  --pa-line-strong:rgba(201,163,106,.38)!important;
  --pa-danger:#9e5d50!important;
  --pa-shadow:0 22px 65px rgba(0,0,0,.28)!important;
}
html[data-perfume-theme="day"]{
  --pa-bg:#e8dbc9!important;
  --pa-panel:#fffaf2!important;
  --pa-panel-2:#f2e4d2!important;
  --pa-card:#fffdf9!important;
  --pa-card-2:#f6eadc!important;
  --pa-text:#1b140f!important;
  --pa-muted:#766958!important;
  --pa-gold:#9b6a31!important;
  --pa-gold-2:#7e5228!important;
  --pa-gold-soft:#bb9159!important;
  --pa-olive:#697058!important;
  --pa-terra:#865946!important;
  --pa-line:rgba(110,77,43,.15)!important;
  --pa-line-strong:rgba(126,82,40,.34)!important;
  --pa-danger:#8e5047!important;
  --pa-shadow:0 20px 55px rgba(75,48,24,.11)!important;
}
.pa-body{background:radial-gradient(circle at 82% 0,rgba(174,111,49,.09),transparent 25%),var(--pa-bg)!important;color:var(--pa-text)!important}
.pa-sidebar,.pa-topbar,.pa-panel-card,.pa-panel-section,.pa-dashboard-hero,.pa-studio-panel,.pa-studio-top,.pa-content [class*="bg-white"],.pa-content [class*="bg-gray-"],.pa-content [class*="bg-slate-"]{border-color:var(--pa-line)!important}
.pa-topbar,.pa-sidebar{background:color-mix(in srgb,var(--pa-panel) 94%,transparent)!important}
.pa-nav-link.active,.pa-studio-link,.pa-action-card.gold,.pa-menu-button:hover,.pa-icon-button:hover{color:var(--pa-gold-soft)!important;border-color:var(--pa-line-strong)!important;background:linear-gradient(135deg,rgba(201,163,106,.13),rgba(126,82,40,.05))!important}
.pa-content [class*="text-pink-"],.pa-content [class*="text-fuchsia-"],.pa-content [class*="text-purple-"],.pa-content [class*="text-violet-"],.pa-content [class*="text-blue-"],.pa-content [class*="text-cyan-"],.pa-content [class*="text-emerald-"],.pa-content [class*="text-green-"],.pa-content [class*="text-yellow-"],.pa-content [class*="text-orange-"],.pa-content [class*="text-red-"],.pa-content [class*="text-rose-"]{color:var(--pa-gold-2)!important}
.pa-content [class*="bg-pink-"],.pa-content [class*="bg-fuchsia-"],.pa-content [class*="bg-purple-"],.pa-content [class*="bg-violet-"],.pa-content [class*="bg-blue-"],.pa-content [class*="bg-cyan-"],.pa-content [class*="bg-emerald-"],.pa-content [class*="bg-green-"],.pa-content [class*="bg-yellow-"],.pa-content [class*="bg-orange-"],.pa-content [class*="bg-red-"],.pa-content [class*="bg-rose-"]{background:linear-gradient(135deg,var(--pa-card-2),var(--pa-panel))!important;color:var(--pa-text)!important}
.pa-content [class*="border-pink-"],.pa-content [class*="border-purple-"],.pa-content [class*="border-violet-"],.pa-content [class*="border-blue-"],.pa-content [class*="border-green-"],.pa-content [class*="border-emerald-"],.pa-content [class*="border-yellow-"],.pa-content [class*="border-orange-"],.pa-content [class*="border-red-"]{border-color:var(--pa-line-strong)!important}

.pa-account{position:relative;direction:rtl}
.pa-account>summary{list-style:none}.pa-account>summary::-webkit-details-marker{display:none}
.pa-account-trigger{min-width:176px;min-height:48px;padding:6px 9px 6px 12px;border:1px solid var(--pa-line);border-radius:13px;display:grid;grid-template-columns:38px minmax(0,1fr) 14px;gap:9px;align-items:center;background:var(--pa-panel-2);cursor:pointer;transition:.2s}
.pa-account-trigger:hover,.pa-account[open] .pa-account-trigger{border-color:var(--pa-line-strong);box-shadow:var(--pa-shadow)}
.pa-account-avatar{width:38px;height:38px;border:1px solid var(--pa-line-strong);border-radius:50%;display:grid;place-items:center;background:linear-gradient(135deg,rgba(201,163,106,.18),rgba(142,94,73,.12));color:var(--pa-gold-soft);font-family:Georgia,serif!important;font-weight:700}
.pa-account-avatar.large{width:48px;height:48px}.pa-account-copy{min-width:0;display:grid;line-height:1.25}.pa-account-copy strong{overflow:hidden;text-overflow:ellipsis;color:var(--pa-text);font-size:12px}.pa-account-copy small{margin-top:3px;color:var(--pa-muted);font-size:8px}.pa-account-chevron{color:var(--pa-muted);font-size:9px;transition:.2s}.pa-account[open] .pa-account-chevron{transform:rotate(180deg)}
.pa-account-dropdown{position:absolute;z-index:80;top:calc(100% + 10px);left:0;width:270px;overflow:hidden;border:1px solid var(--pa-line-strong);border-radius:15px;background:var(--pa-panel);box-shadow:0 30px 80px rgba(0,0,0,.38)}
.pa-account-head{padding:16px;border-bottom:1px solid var(--pa-line);display:grid;grid-template-columns:48px 1fr;gap:11px;align-items:center}.pa-account-head>span:last-child{min-width:0;display:grid}.pa-account-head strong{color:var(--pa-text)}.pa-account-head small{margin-top:3px;overflow:hidden;text-overflow:ellipsis;color:var(--pa-muted);font-size:9px;direction:ltr;text-align:right}
.pa-account-links{padding:7px;display:grid;gap:2px}.pa-account-links a,.pa-account-logout button{width:100%;min-height:43px;padding:0 11px;border:0;border-radius:9px;display:flex;align-items:center;gap:10px;color:var(--pa-muted)!important;background:transparent;font:inherit;font-size:10px;cursor:pointer;text-align:right}.pa-account-links a:hover{color:var(--pa-text)!important;background:rgba(201,163,106,.08)}.pa-account-links i,.pa-account-logout i{width:22px;color:var(--pa-gold);text-align:center}.pa-account-logout{padding:7px;margin:0;border-top:1px solid var(--pa-line)}.pa-account-logout button{color:#c98779!important}.pa-account-logout button:hover{background:rgba(158,93,80,.11)}.pa-account-logout i{color:#b66d60}

.pf-product-editor{width:min(1200px,100%);margin-inline:auto}
.pf-editor-hero{min-height:180px;margin-bottom:14px;padding:30px 32px;border:1px solid var(--pa-line);display:flex;align-items:flex-end;justify-content:space-between;gap:24px;background:radial-gradient(circle at 88% 14%,rgba(201,163,106,.13),transparent 26%),linear-gradient(135deg,var(--pa-card),var(--pa-card-2))}
.pf-editor-hero h1{margin:7px 0 8px!important;color:var(--pa-text)!important;font-size:clamp(34px,4vw,52px)!important;line-height:1.1!important}.pf-editor-hero p{max-width:760px;margin:0;color:var(--pa-muted)!important}.pf-eyebrow{color:var(--pa-gold);font-size:8px;font-weight:800;letter-spacing:.2em}
.pf-back,.pf-outline-btn,.pf-cancel{min-height:43px;padding:0 15px;border:1px solid var(--pa-line-strong);border-radius:10px;display:inline-flex;align-items:center;justify-content:center;gap:8px;color:var(--pa-text)!important;background:transparent;font:inherit;cursor:pointer}
.pf-editor-form{display:grid;gap:14px}.pf-card{padding:28px;border:1px solid var(--pa-line);border-radius:18px;background:linear-gradient(145deg,var(--pa-card),var(--pa-panel-2));box-shadow:0 12px 38px rgba(0,0,0,.08)}
.pf-card-title{margin-bottom:24px;padding-bottom:20px;border-bottom:1px solid var(--pa-line);display:grid;grid-template-columns:44px minmax(0,1fr) 46px;gap:12px;align-items:center}.pf-step{width:38px;height:38px;border:1px solid var(--pa-line-strong);border-radius:50%;display:grid;place-items:center;color:var(--pa-gold);font-size:9px;font-family:Georgia,serif!important}.pf-card-title h2{margin:4px 0 2px!important;color:var(--pa-text)!important;font-size:24px!important}.pf-card-title p{margin:0;color:var(--pa-muted)!important;font-size:10px}.pf-card-title>i{width:46px;height:46px;border-radius:50%;display:grid;place-items:center;background:rgba(201,163,106,.09);color:var(--pa-gold);font-size:18px}
.pf-grid{display:grid;gap:16px}.pf-grid.two{grid-template-columns:repeat(2,minmax(0,1fr))}.pf-grid.three{grid-template-columns:repeat(3,minmax(0,1fr))}.pf-field{min-width:0;display:grid;gap:7px}.pf-field.wide{grid-column:1/-1}.pf-field>span{color:var(--pa-text);font-size:10px;font-weight:700}.pf-field>span b{color:var(--pa-gold)}.pf-field>small{color:var(--pa-muted)!important;font-size:8px;line-height:1.8}
.pf-field input:not([type="checkbox"]):not([type="radio"]),.pf-field select,.pf-field textarea{width:100%;min-width:0;border:1px solid var(--pa-line);border-radius:10px;background:var(--pa-bg);color:var(--pa-text);outline:none;font:inherit}.pf-field input:not([type="checkbox"]):not([type="radio"]),.pf-field select{min-height:48px;padding:0 12px}.pf-field textarea{min-height:140px;padding:12px;resize:vertical}.pf-field input:focus,.pf-field select:focus,.pf-field textarea:focus{border-color:var(--pa-line-strong);box-shadow:0 0 0 4px rgba(201,163,106,.06)}.pf-field.muted{opacity:.48}
.pf-money{position:relative}.pf-money input{padding-left:62px!important}.pf-money small{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--pa-muted);font-size:8px}
.pf-tag-box{min-height:104px;padding:11px;border:1px solid var(--pa-line);border-radius:10px;display:flex;flex-wrap:wrap;gap:7px;align-content:flex-start;background:var(--pa-bg)}.pf-tag input{position:absolute;opacity:0;pointer-events:none}.pf-tag span{min-height:31px;padding:0 10px;border:1px solid var(--pa-line);border-radius:999px;display:flex;align-items:center;color:var(--pa-muted);background:var(--pa-panel);font-size:9px;cursor:pointer}.pf-tag input:checked+span{color:var(--pa-text);border-color:var(--pa-line-strong);background:rgba(201,163,106,.12)}.pf-empty-note{margin:0;color:var(--pa-muted)}
.pf-upload{min-height:180px;padding:25px;border:1px dashed var(--pa-line-strong);border-radius:14px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;background:radial-gradient(circle at 50% 65%,rgba(201,163,106,.09),transparent 35%),var(--pa-bg);cursor:pointer}.pf-upload input{position:absolute;width:1px;height:1px;opacity:0}.pf-upload-icon{width:58px;height:58px;margin-bottom:4px;border:1px solid var(--pa-line-strong);border-radius:50%;display:grid;place-items:center;color:var(--pa-gold);font-size:21px}.pf-upload strong{color:var(--pa-text)}.pf-upload small{color:var(--pa-muted);font-size:9px}
.pf-image-preview{margin-top:12px;display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px}.pf-preview-item{position:relative;height:132px;padding:6px;overflow:hidden;border:1px solid var(--pa-line);border-radius:11px;background:var(--pa-bg);cursor:pointer}.pf-preview-item img{width:100%;height:92px;object-fit:contain}.pf-preview-item span{height:26px;display:grid;place-items:center;color:var(--pa-muted);font:inherit;font-size:8px}.pf-preview-item.selected{border-color:var(--pa-gold);box-shadow:inset 0 0 0 1px var(--pa-gold)}.pf-preview-item.selected span{color:var(--pa-gold)}.pf-preview-help{margin:8px 0 0;color:var(--pa-muted);font-size:8px}
.pf-switch-row{min-height:74px;padding:14px;border:1px solid var(--pa-line);border-radius:12px;display:grid;grid-template-columns:minmax(0,1fr) 48px;gap:14px;align-items:center;background:var(--pa-bg);cursor:pointer}.pf-switch-row>span{display:grid}.pf-switch-row strong{color:var(--pa-text)}.pf-switch-row small{margin-top:3px;color:var(--pa-muted);font-size:9px}.pf-switch-row input{position:absolute;opacity:0}.pf-switch-row>i{width:46px;height:24px;padding:3px;border:1px solid var(--pa-line-strong);border-radius:999px;background:var(--pa-panel-2);transition:.2s}.pf-switch-row>i:after{content:"";width:16px;height:16px;display:block;border-radius:50%;background:var(--pa-muted);transition:.2s}.pf-switch-row input:checked+i{background:rgba(201,163,106,.18)}.pf-switch-row input:checked+i:after{transform:translateX(-20px);background:var(--pa-gold-soft)}
.pf-variants{margin-top:15px;padding:16px;border:1px solid var(--pa-line);border-radius:14px;background:var(--pa-bg)}.pf-variants[hidden]{display:none!important}.pf-variant-head{margin-bottom:11px;display:flex;align-items:center;justify-content:space-between;gap:14px}.pf-variant-head h3{margin:4px 0 0!important;color:var(--pa-text)!important}.pf-variant-list{display:grid;gap:8px}
.pf-variant-row{padding:11px;border:1px solid var(--pa-line);border-radius:11px;display:grid;grid-template-columns:34px repeat(5,minmax(110px,1fr)) 76px 38px;gap:8px;align-items:end;background:var(--pa-panel)}.pf-variant-number{height:42px;display:grid;place-items:center;color:var(--pa-gold);font-size:9px;font-family:Georgia,serif!important}.pf-default-variant{min-height:42px;border:1px solid var(--pa-line);border-radius:9px;display:flex;align-items:center;justify-content:center;gap:6px;color:var(--pa-muted);font-size:8px}.pf-default-variant input{accent-color:var(--pa-gold-2)}.pf-remove-variant{width:38px;height:42px;border:1px solid var(--pa-line);border-radius:9px;display:grid;place-items:center;color:#b9786d;background:transparent;cursor:pointer}
.pf-status-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}.pf-status-option{min-height:92px;padding:13px;border:1px solid var(--pa-line);border-radius:12px;display:grid;grid-template-columns:38px 1fr;gap:10px;align-items:center;background:var(--pa-bg);cursor:pointer}.pf-status-option input{position:absolute;opacity:0}.pf-status-option>span{width:38px;height:38px;border:1px solid var(--pa-line);border-radius:50%;display:grid;place-items:center;color:var(--pa-muted)}.pf-status-option>div{display:grid}.pf-status-option strong{color:var(--pa-text);font-size:10px}.pf-status-option small{margin-top:3px;color:var(--pa-muted);font-size:8px}.pf-status-option:has(input:checked){border-color:var(--pa-line-strong);background:rgba(201,163,106,.06)}.pf-status-option:has(input:checked)>span{color:var(--pa-gold);border-color:var(--pa-line-strong)}
.pf-editor-actions{position:sticky;bottom:12px;z-index:15;padding:11px;border:1px solid var(--pa-line-strong);border-radius:14px;display:flex;justify-content:flex-end;gap:9px;background:color-mix(in srgb,var(--pa-panel) 94%,transparent);backdrop-filter:blur(16px)}.pf-submit{min-height:48px;padding:0 22px;border:0;border-radius:10px;display:inline-flex;align-items:center;gap:10px;background:linear-gradient(120deg,var(--pa-gold-soft),var(--pa-gold-2));color:#171009;font:inherit;font-weight:800;cursor:pointer}.pf-cancel{min-height:48px}

@media(max-width:1180px){.pf-variant-row{grid-template-columns:34px repeat(3,minmax(120px,1fr))}.pf-status-grid{grid-template-columns:1fr 1fr}}
@media(max-width:840px){.pa-account-copy{display:none}.pa-account-trigger{min-width:auto;grid-template-columns:38px 12px}.pf-grid.two,.pf-grid.three{grid-template-columns:1fr}.pf-field.wide{grid-column:auto}.pf-image-preview{grid-template-columns:repeat(3,minmax(0,1fr))}.pf-variant-row{grid-template-columns:34px 1fr 1fr}}
@media(max-width:620px){.pf-editor-hero{min-height:auto;padding:23px 18px;align-items:flex-start;flex-direction:column}.pf-card{padding:18px}.pf-card-title{grid-template-columns:38px 1fr}.pf-card-title>i{display:none}.pf-image-preview{grid-template-columns:1fr 1fr}.pf-status-grid{grid-template-columns:1fr}.pf-variant-row{grid-template-columns:30px 1fr}.pf-variant-row>*{grid-column:2}.pf-variant-number{grid-column:1;grid-row:1}.pf-editor-actions{align-items:stretch;flex-direction:column-reverse}.pf-submit,.pf-cancel{width:100%;justify-content:center}}
'''

JS_TEXT = r'''
(() => {
  "use strict";
  document.addEventListener("click", (event) => {
    document.querySelectorAll("details[data-pa-account][open]").forEach((menu) => {
      if (!menu.contains(event.target)) menu.removeAttribute("open");
    });
  });
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    document.querySelectorAll("details[data-pa-account][open]").forEach((menu) => {
      menu.removeAttribute("open");
    });
  });
})();
'''

COLOR_MAP = {
    "#ec4899":"#b48852", "#db2777":"#95652f", "#be185d":"#805127",
    "#9d174d":"#704520", "#f472b6":"#caa46c", "#f9a8d4":"#ddc095",
    "#e91e63":"#9b6734", "#c2185b":"#87552c", "#ad1457":"#744622",
    "#880e4f":"#5f381d", "#ff4081":"#bb8851", "#f06292":"#c69b6b",
    "#d946ef":"#9a7650", "#a855f7":"#8a6846", "#9333ea":"#75583a",
    "#8b5cf6":"#8d765a", "#7c3aed":"#6c5339", "#3b82f6":"#7b6a54",
    "#2563eb":"#685945", "#06b6d4":"#6f7c73", "#0891b2":"#606f69",
    "#10b981":"#778063", "#22c55e":"#6f775b", "#16a34a":"#636c52",
    "#f59e0b":"#c18c47", "#f97316":"#a76d43", "#ef4444":"#9a5c4f",
    "#e11d48":"#875044", "#fb7185":"#b97c6c",
}

def replace_colors(text):
    count = 0
    for old, new in COLOR_MAP.items():
        text, n = re.subn(re.escape(old), new, text, flags=re.I)
        count += n
    return text, count

def patch_admin_base():
    text = ADMIN_BASE.read_text(encoding="utf-8")
    original = text

    text = re.sub(
        r'<a\b[^>]*href=["\']\{%\s*url\s+["\']first:admin_dashboard["\']\s*%\}["\'][^>]*>.*?</a>',
        "",
        text,
        flags=re.I | re.S,
    )

    css_link = '<link rel="stylesheet" href="{% static \'css/perfume-admin-v2.css\' %}">'
    if "perfume-admin-v2.css" not in text:
        needle = '<link rel="stylesheet" href="{% static \'css/perfume-admin-v1.css\' %}">'
        if needle in text:
            text = text.replace(needle, needle + "\n  " + css_link, 1)
        else:
            text = text.replace("</head>", "  " + css_link + "\n</head>", 1)

    if "data-pa-account" not in text:
        marker = '<div class="pa-topbar-actions">'
        if marker not in text:
            raise RuntimeError("Could not locate pa-topbar-actions in admin base.")
        text = text.replace(marker, marker + "\n" + textwrap.dedent(OWNER_MENU).strip(), 1)

    js_link = '<script src="{% static \'js/perfume-admin-v2.js\' %}"></script>'
    if "perfume-admin-v2.js" not in text:
        text = text.replace("</body>", "  " + js_link + "\n</body>", 1)

    if text != original:
        backup(ADMIN_BASE)
        ADMIN_BASE.write_text(text, encoding="utf-8")
        print("[PATCH] admin base")

def patch_management_templates():
    root = ROOT / "first/templates"
    changed = 0
    replacements = {
        "LUXURY BEAUTY STORE":"MAISON DE PARFUM",
        "محصولات آرایشی":"عطرها و ادکلن‌ها",
        "فروشگاه آرایشی":"فروشگاه عطر",
        "آرایشی شاپ":"فروشگاه عطر",
    }
    class_replacements = {
        "text-pink-500":"text-amber-700",
        "text-pink-600":"text-amber-700",
        "text-pink-700":"text-amber-800",
        "bg-pink-50":"bg-stone-50",
        "bg-pink-100":"bg-amber-50",
        "bg-pink-500":"bg-amber-700",
        "bg-pink-600":"bg-amber-800",
        "border-pink-100":"border-stone-200",
        "border-pink-200":"border-amber-200",
        "border-pink-500":"border-amber-700",
        "focus:border-pink-500":"focus:border-amber-700",
        "focus:ring-pink-100":"focus:ring-amber-100",
        "from-pink-500":"from-amber-700",
        "to-purple-600":"to-stone-800",
    }

    for path in root.rglob("*.html"):
        rel = path.relative_to(root).as_posix()
        content = path.read_text(encoding="utf-8", errors="ignore")
        if not (
            rel.startswith("dashboard/")
            or "analytics" in rel.lower()
            or "pdf" in rel.lower()
            or "گزارش جامع مدیریتی" in content
            or "پیش نمایش گزارش کامل مدیریتی" in content
        ):
            continue

        original = content
        for old, new in replacements.items():
            content = content.replace(old, new)
        content, _ = replace_colors(content)
        for old, new in class_replacements.items():
            content = content.replace(old, new)

        if content != original:
            backup(path)
            path.write_text(content, encoding="utf-8")
            changed += 1

    print("[PATCH] management templates recolored:", changed)

def patch_pdf_palette_literals():
    if not ANALYTICS_VIEWS.exists():
        print("[INFO] analytics_views.py not found")
        return
    text = ANALYTICS_VIEWS.read_text(encoding="utf-8", errors="ignore")
    new, count = replace_colors(text)
    if not count:
        print("[INFO] no old PDF palette literals found")
        return
    backup(ANALYTICS_VIEWS)
    compile(new, str(ANALYTICS_VIEWS), "exec")
    ANALYTICS_VIEWS.write_text(new, encoding="utf-8")
    print("[PATCH] PDF/report palette literals:", count)

def main():
    print("=" * 86)
    print(" PHASE 11 — PERFUME ADMIN POLISH")
    print("=" * 86)

    for p in [ROOT / "manage.py", ADMIN_BASE, ADD_PRODUCT]:
        if not p.exists():
            raise SystemExit(f"Missing required file: {p}")

    if BACKUP.exists():
        raise SystemExit(
            f"Backup already exists: {BACKUP}\n"
            "Rename/delete it only if you intentionally rerun Phase 11."
        )

    names = route_names()
    needed = {"owner_panel","profile","customizer","home","logout","admin_products"}
    missing = needed - names
    if missing:
        raise SystemExit("Required routes missing: " + ", ".join(sorted(missing)))

    BACKUP.mkdir(parents=True)

    protected = {
        rel:(ROOT / rel).read_bytes()
        for rel in PROTECTED
        if (ROOT / rel).exists()
    }

    write(ADMIN_CSS, CSS_TEXT)
    write(ADMIN_JS, JS_TEXT)
    write(ADD_PRODUCT, ADD_PRODUCT_TEMPLATE)
    patch_admin_base()
    patch_management_templates()
    patch_pdf_palette_literals()

    for rel, before in protected.items():
        if (ROOT / rel).read_bytes() != before:
            raise RuntimeError("Unexpected backend change: " + rel)

    run(sys.executable, "manage.py", "check")
    run(sys.executable, "manage.py", "makemigrations", "--check", "--dry-run")
    run(
        sys.executable,
        "manage.py",
        "shell",
        "-c",
        (
            "from django.template.loader import get_template; "
            "[get_template(x) for x in ["
            "'dashboard/perfume_admin_base.html',"
            "'dashboard/admin_add_product.html'"
            "]]; print('ADMIN TEMPLATES OK')"
        ),
    )

    print("\n" + "=" * 86)
    print(" PHASE 11 READY")
    print("=" * 86)
    print("✓ pink/rainbow management palette removed")
    print("✓ duplicate management-dashboard navigation entry removed")
    print("✓ owner-name dropdown added")
    print("✓ owner panel / profile / visual design / store / logout inside dropdown")
    print("✓ logout remains POST + CSRF")
    print("✓ add-product rebuilt specifically for perfume")
    print("✓ bottle volume / edition / fragrance family terminology")
    print("✓ analytics/report palette recolored")
    print("✓ known PDF palette literals recolored when present")
    print("✓ models / urls / commerce logic untouched")
    print()
    print("Restart server, then Ctrl+F5.")

if __name__ == "__main__":
    main()
