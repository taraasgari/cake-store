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
BACKUP = ROOT / ".perfume_frontend_phase07_v2_backup"

FORMS = ROOT / "first/forms.py"
VIEWS = ROOT / "first/views.py"
DECORATORS = ROOT / "first/decorators.py"
LOGIN_TEMPLATE = ROOT / "first/templates/login.html"
BASE = ROOT / "first/templates/perfume_base.html"

JS = ROOT / "static/js/perfume-phase07-v2.js"
CSS = ROOT / "static/css/perfume-phase07-v2.css"

REQUIRED = [
    ROOT / "manage.py",
    FORMS,
    VIEWS,
    DECORATORS,
    LOGIN_TEMPLATE,
    BASE,
]


def run(*args):
    print("\n> " + " ".join(map(str, args)))
    result = subprocess.run(list(args), cwd=ROOT, text=True)
    if result.returncode:
        raise RuntimeError("Command failed: " + " ".join(map(str, args)))


def backup(path: Path):
    if not path.exists():
        return
    target = BACKUP / path.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(path, target)


def write(path: Path, content: str):
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent(content).lstrip(),
        encoding="utf-8",
    )
    print("[WRITE]", path.relative_to(ROOT))


def find_top_function(source: str, name: str):
    tree = ast.parse(source)
    for node in tree.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == name
        ):
            return node
    return None


def replace_top_function(path: Path, name: str, replacement: str):
    source = path.read_text(encoding="utf-8")
    node = find_top_function(source, name)

    if node is None:
        raise RuntimeError(
            f"{name} not found in {path.relative_to(ROOT)}"
        )

    lines = source.splitlines(keepends=True)
    new_source = (
        "".join(lines[: node.lineno - 1])
        + textwrap.dedent(replacement).strip()
        + "\n\n"
        + "".join(lines[node.end_lineno:]).lstrip("\n")
    )

    backup(path)
    path.write_text(new_source, encoding="utf-8")
    print("[PATCH]", path.relative_to(ROOT), "->", name)


def find_class_method(source: str, class_name: str, method_name: str):
    tree = ast.parse(source)

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if (
                    isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and child.name == method_name
                ):
                    return child
    return None


def replace_class_method(
    path: Path,
    class_name: str,
    method_name: str,
    replacement: str,
):
    source = path.read_text(encoding="utf-8")
    node = find_class_method(source, class_name, method_name)

    if node is None:
        raise RuntimeError(
            f"{class_name}.{method_name} not found in "
            f"{path.relative_to(ROOT)}"
        )

    lines = source.splitlines(keepends=True)
    body = textwrap.indent(
        textwrap.dedent(replacement).strip(),
        "    ",
    )

    new_source = (
        "".join(lines[: node.lineno - 1])
        + body
        + "\n\n"
        + "".join(lines[node.end_lineno:]).lstrip("\n")
    )

    backup(path)
    path.write_text(new_source, encoding="utf-8")
    print(
        "[PATCH]",
        path.relative_to(ROOT),
        "->",
        f"{class_name}.{method_name}",
    )


LOGIN_CLEAN_PHONE = r'''
def clean_phone(self):
    identifier = (
        self.cleaned_data.get('phone')
        or ''
    ).strip()

    if not identifier:
        raise ValidationError(
            'شماره تلفن یا نام کاربری مالک را وارد کنید'
        )

    translation = str.maketrans(
        '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩',
        '01234567890123456789',
    )

    normalized = identifier.translate(
        translation
    )

    normalized = re.sub(
        r'[\s\-()]',
        '',
        normalized,
    )

    if normalized.startswith('+98'):
        normalized = '0' + normalized[3:]
    elif normalized.startswith('0098'):
        normalized = '0' + normalized[4:]
    elif (
        normalized.startswith('98')
        and len(normalized) == 12
    ):
        normalized = (
            '0'
            + normalized[2:]
        )

    if re.fullmatch(
        r'09\d{9}',
        normalized,
    ):
        return normalized

    if (
        len(identifier) <= 254
        and re.fullmatch(
            r'[A-Za-z0-9_.@+\-]+',
            identifier,
        )
    ):
        return identifier

    raise ValidationError(
        (
            'شماره تلفن معتبر یا '
            'نام کاربری/ایمیل مالک را وارد کنید'
        )
    )
'''


