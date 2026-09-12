#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / ".perfume_frontend_phase10_backup"
DECORATORS = ROOT / "first/decorators.py"
FILTERS = ROOT / "first/templatetags/custom_filters.py"
TEMPLATE = ROOT / "first/templates/edit_profile.html"
BASE = ROOT / "first/templates/perfume_base.html"
CSS = ROOT / "static/css/perfume-phase10.css"

def run(*args):
    print("\n> " + " ".join(map(str,args)))
    p = subprocess.run(list(args), cwd=ROOT, text=True)
    if p.returncode:
        raise RuntimeError("Command failed")

def backup(path):
    if not path.exists(): return
    dst = BACKUP / path.relative_to(ROOT)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists(): shutil.copy2(path,dst)

def write(path, text):
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")
    print("[WRITE]", path.relative_to(ROOT))

OWNER_POLICY = r"""
# ============================================================
# PERFUME OWNER SUPERUSER POLICY V3
# ============================================================
from functools import wraps as _p10_wraps
from django.contrib import messages as _p10_messages
from django.shortcuts import redirect as _p10_redirect

_p10_old_admin_required = globals().get("admin_required")
_p10_old_permission_required = globals().get("permission_required")
_p10_old_check = globals().get("check_admin_permission")
_p10_old_get_permissions = globals().get("get_effective_admin_permissions")

def _p10_is_owner(user):
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and (
            getattr(user, "is_superuser", False)
            or getattr(user, "is_owner", False)
        )
    )

def admin_required(view_func):
    old_wrapped = (
        _p10_old_admin_required(view_func)
        if callable(_p10_old_admin_required)
        else None
    )
    @_p10_wraps(view_func)
    def wrapper(request,*args,**kwargs):
        if not request.user.is_authenticated:
            _p10_messages.error(request,"❌ لطفاً ابتدا وارد شوید")
            return _p10_redirect("first:login")
        if _p10_is_owner(request.user):
            return view_func(request,*args,**kwargs)
        if old_wrapped:
            return old_wrapped(request,*args,**kwargs)
        _p10_messages.error(request,"⛔ شما دسترسی ادمین ندارید")
        return _p10_redirect("first:home")
    return wrapper

def owner_required(view_func):
    @_p10_wraps(view_func)
    def wrapper(request,*args,**kwargs):
        if not request.user.is_authenticated:
            _p10_messages.error(request,"❌ لطفاً ابتدا وارد شوید")
            return _p10_redirect("first:login")
        if not _p10_is_owner(request.user):
            _p10_messages.error(request,"⛔ فقط مالک سایت به این بخش دسترسی دارد")
            return _p10_redirect("first:home")
        return view_func(request,*args,**kwargs)
    return wrapper

def check_admin_permission(user, permission_name):
    if _p10_is_owner(user):
        return True
    if callable(_p10_old_check):
        return bool(_p10_old_check(user, permission_name))
    return False

def get_effective_admin_permissions(user):
    if _p10_is_owner(user):
        model = globals().get("AdminPermission")
        if model is not None:
            try:
                return list(
                    model.objects.filter(is_active=True)
                    .values_list("name",flat=True)
                )
            except Exception:
                pass
        return []
    if callable(_p10_old_get_permissions):
        return _p10_old_get_permissions(user)
    return []

def permission_required(permission_name, redirect_url="first:home"):
    old_decorator = (
        _p10_old_permission_required(permission_name, redirect_url)
        if callable(_p10_old_permission_required)
        else None
    )
    def decorator(view_func):
        old_wrapped = old_decorator(view_func) if old_decorator else None
        @_p10_wraps(view_func)
        def wrapper(request,*args,**kwargs):
            if not request.user.is_authenticated:
                _p10_messages.error(request,"❌ لطفاً ابتدا وارد شوید")
                return _p10_redirect("first:login")
            if _p10_is_owner(request.user):
                return view_func(request,*args,**kwargs)
            if old_wrapped:
                return old_wrapped(request,*args,**kwargs)
            if not check_admin_permission(request.user, permission_name):
                _p10_messages.error(request,"⛔ شما دسترسی لازم برای این بخش را ندارید")
                return _p10_redirect(redirect_url)
            return view_func(request,*args,**kwargs)
        return wrapper
    return decorator
"""

