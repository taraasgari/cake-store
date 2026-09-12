#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations
import ast
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / ".perfume_frontend_phase07_backup"

FORMS = ROOT / "first/forms.py"
VIEWS = ROOT / "first/views.py"
DECORATORS = ROOT / "first/decorators.py"
LOGIN_TEMPLATE = ROOT / "first/templates/login.html"
BASE = ROOT / "first/templates/perfume_base.html"
JS = ROOT / "static/js/perfume-phase07.js"
CSS = ROOT / "static/css/perfume-phase07.css"

REQUIRED = [FORMS, VIEWS, DECORATORS, LOGIN_TEMPLATE, BASE]


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


def replace_top_level_function(path: Path, function_name: str, replacement: str):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    target = None

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            target = node
            break

    if target is None:
        raise RuntimeError(f"{function_name} not found in {path.relative_to(ROOT)}")

    lines = source.splitlines(keepends=True)
    start = target.lineno - 1
    end = target.end_lineno

    new_source = (
        "".join(lines[:start])
        + textwrap.dedent(replacement).strip()
        + "\n\n"
        + "".join(lines[end:]).lstrip("\n")
    )

    backup(path)
    path.write_text(new_source, encoding="utf-8")
    print("[PATCH]", path.relative_to(ROOT), "->", function_name)


def replace_method_in_class(
    path: Path,
    class_name: str,
    method_name: str,
    replacement: str,
):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    target_class = None
    target_method = None

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            target_class = node
            break

    if target_class is None:
        raise RuntimeError(f"class {class_name} not found in {path.relative_to(ROOT)}")

    for node in target_class.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == method_name:
            target_method = node
            break

    if target_method is None:
        raise RuntimeError(
            f"{class_name}.{method_name} not found in {path.relative_to(ROOT)}"
        )

    lines = source.splitlines(keepends=True)
    start = target_method.lineno - 1
    end = target_method.end_lineno

    normalized = textwrap.dedent(replacement).strip("\n")
    indented = textwrap.indent(normalized, "    ")

    new_source = (
        "".join(lines[:start])
        + indented
        + "\n\n"
        + "".join(lines[end:]).lstrip("\n")
    )

    backup(path)
    path.write_text(new_source, encoding="utf-8")
    print("[PATCH]", path.relative_to(ROOT), f"-> {class_name}.{method_name}")


LOGIN_CLEAN_PHONE = r'''
def clean_phone(self):
    # Normal users keep phone login.
    # Superuser/owner can submit username or email; the view restricts
    # that fallback to active superusers only.
    identifier = (self.cleaned_data.get('phone') or '').strip()

    if not identifier:
        raise ValidationError(
            'شماره تلفن یا نام کاربری مالک را وارد کنید'
        )

    translation = str.maketrans(
        '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩',
        '01234567890123456789',
    )

    normalized = identifier.translate(translation)
    normalized = re.sub(r'[\s\-()]', '', normalized)

    if normalized.startswith('+98'):
        normalized = '0' + normalized[3:]
    elif normalized.startswith('0098'):
        normalized = '0' + normalized[4:]
    elif normalized.startswith('98') and len(normalized) == 12:
        normalized = '0' + normalized[2:]

    if re.fullmatch(r'09\d{9}', normalized):
        return normalized

    if (
        len(identifier) <= 254
        and re.fullmatch(r'[A-Za-z0-9_.@+\-]+', identifier)
    ):
        return identifier

    raise ValidationError(
        'شماره تلفن معتبر یا نام کاربری/ایمیل مالک را وارد کنید'
    )
'''


LOGIN_VIEW = r'''
def login_view(request):
    from django.core.cache import cache
    from django.db.models import Q
    from django.utils.http import url_has_allowed_host_and_scheme
    import hashlib

    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('first:owner_panel')
        return redirect('first:home')

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            identifier = form.cleaned_data['phone']
            password = form.cleaned_data['password']

            remote_addr = request.META.get(
                'REMOTE_ADDR',
                'unknown',
            )

            raw_key = (
                f'{settings.SECRET_KEY}:'
                f'{remote_addr}:'
                f'{identifier}'
            )

            throttle_key = (
                'perfume-login:'
                + hashlib.sha256(
                    raw_key.encode('utf-8')
                ).hexdigest()
            )

            attempts = int(
                cache.get(throttle_key, 0)
                or 0
            )

            if attempts >= 8:
                messages.error(
                    request,
                    (
                        'تعداد تلاش‌های ورود بیش از حد مجاز است. '
                        '۱۵ دقیقه بعد دوباره تلاش کنید.'
                    ),
                )

                return render(
                    request,
                    'login.html',
                    {'form': form},
                    status=429,
                )

            user_obj = (
                User.objects
                .filter(
                    phone=identifier,
                    is_active=True,
                )
                .first()
            )

            if user_obj is None:
                user_obj = (
                    User.objects
                    .filter(
                        Q(username__iexact=identifier)
                        | Q(email__iexact=identifier),
                        is_active=True,
                        is_superuser=True,
                    )
                    .first()
                )

            user = None

            if user_obj is not None:
                user = authenticate(
                    request,
                    username=user_obj.username,
                    password=password,
                )

            if user is not None:
                cache.delete(throttle_key)
                login(request, user)

                messages.success(
                    request,
                    '✨ خوش آمدید!',
                )

                next_page = request.GET.get('next')

                if (
                    next_page
                    and url_has_allowed_host_and_scheme(
                        url=next_page,
                        allowed_hosts={request.get_host()},
                        require_https=request.is_secure(),
                    )
                ):
                    return redirect(next_page)

                if user.is_superuser:
                    return redirect('first:owner_panel')

                return redirect('first:home')

            cache.set(
                throttle_key,
                attempts + 1,
                timeout=900,
            )

            messages.error(
                request,
                '❌ اطلاعات ورود یا رمز عبور اشتباه است',
            )
    else:
        form = LoginForm()

    return render(
        request,
        'login.html',
        {'form': form},
    )
'''