LOGIN_VIEW = r'''
def login_view(request):
    from django.core.cache import cache
    from django.db.models import Q
    from django.utils.http import (
        url_has_allowed_host_and_scheme,
    )
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
                        (
                            Q(username__iexact=identifier)
                            | Q(email__iexact=identifier)
                        ),
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


LOCAL_ACCESS_DECORATORS = r'''
# ==========================================================
# PERFUME SHOP LOCAL ACCESS POLICY
# ==========================================================

def admin_required(view_func):
    from functools import wraps
    from django.contrib import messages
    from django.shortcuts import redirect

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(
                request,
                '❌ لطفاً ابتدا وارد شوید',
            )
            return redirect('first:login')

        if not (
            getattr(request.user, 'is_admin', False)
            or request.user.is_superuser
        ):
            messages.error(
                request,
                '⛔ شما دسترسی ادمین ندارید',
            )
            return redirect('first:home')

        return view_func(request, *args, **kwargs)

    return wrapper


def owner_required(view_func):
    from functools import wraps
    from django.contrib import messages
    from django.shortcuts import redirect

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(
                request,
                '❌ لطفاً ابتدا وارد شوید',
            )
            return redirect('first:login')

        if not (
            getattr(request.user, 'is_owner', False)
            or request.user.is_superuser
        ):
            messages.error(
                request,
                '⛔ فقط مالک سایت به این بخش دسترسی دارد',
            )
            return redirect('first:home')

        return view_func(request, *args, **kwargs)

    return wrapper
