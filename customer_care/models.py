import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from first.models import Order, OrderItem


def generate_ticket_reference():
    return 'SUP-' + secrets.token_hex(4).upper()


class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('new', 'جدید'),
        ('in_progress', 'در حال بررسی'),
        ('waiting_user', 'منتظر پاسخ کاربر'),
        ('answered', 'پاسخ داده شده'),
        ('closed', 'بسته شده'),
    ]

    PRIORITY_CHOICES = [
        ('normal', 'عادی'),
        ('high', 'مهم'),
        ('urgent', 'فوری'),
    ]

    reference = models.CharField(
        max_length=20,
        unique=True,
        default=generate_ticket_reference,
        editable=False,
        verbose_name='کد تیکت',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='support_tickets',
        verbose_name='کاربر',
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='support_tickets',
        verbose_name='سفارش مرتبط',
    )
    subject = models.CharField(
        max_length=180,
        verbose_name='موضوع',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True,
        verbose_name='وضعیت',
    )
    priority = models.CharField(
        max_length=12,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name='اولویت',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'تیکت پشتیبانی'
        verbose_name_plural = 'تیکت‌های پشتیبانی'

    def __str__(self):
        return f'{self.reference} - {self.subject}'


class SupportMessage(models.Model):
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='تیکت',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='support_messages',
        verbose_name='فرستنده',
    )
    body = models.TextField(
        verbose_name='پیام',
    )
    is_staff_reply = models.BooleanField(
        default=False,
        verbose_name='پاسخ پشتیبانی',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = 'پیام پشتیبانی'
        verbose_name_plural = 'پیام‌های پشتیبانی'

    def __str__(self):
        return f'{self.ticket.reference} - {self.created_at:%Y-%m-%d}'


class OrderActionRequest(models.Model):
    KIND_CHOICES = [
        ('cancel', 'درخواست لغو سفارش'),
        ('return', 'درخواست مرجوعی'),
    ]

    STATUS_CHOICES = [
        ('pending', 'در انتظار بررسی'),
        ('approved', 'تأیید شده'),
        ('rejected', 'رد شده'),
        ('received', 'کالا دریافت شد'),
        ('refund_pending', 'در انتظار بازگشت وجه'),
        ('refunded', 'وجه بازگشت داده شد'),
        ('closed', 'بسته شده'),
    ]

    REASON_CHOICES = [
        ('changed_mind', 'انصراف از خرید'),
        ('damaged', 'کالای آسیب‌دیده'),
        ('wrong_item', 'کالای اشتباه ارسال شده'),
        ('defective', 'کالای معیوب'),
        ('not_as_described', 'مغایرت با توضیحات'),
        ('other', 'سایر'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='order_action_requests',
        verbose_name='کاربر',
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='action_requests',
        verbose_name='سفارش',
    )
    kind = models.CharField(
        max_length=10,
        choices=KIND_CHOICES,
        verbose_name='نوع درخواست',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        verbose_name='وضعیت',
    )
    reason = models.CharField(
        max_length=30,
        choices=REASON_CHOICES,
        default='other',
        verbose_name='دلیل',
    )
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات کاربر',
    )
    admin_note = models.TextField(
        blank=True,
        verbose_name='یادداشت مدیریت',
    )
    refund_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='مبلغ قابل بازگشت',
    )
    stock_restored = models.BooleanField(
        default=False,
        verbose_name='موجودی بازگردانده شده',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'درخواست لغو/مرجوعی'
        verbose_name_plural = 'درخواست‌های لغو/مرجوعی'
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'kind'],
                condition=models.Q(
                    status__in=[
                        'pending',
                        'approved',
                        'received',
                        'refund_pending',
                    ]
                ),
                name='unique_open_order_action_per_kind',
            ),
        ]

    def __str__(self):
        return (
            f'{self.get_kind_display()} - '
            f'{self.order.order_number}'
        )


class OrderActionItem(models.Model):
    request = models.ForeignKey(
        OrderActionRequest,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='درخواست',
    )
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.PROTECT,
        related_name='action_request_items',
        verbose_name='آیتم سفارش',
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='تعداد',
    )
    unit_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='مبلغ واحد هنگام درخواست',
    )

    class Meta:
        verbose_name = 'آیتم مرجوعی'
        verbose_name_plural = 'آیتم‌های مرجوعی'
        constraints = [
            models.UniqueConstraint(
                fields=['request', 'order_item'],
                name='unique_item_per_order_action',
            ),
        ]

    @property
    def line_amount(self):
        return self.unit_amount * self.quantity

    def __str__(self):
        return (
            f'{self.order_item.product_name} '
            f'x {self.quantity}'
        )