ADMIN_REQUIRED = r'''
def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(
                request,
                "❌ لطفاً ابتدا وارد شوید",
            )
            return redirect('first:login')

        if not (
            request.user.is_admin
            or request.user.is_superuser
        ):
            messages.error(
                request,
                "⛔ شما دسترسی ادمین ندارید",
            )
            return redirect('first:home')

        return view_func(
            request,
            *args,
            **kwargs,
        )

    return wrapper
'''


OWNER_REQUIRED = r'''
def owner_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(
                request,
                "❌ لطفاً ابتدا وارد شوید",
            )
            return redirect('first:login')

        if not (
            request.user.is_owner
            or request.user.is_superuser
        ):
            messages.error(
                request,
                (
                    "⛔ فقط مالک سایت به این بخش "
                    "دسترسی دارد"
                ),
            )
            return redirect('first:home')

        return view_func(
            request,
            *args,
            **kwargs,
        )

    return wrapper
'''


def patch_permission_helpers():
    text = DECORATORS.read_text(encoding="utf-8")
    original = text

    text = re.sub(
        r'(?m)^(\s*)if user\.is_owner:\s*$',
        r'\1if user.is_owner or user.is_superuser:',
        text,
    )

    if text != original:
        if not (BACKUP / DECORATORS.relative_to(ROOT)).exists():
            backup(DECORATORS)
        DECORATORS.write_text(text, encoding="utf-8")
        print("[PATCH] first/decorators.py -> superuser permission helpers")


def patch_login_template():
    text = LOGIN_TEMPLATE.read_text(encoding="utf-8")
    original = text

    text = text.replace(
        'for="id_phone">شماره تلفن</label>',
        'for="id_phone">شماره تلفن / نام کاربری مالک</label>',
    )
    text = text.replace(
        'placeholder="09123456789"',
        'placeholder="09123456789 یا owner"',
        1,
    )
    text = text.replace(
        'autocomplete="tel"',
        'autocomplete="username"',
        1,
    )

    if text != original:
        backup(LOGIN_TEMPLATE)
        LOGIN_TEMPLATE.write_text(text, encoding="utf-8")
        print("[PATCH] first/templates/login.html -> owner identifier hint")


JS_TEXT = r'''
(() => {
  "use strict";

  const ROOT = document.documentElement;
  const STORAGE_KEY = "velora-theme";

  function normalize(value) {
    return value === "day" || value === "night" ? value : null;
  }

  function readTheme() {
    try {
      return (
        normalize(localStorage.getItem(STORAGE_KEY)) ||
        normalize(localStorage.getItem("perfume-theme")) ||
        normalize(localStorage.getItem("theme")) ||
        normalize(ROOT.dataset.perfumeTheme) ||
        "night"
      );
    } catch (_) {
      return normalize(ROOT.dataset.perfumeTheme) || "night";
    }
  }

  function applyTheme(theme) {
    theme = normalize(theme) || "night";

    ROOT.dataset.perfumeTheme = theme;
    ROOT.style.colorScheme = theme === "day" ? "light" : "dark";

    if (document.body) {
      document.body.dataset.perfumeTheme = theme;
      document.body.classList.toggle("theme-day", theme === "day");
      document.body.classList.toggle("theme-night", theme === "night");
    }

    try {
      localStorage.setItem(STORAGE_KEY, theme);
      localStorage.setItem("perfume-theme", theme);
      localStorage.setItem("theme", theme);
    } catch (_) {}

    document.querySelectorAll("[data-theme-toggle]").forEach(btn => {
      btn.setAttribute(
        "aria-label",
        theme === "night" ? "فعال کردن حالت روز" : "فعال کردن حالت شب"
      );
      btn.setAttribute(
        "title",
        theme === "night" ? "حالت روز" : "حالت شب"
      );
    });
  }

  applyTheme(readTheme());

  document.addEventListener("DOMContentLoaded", () => {
    applyTheme(readTheme());
    setTimeout(() => applyTheme(readTheme()), 0);
  });

  window.addEventListener(
    "click",
    event => {
      const target = event.target;
      if (!(target instanceof Element)) return;

      const btn = target.closest("[data-theme-toggle]");
      if (!btn) return;

      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();

      const current = normalize(ROOT.dataset.perfumeTheme) || readTheme();
      applyTheme(current === "night" ? "day" : "night");
    },
    true
  );
})();
'''


