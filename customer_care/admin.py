from django.contrib import admin

from .models import (
    OrderActionItem,
    OrderActionRequest,
    SupportMessage,
    SupportTicket,
)


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 0
    readonly_fields = ['created_at']


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = [
        'reference',
        'user',
        'subject',
        'status',
        'priority',
        'updated_at',
    ]
    list_filter = [
        'status',
        'priority',
    ]
    search_fields = [
        'reference',
        'user__phone',
        'subject',
    ]
    inlines = [
        SupportMessageInline,
    ]


class OrderActionItemInline(admin.TabularInline):
    model = OrderActionItem
    extra = 0


@admin.register(OrderActionRequest)
class OrderActionRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'order',
        'user',
        'kind',
        'status',
        'refund_amount',
        'created_at',
    ]
    list_filter = [
        'kind',
        'status',
    ]
    search_fields = [
        'order__order_number',
        'user__phone',
    ]
    inlines = [
        OrderActionItemInline,
    ]
