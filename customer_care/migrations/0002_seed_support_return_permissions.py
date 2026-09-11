from django.db import migrations


PERMISSIONS = [
    (
        'support_view',
        'مشاهده تیکت‌های پشتیبانی',
    ),
    (
        'support_reply',
        'پاسخگویی به تیکت‌های پشتیبانی',
    ),
    (
        'returns_manage',
        'مدیریت لغو و مرجوعی سفارش‌ها',
    ),
]


def seed(apps, schema_editor):
    Permission = apps.get_model(
        'first',
        'AdminPermission',
    )
    Role = apps.get_model(
        'first',
        'AdminRole',
    )

    created = {}

    for name, label in PERMISSIONS:
        obj, _ = (
            Permission.objects.get_or_create(
                name=name,
                defaults={
                    'label': label,
                    'is_active': True,
                },
            )
        )

        obj.label = label
        obj.is_active = True
        obj.save(
            update_fields=[
                'label',
                'is_active',
            ]
        )

        created[name] = obj

    support_role = (
        Role.objects.filter(
            name='support'
        ).first()
    )

    if support_role:
        support_role.permissions.add(
            created['support_view'],
            created['support_reply'],
        )

    order_role = (
        Role.objects.filter(
            name='order_manager'
        ).first()
    )

    if order_role:
        order_role.permissions.add(
            created['returns_manage']
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        (
            'customer_care',
            '0001_customer_care_features',
        ),
    ]

    operations = [
        migrations.RunPython(
            seed,
            noop,
        ),
    ]