'''


def ensure_local_access_policy():
    text = DECORATORS.read_text(encoding="utf-8")

    if "PERFUME SHOP LOCAL ACCESS POLICY" in text:
        print("[SKIP] local owner/admin policy already installed")
        return

    backup(DECORATORS)

    text = re.sub(
        r'(?m)^(\s*)if user\.is_owner:\s*$',
        r'\1if user.is_owner or user.is_superuser:',
        text,
    )

    text = (
        text.rstrip()
        + "\n\n"
        + textwrap.dedent(LOCAL_ACCESS_DECORATORS).strip()
        + "\n"
    )

    ast.parse(text)

    DECORATORS.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "[PATCH] first/decorators.py -> "
        "local superuser owner/admin policy"
    )


def patch_login_code():
    forms_text = FORMS.read_text(encoding="utf-8")

    if (
        "نام کاربری/ایمیل مالک"
        not in forms_text
        and "نام کاربری مالک"
        not in forms_text
    ):
        replace_class_method(
            FORMS,
            "LoginForm",
            "clean_phone",
            LOGIN_CLEAN_PHONE,
        )
    else:
        print(
            "[SKIP] LoginForm.clean_phone "
            "already patched by failed Phase 07"
        )

    views_text = VIEWS.read_text(encoding="utf-8")

    if (
        "'perfume-login:'"
        not in views_text
        or "is_superuser=True"
        not in views_text
    ):
        replace_top_function(
            VIEWS,
            "login_view",
            LOGIN_VIEW,
        )
    else:
        print(
            "[SKIP] login_view already patched "
            "by failed Phase 07"
        )


def patch_login_template():
    text = LOGIN_TEMPLATE.read_text(encoding="utf-8")
    original = text

    replacements = [
        (
            "شماره تلفن ثبت‌شده خود را وارد کنید",
            (
                "شماره تلفن را وارد کنید؛ "
                "مالک می‌تواند با نام کاربری یا ایمیل وارد شود"
            ),
        ),
        (
            ">شماره تلفن<",
            ">شماره تلفن / ورود مالک<",
        ),
        (
            'placeholder="09123456789"',
            'placeholder="09123456789 یا owner"',
        ),
    ]

    for old, new in replacements:
        if old in text:
            text = text.replace(old, new, 1)

    if text != original:
        backup(LOGIN_TEMPLATE)
        LOGIN_TEMPLATE.write_text(text, encoding="utf-8")
        print("[PATCH] first/templates/login.html")
    else:
        print("[INFO] login template did not need text patch")


THEME_JS = r'''
(() => {
  "use strict";

  const root = document.documentElement;
  const key = "velora-theme";

  const valid = value => (
    value === "day"
    || value === "night"
  );

  function storedTheme() {
    try {
      const candidates = [
        localStorage.getItem(key),
        localStorage.getItem("perfume-theme"),
        localStorage.getItem("theme"),
      ];

      for (const item of candidates) {
        if (valid(item)) {
          return item;
        }
      }
    } catch (_) {}

    const current = root.dataset.perfumeTheme;
    return valid(current) ? current : "night";
  }

  function apply(theme) {
    if (!valid(theme)) {
      theme = "night";
    }

    root.dataset.perfumeTheme = theme;
    root.style.colorScheme = (
      theme === "day"
        ? "light"
        : "dark"
    );

    if (document.body) {
      document.body.dataset.perfumeTheme = theme;
      document.body.classList.toggle(
        "theme-day",
        theme === "day"
      );
      document.body.classList.toggle(
        "theme-night",
        theme === "night"
      );
    }

    try {
      localStorage.setItem(key, theme);
      localStorage.setItem("perfume-theme", theme);
      localStorage.setItem("theme", theme);
    } catch (_) {}

    document
      .querySelectorAll("[data-theme-toggle]")
      .forEach(button => {
        const toDay = theme === "night";

        button.setAttribute(
          "title",
          toDay ? "حالت روز" : "حالت شب"
        );

        button.setAttribute(
          "aria-label",
          toDay
            ? "فعال کردن حالت روز"
            : "فعال کردن حالت شب"
        );
      });
  }

  apply(storedTheme());

  document.addEventListener(
    "DOMContentLoaded",
    () => {
      apply(storedTheme());
      setTimeout(
        () => apply(storedTheme()),
        0
      );
    }
  );

  window.addEventListener(
    "click",
    event => {
      const target = event.target;

      if (
        !target
        || !(target instanceof Element)
      ) {
        return;
      }

      const button = target.closest(
        "[data-theme-toggle]"
      );

      if (!button) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();

      const current = (
        valid(root.dataset.perfumeTheme)
          ? root.dataset.perfumeTheme
          : storedTheme()
      );

      apply(
        current === "night"
          ? "day"
          : "night"
      );
    },
    true
  );
})();
'''


THEME_CSS = r'''
/* Phase 07 v2 — final theme authority */

html[data-perfume-theme="day"]{
  color-scheme:light!important;
}

html[data-perfume-theme="night"]{
  color-scheme:dark!important;
}

html[data-perfume-theme="day"] body{
  background:#eee2d4!important;
  color:#18120e!important;
}

html[data-perfume-theme="day"] .phase-main{
  background:
    radial-gradient(
      circle at 82% 5%,
      rgba(165,105,47,.10),
      transparent 22%
    ),
    linear-gradient(
      180deg,
      #eee2d4,
      #dfccb7
    )!important;
}

html[data-perfume-theme="night"] body{
  background:#090706!important;
  color:#f7f0e7!important;
}

html[data-perfume-theme="night"] .phase-main{
  background:
    radial-gradient(
      circle at 82% 5%,
      rgba(165,98,42,.10),
      transparent 22%
    ),
    linear-gradient(
      180deg,
      #090706,
      #100b08
    )!important;
}

