"""Validation for the existing SliderImage management forms."""
from urllib.parse import urlsplit

from django import forms
from django.core.exceptions import ValidationError

from .models import SliderImage


def safe_slider_link(value):
    value = str(value or '').strip()
    if not value:
        return ''
    if '\\' in value or any(ord(c) < 32 for c in value):
        raise ValidationError('لینک معتبر نیست.')
    parsed = urlsplit(value)
    if value.startswith('/') and not value.startswith('//'):
        return value
    if parsed.scheme in ('http', 'https') and parsed.netloc and not parsed.username:
        forms.URLField().clean(value)
        return value
    raise ValidationError('لینک باید مسیر داخلی با / یا آدرس کامل http/https باشد.')


class SliderForm(forms.ModelForm):
    class Meta:
        model = SliderImage
        fields = ['title', 'subtitle', 'image', 'order', 'link', 'button_text', 'is_active']

    def clean_link(self):
        return safe_slider_link(self.cleaned_data.get('link'))
