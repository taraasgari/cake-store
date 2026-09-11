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