CSS_TEXT = r'''
html[data-perfume-theme="day"] body,
html[data-perfume-theme="day"] .phase-main{
  color-scheme:light;
}

html[data-perfume-theme="night"] body,
html[data-perfume-theme="night"] .phase-main{
  color-scheme:dark;
}

[data-theme-toggle]{
  position:relative;
}

html[data-perfume-theme="day"] [data-theme-toggle]{
  color:var(--p-gold)!important;
  background:rgba(166,109,45,.07)!important;
  border-color:var(--p-line)!important;
}

html[data-perfume-theme="night"] [data-theme-toggle]{
  color:var(--p-gold-pale)!important;
}

.auth-lux-form input[name="phone"]{
  direction:ltr;
  text-align:left;
}
'''


def patch_base_assets():
    text = BASE.read_text(encoding="utf-8")
    original = text

    css_link = '<link rel="stylesheet" href="{% static \'css/perfume-phase07.css\' %}">'
    js_link = '<script src="{% static \'js/perfume-phase07.js\' %}"></script>'

    if "perfume-phase07.css" not in text:
        if "{% block extra_css %}" in text:
            text = text.replace(
                "{% block extra_css %}",
                css_link + "\n    {% block extra_css %}",
                1,
            )
        else:
            text = text.replace("</head>", "    " + css_link + "\n</head>", 1)

    if "perfume-phase07.js" not in text:
        if "</body>" not in text:
            raise RuntimeError("Could not find </body> in perfume_base.html")
        text = text.replace(
            "</body>",
            "    " + js_link + "\n</body>",
            1,
        )

    if text != original:
        backup(BASE)
        BASE.write_text(text, encoding="utf-8")
        print("[PATCH] first/templates/perfume_base.html -> Phase 07 assets")


def main():
    print("=" * 84)
    print(" PHASE 07 — OWNER LOGIN + DAY/NIGHT FIX")
    print("=" * 84)

    if not (ROOT / "manage.py").exists():
        raise SystemExit("Put this file beside manage.py.")

    missing = [p for p in REQUIRED if not p.exists()]
    if missing:
        raise SystemExit(
            "Missing required file(s):\n"
            + "\n".join(str(p.relative_to(ROOT)) for p in missing)
        )

    if BACKUP.exists():
        raise SystemExit(
            f"Backup already exists: {BACKUP}\n"
            "Rename/delete it only if you intentionally want to rerun Phase 07."
        )

    BACKUP.mkdir(parents=True)

    replace_method_in_class(
        FORMS,
        "LoginForm",
        "clean_phone",
        LOGIN_CLEAN_PHONE,
    )

    replace_top_level_function(
        VIEWS,
        "login_view",
        LOGIN_VIEW,
    )

    replace_top_level_function(
        DECORATORS,
        "admin_required",
        ADMIN_REQUIRED,
    )

    replace_top_level_function(
        DECORATORS,
        "owner_required",
        OWNER_REQUIRED,
    )

    patch_permission_helpers()
    patch_login_template()

    write(JS, JS_TEXT)
    write(CSS, CSS_TEXT)
    patch_base_assets()

    for path in [FORMS, VIEWS, DECORATORS]:
        ast.parse(path.read_text(encoding="utf-8"))
        print("[PYTHON OK]", path.relative_to(ROOT))

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

    print("\n[CHECK] Superuser account")
    run(
        sys.executable,
        "manage.py",
        "shell",
        "-c",
        (
            "from first.models import User; "
            "print(list(User.objects.filter(is_superuser=True)"
            ".values('id','username','email','phone','role','is_staff','is_superuser')))"
        ),
    )

    print("\n" + "=" * 84)
    print(" PHASE 07 READY")
    print("=" * 84)
    print("OWNER LOGIN:")
    print("  use: owner OR the owner's email")
    print("  password: existing owner password")
    print("  no phone/role/database edit required")
    print("  superuser receives owner/admin protected access")
    print("  successful owner login redirects to owner_panel")
    print("")
    print("THEME:")
    print("  conflicting old click handlers are blocked")
    print("  day/night state is persisted reliably")
    print("")
    print("Now run:")
    print("  python manage.py runserver")


if __name__ == "__main__":
    main()