FILTER_POLICY = r"""
# ============================================================
# PERFUME OWNER TEMPLATE PERMISSION POLICY V3
# ============================================================
_p10_old_has_permission = globals().get("has_permission")
_p10_old_get_user_permissions = globals().get("get_user_permissions")

@register.filter(name="has_permission")
def has_permission(user, permission_name):
    if (
        user
        and getattr(user,"is_authenticated",False)
        and (
            getattr(user,"is_superuser",False)
            or getattr(user,"is_owner",False)
        )
    ):
        return True
    if callable(_p10_old_has_permission):
        return _p10_old_has_permission(user,permission_name)
    try:
        from ..decorators import check_admin_permission
        return check_admin_permission(user,permission_name)
    except Exception:
        return False

@register.filter(name="get_user_permissions")
def get_user_permissions(user):
    if (
        user
        and getattr(user,"is_authenticated",False)
        and (
            getattr(user,"is_superuser",False)
            or getattr(user,"is_owner",False)
        )
    ):
        try:
            from ..decorators import get_effective_admin_permissions
            return get_effective_admin_permissions(user)
        except Exception:
            return []
    if callable(_p10_old_get_user_permissions):
        return _p10_old_get_user_permissions(user)
    return []
"""

EDIT_TEMPLATE = r"""
{% extends 'perfume_base.html' %}
{% block title %}ویرایش پروفایل | {{ settings.site_name|default:'فروشگاه عطر' }}{% endblock %}
{% block content %}
<section class="p10-page">
  <div class="p10-shell">
    <header class="p10-hero">
      <div>
        <span>PRIVATE ACCOUNT</span>
        <h1>ویرایش پروفایل</h1>
        <p>اطلاعات حساب و مشخصات تماس خود را به‌روزرسانی کنید.</p>
      </div>
      <div class="p10-seal"><i class="fa-regular fa-user"></i><small>PROFILE</small></div>
    </header>

    <div class="p10-grid">
      <aside class="p10-side">
        <div class="p10-avatar">
          {% if user.profile_image %}
            <img src="{{ user.profile_image.url }}" alt="{{ user.username }}">
          {% else %}
            <span>{{ user.username|first|upper }}</span>
          {% endif %}
        </div>
        <span class="p10-kicker">{% if user.is_superuser %}STORE OWNER{% else %}MEMBER{% endif %}</span>
        <h2>{{ user.username }}</h2>
        <p>{{ user.email|default:'ایمیل ثبت نشده' }}</p>

        <div class="p10-badges">
          {% if user.is_superuser %}
          <span><i class="fa-solid fa-crown"></i> مالک فروشگاه</span>
          {% endif %}
          <span><i class="fa-solid fa-shield-halved"></i> اطلاعات خصوصی</span>
          <span><i class="fa-solid fa-lock"></i> حساب امن</span>
        </div>

        <a class="p10-outline full" href="{% url 'first:profile' %}">
          بازگشت به پروفایل
        </a>
      </aside>

      <section class="p10-card">
        <div class="p10-card-head">
          <div><span class="p10-kicker">PERSONAL DETAILS</span><h2>اطلاعات شخصی</h2></div>
          <i class="fa-solid fa-pen-to-square"></i>
        </div>

        <form method="post" enctype="multipart/form-data" class="p10-form">
          {% csrf_token %}
          {% if form.non_field_errors %}
          <div class="p10-errors">{{ form.non_field_errors }}</div>
          {% endif %}

          <div class="p10-fields">
            {% for field in form %}
            <div class="p10-field {% if field.name == 'profile_image' %}wide{% endif %}">
              <label for="{{ field.id_for_label }}">
                {{ field.label }} {% if field.field.required %}<b>*</b>{% endif %}
              </label>
              <div class="p10-control">{{ field }}</div>
              {% if field.help_text %}<small>{{ field.help_text|safe }}</small>{% endif %}
              {% if field.errors %}<div class="p10-errors">{{ field.errors }}</div>{% endif %}
            </div>
            {% endfor %}
          </div>

          <div class="p10-actions">
            <a class="p10-outline" href="{% url 'first:profile' %}">انصراف</a>
            <button class="p10-save" type="submit">
              ذخیره تغییرات <i class="fa-solid fa-arrow-left"></i>
            </button>
          </div>
        </form>
      </section>
    </div>
  </div>
</section>
{% endblock %}
"""

