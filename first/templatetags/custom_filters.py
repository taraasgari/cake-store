from django import template
from django.utils.safestring import mark_safe
from ..models import SiteSettings
from ..decorators import (
    check_admin_permission,
    get_effective_admin_permissions,
)

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """دریافت آیتم از دیکشنری با کلید"""
    if dictionary is None:
        return {}
    return dictionary.get(key, {})

@register.filter
def get_value(dictionary, key):
    """دریافت مقدار از دیکشنری با کلید"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def has_permission(user, permission_name):
    return check_admin_permission(
        user,
        permission_name,
    )

@register.filter
def get_user_permissions(user):
    return get_effective_admin_permissions(
        user
    )

@register.filter(name='format_number')
def format_number(value):
    """تبدیل اعداد به فارسی یا انگلیسی بر اساس تنظیمات سایت"""
    if value is None:
        return ''
    settings = SiteSettings.get_settings()
    str_value = str(value)
    if settings.number_format == 'persian':
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'
        trans_table = str.maketrans(english_digits, persian_digits)
        return mark_safe(str_value.translate(trans_table))
    return mark_safe(str_value)

@register.filter(name='price_format')
def price_format(value):
    """فرمت قیمت با جداکننده هزارگان + تبدیل به فارسی/انگلیسی"""
    if value is None:
        return ''
    settings = SiteSettings.get_settings()
    try:
        formatted = f"{int(value):,}"
    except:
        formatted = str(value)
    if settings.number_format == 'persian':
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'
        trans_table = str.maketrans(english_digits, persian_digits)
        return mark_safe(formatted.translate(trans_table))
    return mark_safe(formatted)

# ============================================
# فیلترهای دیگر
# ============================================

@register.filter
def abs_filter(value):
    """فیلتر قدر مطلق برای تمپلیت‌ها"""
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value

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
