# first/templatetags/filters.py

from django import template

register = template.Library()

@register.filter(name='abs')
def abs_filter(value):
    """فیلتر قدر مطلق برای تمپلیت‌ها"""
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value