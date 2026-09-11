"""تنظیمات عمومی سایت و داده‌های ویرایشگر بصری."""

import json

from .models import SiteSettings


DEFAULT_CUSTOMIZER_THEME = {
    'primary': '#ec407a',
    'secondary': '#d81b60',
    'accent': '#ab47bc',
    'bg': '#fdf2f8',
    'text': '#1a1a2e',
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

    can_edit = bool(
        user and
        user.is_authenticated and
        getattr(user, 'is_owner', False)
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