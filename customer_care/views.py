from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Sum
from django.http import Http404
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.views.decorators.http import require_POST

from first.decorators import permission_required
from first.models import (
    AdminPermission,
    Order,
    Product,
    ProductVariant,
)

from .forms import (
    AdminActionStatusForm,
    OrderActionBaseForm,
    OrderTrackingForm,
    ReturnRequestForm,
    SupportMessageForm,
    SupportTicketForm,
)
from .models import (
    OrderActionItem,
    OrderActionRequest,
    SupportMessage,
    SupportTicket,
)


CANCEL_ALLOWED_STATUSES = {
    'pending',
    'paid',
    'processing',
}

RETURN_ALLOWED_STATUSES = {
    'delivered',
}


def _open_action_exists(order, kind):
    return OrderActionRequest.objects.filter(
        order=order,
        kind=kind,
        status__in=[
            'pending',
            'approved',
            'received',
            'refund_pending',
        ],
    ).exists()


def _locked_return_selection(order, selected):
    # Revalidate return quantities while the order row is locked.
    # This repeats form validation inside the transaction so concurrent
    # requests cannot both consume the same remaining return quantity.
    item_ids = [
        item.pk
        for item, _quantity in selected
    ]

    locked_items = {
        item.pk: item
        for item in (
            order.items
            .select_for_update()
            .filter(pk__in=item_ids)
        )
    }

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
            .values('order_item_id')
            .annotate(total=Sum('quantity'))
        )
    }

    validated = []

    for submitted_item, quantity in selected:
        item = locked_items.get(
            submitted_item.pk
        )

        if item is None:
            raise ValueError(
                'یکی از اقلام سفارش دیگر معتبر نیست.'
            )

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

        if quantity > remaining:
            raise ValueError(
                (
                    f'از «{item.product_name}» '
                    f'فقط {remaining} عدد دیگر '
                    'قابل مرجوعی است.'
                )
            )

        validated.append(
            (item, quantity)
        )

    return validated


def _ticket_for_user_or_404(user, reference):
    return get_object_or_404(
        SupportTicket.objects.select_related(
            'order',
            'user',
        ),
        reference=reference,
        user=user,
    )


def _restore_stock_for_action(action):
    if action.stock_restored:
        return

    with transaction.atomic():
        action = (
            OrderActionRequest.objects
            .select_for_update()
            .get(pk=action.pk)
        )

        if action.stock_restored:
            return

        if action.kind == 'cancel':
            action_items = [
                (
                    item,
                    item.quantity,
                )
                for item in action.order.items.select_related(
                    'product',
                    'variant',
                )
            ]
        else:
            action_items = [
                (
                    action_item.order_item,
                    action_item.quantity,
                )
                for action_item in action.items.select_related(
                    'order_item__product',
                    'order_item__variant',
                )
            ]

        for order_item, quantity in action_items:
            if order_item.variant_id:
                ProductVariant.objects.filter(
                    pk=order_item.variant_id
                ).update(
                    stock=F('stock') + quantity
                )

            elif order_item.product_id:
                Product.objects.filter(
                    pk=order_item.product_id
                ).update(
                    stock=F('stock') + quantity,
                    is_available=True,
                )

            if order_item.product_id:
                product = (
                    Product.objects
                    .select_for_update()
                    .get(pk=order_item.product_id)
                )
                product.sales_count = max(
                    0,
                    product.sales_count - quantity,
                )
                product.save(
                    update_fields=['sales_count']
                )

        action.stock_restored = True
        action.save(
            update_fields=[
                'stock_restored',
                'updated_at',
            ]
        )