html[data-perfume-theme="day"] [data-theme-toggle]{
  background:#e2cfb8!important;
  color:#7c4c21!important;
  border-color:rgba(120,76,34,.26)!important;
}

html[data-perfume-theme="night"] [data-theme-toggle]{
  background:#17110d!important;
  color:#e3c286!important;
  border-color:rgba(218,178,112,.22)!important;
}
'''


def patch_base_assets():
    text = BASE.read_text(encoding="utf-8")
    original = text

    css_link = (
        '<link rel="stylesheet" '
        'href="{% static \'css/perfume-phase07-v2.css\' %}">'
    )

    js_link = (
        '<script src="{% static \'js/perfume-phase07-v2.js\' %}"></script>'
    )

    if "perfume-phase07-v2.css" not in text:
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

    if "perfume-phase07-v2.js" not in text:
        if "</body>" not in text:
            raise RuntimeError(
                "Could not find </body> in perfume_base.html"
            )

        text = text.replace(
            "</body>",
            "    " + js_link + "\n</body>",
            1,
        )

    if text != original:
        backup(BASE)
        BASE.write_text(text, encoding="utf-8")
        print(
            "[PATCH] first/templates/perfume_base.html "
            "-> Phase 07 v2 assets"
        )


def verify_owner_policy():
    command = (
        "from first.models import User; "
        "from first.decorators import owner_required, admin_required; "
        "u=User.objects.filter(is_superuser=True).first(); "
        "print('SUPERUSER=', None if u is None else "
        "{'id':u.id,'username':u.username,'role':u.role,"
        "'phone':u.phone,'is_superuser':u.is_superuser}); "
        "print('OWNER_DECORATOR=', callable(owner_required)); "
        "print('ADMIN_DECORATOR=', callable(admin_required))"
    )

    run(
        sys.executable,
        "manage.py",
        "shell",
        "-c",
        command,
    )


def main():
    print("=" * 84)
    print(" PHASE 07 V2 — RESUME OWNER LOGIN + DAY MODE")
    print("=" * 84)

    missing = [path for path in REQUIRED if not path.exists()]

    if missing:
        raise SystemExit(
            "Missing required files:\n"
            + "\n".join(str(p) for p in missing)
        )

    if BACKUP.exists():
        raise SystemExit(
            f"Backup already exists: {BACKUP}\n"
            "Rename/delete it only if you intentionally rerun v2."
        )

    BACKUP.mkdir(parents=True)

    # Previous Phase 07 stopped after forms.py and views.py.
    # These checks safely resume from that partial state.
    patch_login_code()

    # admin_required / owner_required were previously extracted to shop-core.
    # We add storefront-local wrappers here instead of touching shop-core.
    ensure_local_access_policy()

    patch_login_template()

    write(JS, THEME_JS)
    write(CSS, THEME_CSS)
    patch_base_assets()

    for path in [FORMS, VIEWS, DECORATORS]:
        ast.parse(path.read_text(encoding="utf-8"))
        print("[PYTHON OK]", path.relative_to(ROOT))

    print("\n[CHECK] Django")
    run(
        sys.executable,
        "manage.py",
        "check",
    )

    print("\n[CHECK] Migration drift")
    run(
        sys.executable,
        "manage.py",
        "makemigrations",
        "--check",
        "--dry-run",
    )

    print("\n[CHECK] Owner policy")
    verify_owner_policy()

    print("\n" + "=" * 84)
    print(" PHASE 07 V2 READY")
    print("=" * 84)
    print("Owner login:")
    print("  identifier: owner")
    print("  or: existing superuser email")
    print("  password: existing owner password")
    print("  phone/role/database are NOT changed")
    print()
    print("Theme:")
    print("  day/night double-toggle conflict fixed")
    print("  selected mode persists")
    print()
    print("Now run:")
    print("  python manage.py runserver")
    print("Then hard refresh browser with Ctrl+F5")


if __name__ == "__main__":
    main()
