#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Restore the storefront UI to the committed starter/shop-core-style frontend,
while KEEPING only the custom perfume homepage + top header/nav from Phase 01.

Run beside manage.py:
    python restore_core_frontend_keep_home.py

What stays custom:
- first/templates/index.html
- first/templates/perfume_base.html
- static/css/perfume-phase01.css
- static/js/perfume-phase01.js

What is restored from current Git HEAD:
- every other tracked template in first/templates/
- every tracked template in customer_care/templates/

Backend is never modified.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / ".restore_core_frontend_backup"

KEEP = {
    "first/templates/index.html",
    "first/templates/perfume_base.html",
    "static/css/perfume-phase01.css",
    "static/js/perfume-phase01.js",
}

GENERATED_OLD_THEME_FILES = {
    "static/css/perfume-luxury.css",
    "static/css/perfume-luxury-v2.css",
    "static/js/perfume-luxury.js",
    "static/js/perfume-luxury-v2.js",
}

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


def cmd(*args: str, capture: bool = False) -> str:
    result = subprocess.run(
        list(args),
        cwd=ROOT,
        text=True,
        capture_output=capture,
    )
    if result.returncode:
        if capture:
            print(result.stdout)
            print(result.stderr)
        raise RuntimeError("Command failed: " + " ".join(args))
    return result.stdout if capture else ""


def git_bytes(rel: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"HEAD:{rel}"],
        cwd=ROOT,
        capture_output=True,
    )
    if result.returncode:
        raise RuntimeError(f"Could not read HEAD:{rel}")
    return result.stdout


def backup(rel: str) -> None:
    src = ROOT / rel
    if not src.exists():
        return
    dst = BACKUP / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> None:
    print("=" * 78)
    print(" RESTORE CORE/STarter FRONTEND — KEEP HOME + HEADER")
    print("=" * 78)

    if not (ROOT / "manage.py").exists():
        raise SystemExit("Put this script beside manage.py in perfume-shop.")

    if not (ROOT / ".git").exists():
        raise SystemExit("perfume-shop must be a Git repository.")

    if BACKUP.exists():
        raise SystemExit(
            f"Backup already exists: {BACKUP}\n"
            "Rename/delete it only if you intentionally want to run this again."
        )

    missing_keep = [p for p in KEEP if not (ROOT / p).exists()]
    if missing_keep:
        raise SystemExit(
            "Custom Home/Header files are missing:\n  - "
            + "\n  - ".join(missing_keep)
        )

    BACKUP.mkdir(parents=True)

    backend_snapshot = {
        rel: (ROOT / rel).read_bytes()
        for rel in BACKEND_GUARD
        if (ROOT / rel).exists()
    }

    # Backup custom files too, so this operation is fully reversible.
    for rel in KEEP:
        backup(rel)

    # Remove accidental old-theme CSS imports from the custom perfume base.
    base_path = ROOT / "first/templates/perfume_base.html"
    base_text = base_path.read_text(encoding="utf-8")
    cleaned_lines = []
    for line in base_text.splitlines():
        if "perfume-luxury.css" in line or "perfume-luxury-v2.css" in line:
            continue
        cleaned_lines.append(line)
    base_path.write_text("\n".join(cleaned_lines) + "\n", encoding="utf-8")
    print("[KEEP] first/templates/perfume_base.html (header/nav)")
    print("[KEEP] first/templates/index.html (homepage)")
    print("[KEEP] Phase 01 CSS/JS")

    tracked = cmd("git", "ls-files", capture=True).splitlines()

    restore_paths = [
        rel for rel in tracked
        if (
            rel.startswith("first/templates/")
            or rel.startswith("customer_care/templates/")
        )
        and rel not in KEEP
    ]

    print(f"\n[RESTORE] {len(restore_paths)} tracked templates from Git HEAD")

    for rel in restore_paths:
        backup(rel)
        target = ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git_bytes(rel))
        print("  [RESTORED]", rel)

    # Old generated perfume themes are no longer referenced.
    for rel in GENERATED_OLD_THEME_FILES:
        path = ROOT / rel
        if path.exists():
            backup(rel)
            path.unlink()
            print("[REMOVE OLD GENERATED THEME]", rel)

    # Hard backend safety check.
    for rel, original in backend_snapshot.items():
        if (ROOT / rel).read_bytes() != original:
            raise RuntimeError(f"Backend changed unexpectedly: {rel}")

    print("\n[CHECK] Django")
    cmd(sys.executable, "manage.py", "check")

    print("\n[CHECK] Migration drift")
    cmd(sys.executable, "manage.py", "makemigrations", "--check", "--dry-run")

    print("\n" + "=" * 78)
    print(" DONE")
    print("=" * 78)
    print("Custom kept:")
    print("  - Home page")
    print("  - Large perfume header/nav/search")
    print("Restored:")
    print("  - Login / Signup")
    print("  - Product/catalog/detail pages")
    print("  - Cart / Checkout / Orders")
    print("  - Profile / Account pages")
    print("  - Customer-care pages")
    print("Backend remained byte-for-byte unchanged.")
    print("\nNow run:")
    print("  python manage.py runserver")
    print("\nThen inspect /, /login/, /signup/, /products/, /profile/.")


if __name__ == "__main__":
    main()