def order_tracking(request):
    from time import time

    translation = str.maketrans(
        '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩',
        '01234567890123456789',
    )

    order = None
    searched = False
    now_ts = int(time())

    attempts = request.session.get(
        'order_tracking_attempts',
        [],
    )

    attempts = [
        int(ts)
        for ts in attempts
        if (
            isinstance(
                ts,
                (int, float),
            )
            and now_ts - int(ts) < 600
        )
    ]

    if request.method == 'POST':
        if len(attempts) >= 10:
            messages.error(
                request,
                (
                    'تعداد تلاش‌های پیگیری بیش از حد مجاز است. '
                    'کمی بعد دوباره تلاش کنید.'
                ),
            )

            return render(
                request,
                'customer_care/order_tracking.html',
                {
                    'form': OrderTrackingForm(
                        request.POST
                    ),
                    'order': None,
                    'searched': True,
                },
                status=429,
            )

        attempts.append(
            now_ts
        )
        request.session[
            'order_tracking_attempts'
        ] = attempts

        if request.user.is_authenticated:
            searched = True

            order_code = (
                request.POST.get(
                    'order_number',
                    '',
                )
                .strip()
                .translate(translation)
                .lstrip('#')
            )

            if order_code:
                order = (
                    Order.objects
                    .prefetch_related('items')
                    .filter(
                        order_number=order_code,
                        user=request.user,
                    )
                    .first()
                )

            form = OrderTrackingForm()
        else:
            form = OrderTrackingForm(
                request.POST
            )

            if form.is_valid():
                searched = True

                order_code = (
                    form.cleaned_data[
                        'order_number'
                    ]
                    .strip()
                    .translate(translation)
                    .lstrip('#')
                )

                order = (
                    Order.objects
                    .prefetch_related('items')
                    .filter(
                        order_number=order_code,
                        phone=(
                            form.cleaned_data[
                                'phone'
                            ]
                        ),
                    )
                    .first()
                )

        if order is not None:
            request.session[
                'order_tracking_attempts'
            ] = []
    else:
        form = OrderTrackingForm()

    return render(
        request,
        'customer_care/order_tracking.html',
        {
            'form': form,
            'order': order,
            'searched': searched,
        },
    )


@login_required
def support_home(request):
    tickets = (
        SupportTicket.objects
        .filter(user=request.user)
        .select_related('order')
    )

    return render(
        request,
        'customer_care/support_home.html',
        {
            'tickets': tickets,
        },
    )


@login_required
def support_create(request):
    initial = {}

    if request.method != 'POST':
        order_id = request.GET.get(
            'order'
        )

        if order_id:
            owned_order = (
                Order.objects
                .filter(
                    pk=order_id,
                    user=request.user,
                )
                .first()
            )

            if owned_order is not None:
                initial[
                    'order'
                ] = owned_order

    if request.method == 'POST':
        form = SupportTicketForm(
            request.POST,
            user=request.user,
        )
        message_form = SupportMessageForm(
            request.POST
        )

        if (
            form.is_valid()
            and message_form.is_valid()
        ):
            with transaction.atomic():
                ticket = form.save(
                    commit=False
                )
                ticket.user = request.user
                ticket.save()

                SupportMessage.objects.create(
                    ticket=ticket,
                    sender=request.user,
                    body=message_form.cleaned_data[
                        'body'
                    ],
                    is_staff_reply=False,
                )

            messages.success(
                request,
                'تیکت پشتیبانی ثبت شد.',
            )

            return redirect(
                'customer_care:support_detail',
                reference=ticket.reference,
            )
    else:
        form = SupportTicketForm(
            user=request.user,
            initial=initial,
        )
        message_form = (
            SupportMessageForm()
        )

    return render(
        request,
        'customer_care/support_create.html',
        {
            'form': form,
            'message_form': message_form,
        },
    )


@login_required
def support_detail(
    request,
    reference,
):
    ticket = _ticket_for_user_or_404(
        request.user,
        reference,
    )

    return render(
        request,
        'customer_care/support_detail.html',
        {
            'ticket': ticket,
            'message_form': SupportMessageForm(),
        },
    )


