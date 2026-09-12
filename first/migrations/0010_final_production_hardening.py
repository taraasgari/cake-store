from django.db import migrations, models
from django.db.models.functions import Lower
import django.core.validators
import django.db.models.deletion
from django.utils.text import slugify


def _backfill_unique_slug(model, prefix):
    for row in model.objects.filter(slug='').order_by('pk'):
        base = slugify(getattr(row, 'name', '') or '') or f'{prefix}-{row.pk}'
        candidate = base[: model._meta.get_field('slug').max_length]
        if not candidate:
            candidate = f'{prefix}-{row.pk}'
        suffix = 2
        while model.objects.exclude(pk=row.pk).filter(slug=candidate).exists():
            tail = f'-{suffix}'
            candidate = f'{base[: max(1, model._meta.get_field("slug").max_length - len(tail))]}{tail}'
            suffix += 1
        row.slug = candidate
        row.save(update_fields=['slug'])


def normalize_users_and_settings(apps, schema_editor):
    User = apps.get_model('first', 'User')
    Product = apps.get_model('first', 'Product')
    Category = apps.get_model('first', 'Category')
    Brand = apps.get_model('first', 'Brand')
    ProductType = apps.get_model('first', 'ProductType')
    Tag = apps.get_model('first', 'Tag')
    SiteSettings = apps.get_model('first', 'SiteSettings')
    Order = apps.get_model('first', 'Order')

    # Repair legacy rows created before slug generation became mandatory.
    for model, prefix in (
        (Product, 'product'),
        (Category, 'category'),
        (Brand, 'brand'),
        (ProductType, 'type'),
        (Tag, 'tag'),
    ):
        _backfill_unique_slug(model, prefix)

    seen = {}
    users_to_update = []
    for user in User.objects.all().only('id', 'email'):
        email = (user.email or '').strip().lower()
        if not email:
            continue
        if email in seen and seen[email] != user.pk:
            raise RuntimeError(
                'Cannot enforce case-insensitive email uniqueness. '
                f'Conflicting users: {seen[email]} and {user.pk} ({email}).'
            )
        seen[email] = user.pk
        if user.email != email:
            user.email = email
            users_to_update.append(user)
    if users_to_update:
        User.objects.bulk_update(users_to_update, ['email'])

    # Freeze customer identity on existing orders so historical invoices
    # remain readable even if the account is later edited or removed.
    for order in Order.objects.select_related('user').all().iterator():
        if not order.user_id:
            continue
        fields = []
        if not order.customer_name:
            full_name = (
                f'{order.user.first_name} {order.user.last_name}'.strip()
                or order.user.username
            )
            order.customer_name = full_name
            fields.append('customer_name')
        if not order.customer_email:
            order.customer_email = order.user.email or ''
            fields.append('customer_email')
        if fields:
            order.save(update_fields=fields)

    settings_rows = list(SiteSettings.objects.order_by('pk'))
    if settings_rows:
        keep = settings_rows[0]
        for extra in settings_rows[1:]:
            extra.delete()
        keep.singleton_key = 1

        # Only replace the old cosmetics defaults. Merchant-customized values stay untouched.
        replacements = {
            'site_name': ('آرایشی شاپ', 'فروشگاه عطر'),
            'site_title': ('آرایشی شاپ - لوکس ترین فروشگاه آرایشی', 'فروشگاه عطر - خانه رایحه‌های ماندگار'),
            'site_description': ('مرجع تخصصی لوازم آرایشی با کیفیت و اصالت تضمینی', 'فروشگاه تخصصی عطر با تمرکز بر اصالت، انتخاب دقیق و تجربه لوکس'),
            'primary_color': ('#ec407a', '#C9954D'),
            'secondary_color': ('#d81b60', '#75471F'),
            'accent_color': ('#ab47bc', '#E3C286'),
            'background_color': ('#fdf2f8', '#090706'),
            'text_color': ('#1a1a2e', '#F7F0E7'),
            'footer_text': ('© ۱۴۰۴ آرایشی شاپ - تمامی حقوق محفوظ است', '© ۱۴۰۵ فروشگاه عطر - تمامی حقوق محفوظ است'),
            'footer_bg_color': ('#1a0a1a', '#0B0806'),
            'email': ('info@arayeshi.shop', 'info@example.com'),
        }
        update_fields = ['singleton_key']
        for field, (old, new) in replacements.items():
            if getattr(keep, field) == old:
                setattr(keep, field, new)
                update_fields.append(field)
        keep.save(update_fields=update_fields)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('first', '0009_v7_preserve_order_history'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=models.CharField(
                max_length=11,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        regex='^09\\d{9}$',
                        message='شماره تلفن باید با ۰۹ شروع شود و ۱۱ رقم باشد.',
                    )
                ],
                verbose_name='شماره تلفن',
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='customer_email',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
        migrations.AddField(
            model_name='order',
            name='customer_name',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AlterField(
            model_name='order',
            name='user',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='orders',
                to='first.user',
            ),
        ),
        migrations.CreateModel(
            name='NewsletterSubscriber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='ایمیل')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'عضو خبرنامه',
                'verbose_name_plural': 'اعضای خبرنامه',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='singleton_key',
            field=models.PositiveSmallIntegerField(editable=False, null=True),
        ),
        migrations.RunPython(normalize_users_and_settings, noop_reverse),
        migrations.AlterField(
            model_name='sitesettings',
            name='singleton_key',
            field=models.PositiveSmallIntegerField(default=1, editable=False, unique=True),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.UniqueConstraint(Lower('email'), name='first_user_email_ci_unique'),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='site_name',
            field=models.CharField(default='فروشگاه عطر', max_length=100, verbose_name='نام سایت'),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='site_title',
            field=models.CharField(default='فروشگاه عطر - خانه رایحه‌های ماندگار', max_length=100, verbose_name='عنوان سایت'),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='site_description',
            field=models.TextField(default='فروشگاه تخصصی عطر با تمرکز بر اصالت، انتخاب دقیق و تجربه لوکس', max_length=500, verbose_name='توضیحات سایت'),
        ),
        migrations.AlterField(model_name='sitesettings', name='primary_color', field=models.CharField(default='#C9954D', max_length=7, verbose_name='رنگ اصلی')),
        migrations.AlterField(model_name='sitesettings', name='secondary_color', field=models.CharField(default='#75471F', max_length=7, verbose_name='رنگ ثانویه')),
        migrations.AlterField(model_name='sitesettings', name='accent_color', field=models.CharField(default='#E3C286', max_length=7, verbose_name='رنگ تاکید')),
        migrations.AlterField(model_name='sitesettings', name='background_color', field=models.CharField(default='#090706', max_length=7, verbose_name='رنگ پس‌زمینه')),
        migrations.AlterField(model_name='sitesettings', name='text_color', field=models.CharField(default='#F7F0E7', max_length=7, verbose_name='رنگ متن')),
        migrations.AlterField(model_name='sitesettings', name='footer_text', field=models.CharField(default='© ۱۴۰۵ فروشگاه عطر - تمامی حقوق محفوظ است', max_length=200, verbose_name='متن فوتر')),
        migrations.AlterField(model_name='sitesettings', name='footer_bg_color', field=models.CharField(default='#0B0806', max_length=7, verbose_name='رنگ پس‌زمینه فوتر')),
        migrations.AlterField(model_name='sitesettings', name='email', field=models.EmailField(default='info@example.com', max_length=254, verbose_name='ایمیل')),
    ]
