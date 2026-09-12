"""تنظیمات عمومی سایت و داده‌های ویرایشگر بصری."""

import json

from .models import SiteSettings


DEFAULT_CUSTOMIZER_THEME = {
    'primary': '#c9954d',
    'secondary': '#75471f',
    'accent': '#e3c286',
    'bg': '#090706',
    'text': '#f7f0e7',
}


def _read_customizer_rules(site_settings):
    try:
        rules = json.loads(
            site_settings.customizer_rules or '[]'
        )
    except (TypeError, ValueError, json.JSONDecodeError):
        return []

    return rules if isinstance(rules, list) else []


def site_settings(request):
    """ارسال تنظیمات سایت به تمام قالب‌ها."""
    current_settings = SiteSettings.get_settings()
    user = getattr(request, 'user', None)

    stored_theme = current_settings.customizer_theme

    if not isinstance(stored_theme, dict):
        stored_theme = {}

    theme = {
        **DEFAULT_CUSTOMIZER_THEME,
        **stored_theme,
        'primary': str(
            current_settings.primary_color or
            DEFAULT_CUSTOMIZER_THEME['primary']
        ),
        'secondary': str(
            current_settings.secondary_color or
            DEFAULT_CUSTOMIZER_THEME['secondary']
        ),
        'accent': str(
            current_settings.accent_color or
            DEFAULT_CUSTOMIZER_THEME['accent']
        ),
        'bg': str(
            current_settings.background_color or
            DEFAULT_CUSTOMIZER_THEME['bg']
        ),
        'text': str(
            current_settings.text_color or
            DEFAULT_CUSTOMIZER_THEME['text']
        ),
    }

    # Keep this permission gate in sync with ``owner_required``.
    # A Django superuser is treated as the store owner throughout the
    # admin/owner panel, even when the custom ``role`` field is still
    # ``user`` (which is exactly how a normal createsuperuser account is
    # created).  Previously the visual editor only checked ``is_owner``;
    # that made the studio page open for a superuser while the iframe
    # silently disabled every editing listener.
    can_edit = bool(
        user and
        user.is_authenticated and
        (
            getattr(user, 'is_superuser', False) or
            getattr(user, 'is_owner', False)
        )
    )

    return {
        'settings': current_settings,
        'visual_customizer': {
            'rules': _read_customizer_rules(
                current_settings
            ),
            'theme': theme,
            'canEdit': can_edit,
        },
    }