@login_required
@require_POST
def support_reply(
    request,
    reference,
):
    ticket = _ticket_for_user_or_404(
        request.user,
        reference,
    )

    if ticket.status == 'closed':
        messages.error(
            request,
            'این تیکت بسته شده است.',
        )
        return redirect(
            'customer_care:support_detail',
            reference=ticket.reference,
        )

    form = SupportMessageForm(
        request.POST
    )

    if form.is_valid():
        SupportMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            body=form.cleaned_data['body'],
            is_staff_reply=False,
        )

        ticket.status = 'in_progress'
        ticket.save(
            update_fields=[
                'status',
                'updated_at',
            ]
        )

        messages.success(
            request,
            'پیام شما ارسال شد.',
        )

    return redirect(
        'customer_care:support_detail',
        reference=ticket.reference,
    )


@login_required
def order_actions_home(request):
    return redirect(
        'first:user_orders'
    )


@login_required
def order_action_detail(
    request,
    pk,
):
    action = get_object_or_404(
        OrderActionRequest.objects
        .select_related('order')
        .prefetch_related(
            'items__order_item'
        ),
        pk=pk,
        user=request.user,
    )

    return render(
        request,
        'customer_care/order_action_detail.html',
        {
            'action': action,
        },
    )


@login_required
@require_POST
def cancel_order_request(
    request,
    order_number,
):
    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user,
    )

    if order.status not in CANCEL_ALLOWED_STATUSES:
        messages.error(
            request,
            'این سفارش دیگر قابل لغو نیست.',
        )
        return redirect(
            'first:order_detail',
            order_number=order.order_number,
        )

    if _open_action_exists(
        order,
        'cancel',
    ):
        messages.info(
            request,
            'برای این سفارش قبلاً درخواست لغو ثبت شده است.',
        )
        return redirect(
            'customer_care:order_actions_home'
        )

    form = OrderActionBaseForm(
        request.POST
    )

    if not form.is_valid():
        messages.error(
            request,
            'اطلاعات درخواست لغو معتبر نیست.',
        )
        return redirect(
            'first:order_detail',
            order_number=order.order_number,
        )

    action = form.save(
        commit=False
    )
    action.user = request.user
    action.order = order
    action.kind = 'cancel'
    action.refund_amount = order.total
    action.save()

    messages.success(
        request,
        'درخواست لغو سفارش ثبت شد.',
    )

    return redirect(
        'customer_care:order_action_detail',
        pk=action.pk,
    )


@login_required
def return_order_request(
    request,
    order_number,
):
    order = get_object_or_404(
        Order.objects.prefetch_related(
            'items'
        ),
        order_number=order_number,
        user=request.user,
    )

    if order.status not in RETURN_ALLOWED_STATUSES:
        messages.error(
            request,
            'مرجوعی فقط برای سفارش تحویل‌شده قابل ثبت است.',
        )
        return redirect(
            'first:order_detail',
            order_number=order.order_number,
        )

    if _open_action_exists(
        order,
        'return',
    ):
        messages.info(
            request,
            'برای این سفارش یک درخواست مرجوعی باز وجود دارد.',
        )
        return redirect(
            'customer_care:order_actions_home'
        )

    if request.method == 'POST':
        form = ReturnRequestForm(
            request.POST,
            order=order,
        )

        if form.is_valid():
            selected = form.cleaned_data[
                'selected_items'
            ]

            with transaction.atomic():
                locked_order = (
                    Order.objects
                    .select_for_update()
                    .get(
                        pk=order.pk,
                        user=request.user,
                    )
                )

                if (
                    locked_order.status
                    not in RETURN_ALLOWED_STATUSES
                ):
                    messages.error(
                        request,
                        (
                            'وضعیت سفارش تغییر کرده است؛ '
                            'مرجوعی دیگر قابل ثبت نیست.'
                        ),
                    )
                    return redirect(
                        'first:order_detail',
                        order_number=(
                            locked_order.order_number
                        ),
                    )

                if _open_action_exists(
                    locked_order,
                    'return',
                ):
                    messages.info(
                        request,
                        (
                            'برای این سفارش یک درخواست '
                            'مرجوعی باز وجود دارد.'
                        ),
                    )
                    return redirect(
                        'customer_care:order_actions_home'
                    )

                try:
                    selected = (
                        _locked_return_selection(
                            locked_order,
                            selected,
                        )
                    )
                except ValueError as exc:
                    messages.error(
                        request,
                        str(exc),
                    )
                    return redirect(
                        'first:order_detail',
                        order_number=(
                            locked_order.order_number
                        ),
                    )

                action = form.save(
                    commit=False
                )
                action.user = request.user
                action.order = locked_order
                action.kind = 'return'

                refund_amount = Decimal('0')

                for item, quantity in selected:
                    refund_amount += (
                        item.price * quantity
                    )

                action.refund_amount = (
                    refund_amount
                )
                action.save()

                for item, quantity in selected:
                    OrderActionItem.objects.create(
                        request=action,
                        order_item=item,
                        quantity=quantity,
                        unit_amount=item.price,
                    )

            messages.success(
                request,
                'درخواست مرجوعی ثبت شد.',
            )

            return redirect(
                'customer_care:order_action_detail',
                pk=action.pk,
            )
    else:
        form = ReturnRequestForm(
            order=order
        )

    return render(
        request,
        'customer_care/return_request.html',
        {
            'form': form,
            'order': order,
        },
    )


