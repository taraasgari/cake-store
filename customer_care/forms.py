import re

from django import forms
from django.db.models import Sum

from first.models import Order

from .models import (
    OrderActionItem,
    OrderActionRequest,
    SupportTicket,
)


PHONE_TRANSLATION = str.maketrans(
    '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩',
    '01234567890123456789',
)


def normalize_phone(value):
    value = (value or '').strip().translate(
        PHONE_TRANSLATION
    )
    value = re.sub(r'[\s\-()]', '', value)

    if value.startswith('+98'):
        value = '0' + value[3:]
    elif value.startswith('0098'):
        value = '0' + value[4:]
    elif value.startswith('98') and len(value) == 12:
        value = '0' + value[2:]

    return value


class OrderTrackingForm(forms.Form):
    order_number = forms.CharField(
        max_length=20,
        label='کد سفارش',
        widget=forms.TextInput(
            attrs={
                'class': 'w-full rounded-xl border p-3',
                'placeholder': 'مثلاً 12345678',
                'dir': 'ltr',
                'autocomplete': 'off',
            }
        ),
    )
    phone = forms.CharField(
        max_length=20,
        label='شماره تلفن سفارش',
        widget=forms.TextInput(
            attrs={
                'class': 'w-full rounded-xl border p-3',
                'placeholder': '09123456789',
                'dir': 'ltr',
                'inputmode': 'tel',
                'autocomplete': 'tel',
            }
        ),
    )

    def clean_phone(self):
        phone = normalize_phone(
            self.cleaned_data.get('phone')
        )

        if not re.fullmatch(r'09\d{9}', phone):
            raise forms.ValidationError(
                'شماره تلفن معتبر وارد کنید.'
            )

        return phone


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = [
            'subject',
            'order',
            'priority',
        ]
        widgets = {
            'subject': forms.TextInput(
                attrs={
                    'class': 'w-full rounded-xl border p-3',
                    'placeholder': 'موضوع درخواست',
                }
            ),
            'order': forms.Select(
                attrs={
                    'class': 'w-full rounded-xl border p-3',
                }
            ),
            'priority': forms.Select(
                attrs={
                    'class': 'w-full rounded-xl border p-3',
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is None:
            self.fields['order'].queryset = Order.objects.none()
        else:
            self.fields['order'].queryset = (
                Order.objects
                .filter(user=user)
                .order_by('-created_at')
            )

        self.fields['order'].required = False


class SupportMessageForm(forms.Form):
    body = forms.CharField(
        label='پیام',
        min_length=2,
        max_length=5000,
        widget=forms.Textarea(
            attrs={
                'class': 'w-full rounded-xl border p-3',
                'rows': 5,
                'placeholder': 'پیام خود را بنویسید...',
            }
        ),
    )


class OrderActionBaseForm(forms.ModelForm):
    class Meta:
        model = OrderActionRequest
        fields = [
            'reason',
            'description',
        ]
        widgets = {
            'reason': forms.Select(
                attrs={
                    'class': 'w-full rounded-xl border p-3',
                }
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'w-full rounded-xl border p-3',
                    'rows': 4,
                    'placeholder': 'توضیحات بیشتر...',
                }
            ),
        }


class ReturnRequestForm(OrderActionBaseForm):
    def __init__(
        self,
        *args,
        order=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.order = order
        self.remaining_by_item = {}

        if order is None:
            return

        already_requested = {
            row['order_item_id']: (
                row['total'] or 0
            )
            for row in (
                OrderActionItem.objects
                .filter(
                    request__order=order,
                    request__kind='return',
                )
                .exclude(
                    request__status='rejected'
                )
                .values(
                    'order_item_id'
                )
                .annotate(
                    total=Sum('quantity')
                )
            )
        }

        for item in order.items.all():
            remaining = max(
                0,
                item.quantity
                - int(
                    already_requested.get(
                        item.pk,
                        0,
                    )
                ),
            )

            self.remaining_by_item[
                item.pk
            ] = remaining

            self.fields[
                f'item_{item.pk}'
            ] = forms.BooleanField(
                required=False,
                label=item.product_name,
                disabled=(
                    remaining <= 0
                ),
            )

            self.fields[
                f'qty_{item.pk}'
            ] = forms.IntegerField(
                required=False,
                min_value=1,
                max_value=max(
                    1,
                    remaining,
                ),
                initial=1,
                label='تعداد',
                disabled=(
                    remaining <= 0
                ),
            )

    def clean(self):
        cleaned = super().clean()

        if self.order is None:
            return cleaned

        selected = []

        for item in self.order.items.all():
            if not cleaned.get(
                f'item_{item.pk}'
            ):
                continue

            remaining = (
                self.remaining_by_item
                .get(
                    item.pk,
                    0,
                )
            )

            quantity = (
                cleaned.get(
                    f'qty_{item.pk}'
                )
                or 1
            )

            if remaining <= 0:
                raise forms.ValidationError(
                    (
                        f'تمام تعداد '
                        f'«{item.product_name}» '
                        'قبلاً برای مرجوعی '
                        'ثبت شده است.'
                    )
                )

            if quantity > remaining:
                raise forms.ValidationError(
                    (
                        f'از «{item.product_name}» '
                        f'فقط {remaining} عدد دیگر '
                        'قابل مرجوعی است.'
                    )
                )

            selected.append(
                (
                    item,
                    quantity,
                )
            )

        if not selected:
            raise forms.ValidationError(
                (
                    'حداقل یک کالای قابل '
                    'مرجوعی را انتخاب کنید.'
                )
            )

        cleaned[
            'selected_items'
        ] = selected

        return cleaned


class AdminActionStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=OrderActionRequest.STATUS_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'w-full rounded-xl border p-3',
            }
        ),
    )
    admin_note = forms.CharField(
        required=False,
        max_length=5000,
        widget=forms.Textarea(
            attrs={
                'class': 'w-full rounded-xl border p-3',
                'rows': 4,
                'placeholder': 'یادداشت مدیریت...',
            }
        ),
    )