CSS_TEXT = r"""
.p10-page{padding:46px 0 92px;background:radial-gradient(circle at 82% 5%,rgba(171,103,42,.1),transparent 24%),var(--p-bg)}
.p10-shell{width:min(1280px,calc(100% - 48px));margin:auto}
.p10-hero{min-height:220px;margin-bottom:18px;padding:40px 44px;border:1px solid var(--p-line);display:flex;align-items:flex-end;justify-content:space-between;gap:30px;background:radial-gradient(circle at 85% 22%,rgba(192,131,63,.15),transparent 24%),linear-gradient(125deg,var(--p-surface),var(--p-surface-2))}
.p10-hero>div:first-child>span,.p10-kicker{color:var(--p-gold);font-size:9px;font-weight:700;letter-spacing:.2em}
.p10-hero h1{margin:9px 0 10px!important;font-size:clamp(44px,5vw,70px)!important;line-height:1!important}
.p10-hero p{margin:0;color:var(--p-muted)!important}
.p10-seal{width:110px;height:110px;flex:none;border:1px solid var(--p-line-strong);border-radius:50%;display:grid;place-items:center;align-content:center;gap:6px;color:var(--p-gold);background:var(--p-bg)}
.p10-seal i{font-size:30px}.p10-seal small{font-size:8px;letter-spacing:.18em}
.p10-grid{display:grid;grid-template-columns:320px minmax(0,1fr);gap:18px;align-items:start}
.p10-side,.p10-card{border:1px solid var(--p-line);background:linear-gradient(145deg,var(--p-surface),var(--p-surface-2))}
.p10-side{padding:32px 24px;text-align:center}.p10-card{padding:34px;box-shadow:var(--p-shadow)}
.p10-avatar{width:124px;height:124px;margin:0 auto 20px;border:1px solid var(--p-line-strong);border-radius:50%;overflow:hidden;display:grid;place-items:center;background:var(--p-bg);color:var(--p-gold);font-size:43px;font-family:Georgia,serif!important}
.p10-avatar img{width:100%;height:100%;object-fit:cover}
.p10-side h2{margin:8px 0 4px!important;font-size:27px!important}.p10-side>p{margin:0;color:var(--p-muted)!important;overflow-wrap:anywhere}
.p10-badges{display:grid;gap:8px;margin:24px 0}.p10-badges span{min-height:42px;padding:0 12px;border:1px solid var(--p-line);display:flex;align-items:center;gap:10px;color:var(--p-muted);font-size:11px}.p10-badges i{width:22px;color:var(--p-gold)}
.p10-card-head{padding-bottom:23px;margin-bottom:25px;border-bottom:1px solid var(--p-line);display:flex;align-items:center;justify-content:space-between}.p10-card-head h2{margin:7px 0 0!important;font-size:32px!important}.p10-card-head>i{width:54px;height:54px;border:1px solid var(--p-line-strong);border-radius:50%;display:grid;place-items:center;color:var(--p-gold)}
.p10-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px 16px}.p10-field{min-width:0;display:grid;gap:8px;align-content:start}.p10-field.wide{grid-column:1/-1}.p10-field label{color:var(--p-muted)!important;font-size:11px;font-weight:600}.p10-field label b{color:var(--p-gold)}.p10-field>small{color:var(--p-muted)!important;font-size:9px}
.p10-control input:not([type=checkbox]):not([type=radio]),.p10-control select,.p10-control textarea{width:100%!important;max-width:none!important;min-width:0!important;min-height:54px!important;margin:0!important;padding:0 15px!important;border:1px solid var(--p-line)!important;border-radius:0!important;background:var(--p-bg)!important;color:var(--p-text)!important;outline:none!important;box-shadow:none!important;font:inherit!important}
.p10-control textarea{min-height:130px!important;padding:14px 15px!important}.p10-control input:focus,.p10-control select:focus,.p10-control textarea:focus{border-color:var(--p-line-strong)!important;box-shadow:0 0 0 4px rgba(190,137,70,.07)!important}
.p10-control input[type=file]{width:100%!important;min-height:64px!important;padding:10px!important;border:1px dashed var(--p-line-strong)!important;background:var(--p-bg)!important;color:var(--p-muted)!important}.p10-control input[type=file]::file-selector-button{min-height:40px;margin-left:12px;padding:0 16px;border:0;background:linear-gradient(120deg,var(--p-gold-pale),var(--p-gold-deep));color:#171008;font:inherit}
.p10-errors ul{margin:0!important;padding:9px 12px!important;list-style:none!important;border:1px solid rgba(190,80,70,.3);color:#df8e85!important;font-size:10px}
.p10-actions{margin-top:30px;padding-top:24px;border-top:1px solid var(--p-line);display:flex;justify-content:flex-end;gap:10px}.p10-save,.p10-outline{min-height:50px;padding:0 19px;display:inline-flex;align-items:center;justify-content:center;gap:10px;font:inherit}.p10-save{border:0;background:linear-gradient(120deg,var(--p-gold-pale),var(--p-gold-deep));color:#171008;font-weight:700}.p10-outline{border:1px solid var(--p-line-strong);background:transparent;color:var(--p-text)!important}.full{width:100%}
html[data-perfume-theme=day] .p10-page{background:#e8d9c8!important}html[data-perfume-theme=day] .p10-hero,html[data-perfume-theme=day] .p10-side,html[data-perfume-theme=day] .p10-card{background:linear-gradient(145deg,#fffdf9,#f1e3d2)!important}html[data-perfume-theme=day] .p10-control input:not([type=checkbox]):not([type=radio]),html[data-perfume-theme=day] .p10-control select,html[data-perfume-theme=day] .p10-control textarea,html[data-perfume-theme=day] .p10-avatar{background:#f8eee2!important;color:#18120e!important}
html[data-perfume-theme=night] .p10-hero,html[data-perfume-theme=night] .p10-side,html[data-perfume-theme=night] .p10-card{background:linear-gradient(145deg,#17110d,#21160f)!important}html[data-perfume-theme=night] .p10-control input:not([type=checkbox]):not([type=radio]),html[data-perfume-theme=night] .p10-control select,html[data-perfume-theme=night] .p10-control textarea,html[data-perfume-theme=night] .p10-avatar{background:#0f0b09!important;color:#f7f0e7!important}
@media(max-width:900px){.p10-grid{grid-template-columns:1fr}.p10-side{text-align:right}.p10-avatar{margin-right:0;margin-left:0}}
@media(max-width:680px){.p10-page{padding:24px 0 58px}.p10-shell{width:calc(100% - 24px)}.p10-hero{min-height:auto;padding:28px 21px}.p10-seal{display:none}.p10-card{padding:24px 18px}.p10-fields{grid-template-columns:1fr}.p10-field.wide{grid-column:auto}.p10-actions{flex-direction:column-reverse}.p10-save,.p10-outline{width:100%}}
"""