@permission_required(
    'support_view',
    redirect_url='first:admin_dashboard',
)
def admin_support_list(request):
    tickets = (
        SupportTicket.objects
        .select_related(
            'user',
            'order',
        )
        .all()
    )

    status = request.GET.get(
        'status'
    )

    if status:
        tickets = tickets.filter(
            status=status
        )

    return render(
        request,
        'customer_care/admin_support_list.html',
        {
            'tickets': tickets,
            'statuses': SupportTicket.STATUS_CHOICES,
        },
    )


@permission_required(
    'support_view',
    redirect_url='first:admin_dashboard',
)
def admin_support_detail(
    request,
    reference,
):
    ticket = get_object_or_404(
        SupportTicket.objects
        .select_related(
            'user',
            'order',
        ),
        reference=reference,
    )

    return render(
        request,
        'customer_care/admin_support_detail.html',
        {
            'ticket': ticket,
            'message_form': SupportMessageForm(),
        },
    )


@permission_required(
    'support_reply',
    redirect_url='first:admin_dashboard',
)
@require_POST
def admin_support_reply(
    request,
    reference,
):
    ticket = get_object_or_404(
        SupportTicket,
        reference=reference,
    )

    form = SupportMessageForm(
        request.POST
    )

    if form.is_valid():
        SupportMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            body=form.cleaned_data['body'],
            is_staff_reply=True,
        )

        ticket.status = 'answered'
        ticket.save(
            update_fields=[
                'status',
                'updated_at',
            ]
        )

        messages.success(
            request,
            'پاسخ پشتیبانی ارسال شد.',
        )

    return redirect(
        'customer_care:admin_support_detail',
        reference=ticket.reference,
    )


@permission_required(
    'support_reply',
    redirect_url='first:admin_dashboard',
)
@require_POST
def admin_support_status(
    request,
    reference,
):
    ticket = get_object_or_404(
        SupportTicket,
        reference=reference,
    )

    new_status = request.POST.get(
        'status'
    )

    valid_statuses = {
        value
        for value, _ in SupportTicket.STATUS_CHOICES
    }

    if new_status not in valid_statuses:
        raise Http404

    ticket.status = new_status

    if new_status == 'closed':
        ticket.closed_at = timezone.now()
    else:
        ticket.closed_at = None

    ticket.save(
        update_fields=[
            'status',
            'closed_at',
            'updated_at',
        ]
    )

    return redirect(
        'customer_care:admin_support_detail',
        reference=ticket.reference,
    )


@permission_required(
    'returns_manage',
    redirect_url='first:admin_dashboard',
)
def admin_order_actions_list(request):
    actions = (
        OrderActionRequest.objects
        .select_related(
            'user',
            'order',
        )
        .prefetch_related(
            'items__order_item'
        )
    )

    return render(
        request,
        'customer_care/admin_order_actions_list.html',
        {
            'actions': actions,
        },
    )


