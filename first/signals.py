"""Clean replaced/deleted uploaded files after successful database commits."""
from django.db import transaction
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import (
    Brand,
    Category,
    Color,
    Product,
    ProductImage,
    ProductVariant,
    SiteSettings,
    SliderImage,
    User,
)

_FILE_FIELDS = {
    User: ('profile_image',),
    Category: ('image',),
    Brand: ('logo',),
    Color: ('image',),
    Product: ('main_image',),
    ProductVariant: ('image',),
    ProductImage: ('image',),
    SiteSettings: (
        'logo',
        'favicon',
        'default_product_image',
        'default_avatar',
        'background_image',
    ),
    SliderImage: ('image',),
}


def _schedule_delete(field_file):
    if not field_file or not getattr(field_file, 'name', ''):
        return
    storage = field_file.storage
    name = field_file.name
    transaction.on_commit(lambda: storage.delete(name) if storage.exists(name) else None)


@receiver(pre_save)
def cleanup_replaced_files(sender, instance, **kwargs):
    fields = _FILE_FIELDS.get(sender)
    if not fields or not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    for field_name in fields:
        old_file = getattr(old, field_name, None)
        new_file = getattr(instance, field_name, None)
        old_name = getattr(old_file, 'name', '') or ''
        new_name = getattr(new_file, 'name', '') or ''
        if old_name and old_name != new_name:
            _schedule_delete(old_file)


@receiver(post_delete)
def cleanup_deleted_files(sender, instance, **kwargs):
    fields = _FILE_FIELDS.get(sender)
    if not fields:
        return
    for field_name in fields:
        _schedule_delete(getattr(instance, field_name, None))