def append_policy(path, marker, policy):
    text = path.read_text(encoding="utf-8")
    if marker in text:
        print("[SKIP]", marker)
        return
    backup(path)
    text = text.rstrip() + "\n\n" + textwrap.dedent(policy).strip() + "\n"
    ast.parse(text)
    path.write_text(text,encoding="utf-8")
    print("[PATCH]", path.relative_to(ROOT))

def patch_base():
    text = BASE.read_text(encoding="utf-8")
    if "perfume-phase10.css" in text: return
    backup(BASE)
    link = '<link rel="stylesheet" href="{% static \'css/perfume-phase10.css\' %}">'
    if "{% block extra_css %}" in text:
        text = text.replace("{% block extra_css %}", link+"\n{% block extra_css %}",1)
    else:
        text = text.replace("</head>",link+"\n</head>",1)
    BASE.write_text(text,encoding="utf-8")
    print("[PATCH] base CSS")

def main():
    print("="*80)
    print("PHASE 10 — OWNER FULL ACCESS + EDIT PROFILE")
    print("="*80)
    for p in [ROOT/"manage.py",DECORATORS,TEMPLATE,BASE]:
        if not p.exists(): raise SystemExit(f"Missing: {p}")
    if BACKUP.exists(): raise SystemExit(f"Backup exists: {BACKUP}")
    BACKUP.mkdir(parents=True)

    protected = {}
    for rel in ["first/models.py","first/views.py","first/urls.py","first/forms.py"]:
        p=ROOT/rel
        if p.exists(): protected[rel]=p.read_bytes()

    append_policy(DECORATORS,"PERFUME OWNER SUPERUSER POLICY V3",OWNER_POLICY)
    if FILTERS.exists():
        append_policy(FILTERS,"PERFUME OWNER TEMPLATE PERMISSION POLICY V3",FILTER_POLICY)

    write(TEMPLATE,EDIT_TEMPLATE)
    write(CSS,CSS_TEXT)
    patch_base()

    for rel,before in protected.items():
        if (ROOT/rel).read_bytes()!=before:
            raise RuntimeError("Unexpected change: "+rel)

    run(sys.executable,"manage.py","check")
    run(sys.executable,"manage.py","makemigrations","--check","--dry-run")
    run(
        sys.executable,"manage.py","shell","-c",
        "from first.models import User; "
        "from first.decorators import check_admin_permission; "
        "u=User.objects.filter(is_superuser=True).first(); "
        "assert u is not None; "
        "print({'username':u.username,'role':u.role,'is_superuser':u.is_superuser}); "
        "assert check_admin_permission(u,'__probe__') is True; "
        "print('OWNER FULL ACCESS PROBE: OK')"
    )
    run(
        sys.executable,"manage.py","shell","-c",
        "from django.template.loader import get_template; "
        "get_template('edit_profile.html'); print('EDIT PROFILE TEMPLATE: OK')"
    )

    print("\n"+"="*80)
    print("PHASE 10 READY")
    print("="*80)
    print("Owner/superuser full admin bypass: ON")
    print("Database role/phone changed: NO")
    print("Edit profile redesigned: YES")
    print("IMPORTANT: restart runserver, then Ctrl+F5")

if __name__=="__main__":
    main()