@permission_required(
    'returns_manage',
    redirect_url='first:admin_dashboard',
)
def admin_order_action_detail(
    request,
    pk,
):
    action = get_object_or_404(
        OrderActionRequest.objects
        .select_related(
            'user',
            'order',
        )
        .prefetch_related(
            'items__order_item'
        ),
        pk=pk,
    )

    return render(
        request,
        'customer_care/admin_order_action_detail.html',
        {
            'action': action,
            'status_form': AdminActionStatusForm(
                initial={
                    'status': action.status,
                    'admin_note': action.admin_note,
                }
            ),
        },
    )


@permission_required(
    'returns_manage',
    redirect_url='first:admin_dashboard',
)
@require_POST
def admin_order_action_update(
    request,
    pk,
):
    action = get_object_or_404(
        OrderActionRequest.objects
        .select_related('order'),
        pk=pk,
    )

    form = AdminActionStatusForm(
        request.POST
    )

    if not form.is_valid():
        messages.error(
            request,
            'وضعیت انتخاب‌شده معتبر نیست.',
        )
        return redirect(
            'customer_care:admin_order_action_detail',
            pk=action.pk,
        )

    new_status = form.cleaned_data['status']

    transitions = {
        'cancel': {
            'pending': {'approved', 'rejected'},
            'approved': {'refund_pending', 'closed'},
            'refund_pending': {'refunded'},
            'refunded': {'closed'},
            'rejected': {'closed'},
            'closed': set(),
        },
        'return': {
            'pending': {'approved', 'rejected'},
            'approved': {'received', 'closed'},
            'received': {'refund_pending', 'closed'},
            'refund_pending': {'refunded'},
            'refunded': {'closed'},
            'rejected': {'closed'},
            'closed': set(),
        },
    }

    allowed = (
        transitions
        .get(action.kind, {})
        .get(action.status, set())
    )

    if (
        new_status != action.status
        and new_status not in allowed
    ):
        messages.error(
            request,
            (
                'این تغییر وضعیت مجاز نیست. '
                'مراحل لغو/مرجوعی باید به ترتیب انجام شوند.'
            ),
        )
        return redirect(
            'customer_care:admin_order_action_detail',
            pk=action.pk,
        )

    with transaction.atomic():
        action = (
            OrderActionRequest.objects
            .select_for_update()
            .select_related('order')
            .get(pk=action.pk)
        )

        old_status = action.status

        action.status = new_status
        action.admin_note = (
            form.cleaned_data[
                'admin_note'
            ]
        )

        if new_status in {
            'rejected',
            'refunded',
            'closed',
        }:
            action.resolved_at = timezone.now()

        action.save(
            update_fields=[
                'status',
                'admin_note',
                'resolved_at',
                'updated_at',
            ]
        )

        if (
            action.kind == 'cancel'
            and old_status != 'approved'
            and new_status == 'approved'
        ):
            _restore_stock_for_action(action)

            order = action.order
            order.status = 'cancelled'
            order.save(
                update_fields=[
                    'status',
                    'updated_at',
                ]
            )

        elif (
            action.kind == 'return'
            and old_status != 'received'
            and new_status == 'received'
        ):
            _restore_stock_for_action(action)

        if new_status == 'refunded':
            if action.kind == 'cancel':
                order = action.order
                order.status = 'refunded'
                order.save(
                    update_fields=[
                        'status',
                        'updated_at',
                    ]
                )

            elif action.kind == 'return':
                requested = {
                    item.order_item_id:
                    item.quantity
                    for item
                    in action.items.all()
                }

                complete = all(
                    requested.get(
                        item.pk,
                        0,
                    ) >= item.quantity
                    for item
                    in action.order.items.all()
                )

                if complete:
                    order = action.order
                    order.status = 'refunded'
                    order.save(
                        update_fields=[
                            'status',
                            'updated_at',
                        ]
                    )

    messages.success(
        request,
        'وضعیت درخواست به‌روزرسانی شد.',
    )

    return redirect(
        'customer_care:admin_order_action_detail',
        pk=action.pk,
    )
