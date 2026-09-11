from __future__ import annotations

import json
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify


def _model(name):
    try:
        return apps.get_model("first", name)
    except LookupError:
        return None


def _has_field(model, name):
    if model is None:
        return False
    try:
        model._meta.get_field(name)
        return True
    except Exception:
        return False


def _set_if_field(obj, field, value):
    if value is None:
        return
    if _has_field(type(obj), field):
        setattr(obj, field, value)


def _upsert_named(model, name, *, parent=None):
    if model is None:
        return None

    obj = model.objects.filter(name=name).first()
    if obj is None:
        obj = model(name=name)

    if _has_field(model, "slug") and not getattr(obj, "slug", None):
        base = slugify(name, allow_unicode=True) or "item"
        candidate = base
        serial = 2
        query = model.objects.all()
        if getattr(obj, "pk", None):
            query = query.exclude(pk=obj.pk)

        while query.filter(slug=candidate).exists():
            candidate = f"{base}-{serial}"
            serial += 1

        obj.slug = candidate

    if _has_field(model, "is_active"):
        obj.is_active = True

    if parent is not None and _has_field(model, "parent"):
        obj.parent = parent

    obj.save()
    return obj


class Command(BaseCommand):
    help = "Apply storefront branding and seed optional starter catalog data."

    def add_arguments(self, parser):
        parser.add_argument(
            "profile",
            nargs="?",
            default="store_profile.json",
        )

    def handle(self, *args, **options):
        profile_path = Path(options["profile"]).resolve()

        if not profile_path.exists():
            raise CommandError(f"Profile not found: {profile_path}")

        try:
            data = json.loads(
                profile_path.read_text(encoding="utf-8")
            )
        except Exception as exc:
            raise CommandError(
                f"Invalid profile JSON: {exc}"
            ) from exc

        SiteSettings = _model("SiteSettings")
        Category = _model("Category")
        ProductType = _model("ProductType")
        Tag = _model("Tag")

        if SiteSettings is None:
            raise CommandError("first.SiteSettings model not found.")

        if hasattr(SiteSettings, "get_settings"):
            site = SiteSettings.get_settings()
        else:
            site = SiteSettings.objects.first() or SiteSettings()

        branding = data.get("branding", {})
        mapping = {
            "site_name": branding.get("site_name"),
            "site_title": branding.get("site_title"),
            "site_description": branding.get("site_description"),
            "primary_color": branding.get("primary_color"),
            "secondary_color": branding.get("secondary_color"),
            "accent_color": branding.get("accent_color"),
            "background_color": branding.get("background_color"),
            "text_color": branding.get("text_color"),
            "footer_text": branding.get("footer_text"),
        }

        for field, value in mapping.items():
            _set_if_field(site, field, value)

        site.save()

        category_count = 0
        for item in data.get("categories", []):
            if isinstance(item, str) and item.strip():
                _upsert_named(Category, item.strip())
                category_count += 1

        type_count = 0
        for name in data.get("product_types", []):
            if isinstance(name, str) and name.strip():
                _upsert_named(ProductType, name.strip())
                type_count += 1

        tag_count = 0
        for name in data.get("tags", []):
            if isinstance(name, str) and name.strip():
                _upsert_named(Tag, name.strip())
                tag_count += 1

        self.stdout.write(
            self.style.SUCCESS("Store profile applied successfully.")
        )
        self.stdout.write(f"Categories seeded: {category_count}")
        self.stdout.write(f"Product types seeded: {type_count}")
        self.stdout.write(f"Tags seeded: {tag_count}")
