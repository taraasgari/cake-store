from django.test import TestCase
from django.urls import reverse

from first.models import (
    AdminPermission,
    Order,
    OrderItem,
    Product,
    User,
)

from .models import (
    OrderActionItem,
    OrderActionRequest,
    SupportMessage,
    SupportTicket,
)


class CustomerCareTests(TestCase):
    def setUp(self):
        self.password = 'StrongPass123!'

        self.user = User.objects.create_user(
            username='user-one',
            email='one@example.com',
            phone='09120000001',
            password=self.password,
        )
        self.other = User.objects.create_user(
            username='user-two',
            email='two@example.com',
            phone='09120000002',
            password=self.password,
        )
        self.owner = User.objects.create_user(
            username='owner-care',
            email='owner-care@example.com',
            phone='09120000003',
            password=self.password,
            role='owner',
            is_staff=True,
            is_superuser=True,
        )

        self.order = Order.objects.create(
            user=self.user,
            order_number='12345678',
            subtotal=100000,
            discount=0,
            shipping_cost=0,
            total=100000,
            address='تهران',
            postal_code='1234567890',
            phone='09120000001',
            status='processing',
            payment_method='online',
            is_paid=True,
        )

    def test_order_tracking_requires_code_and_phone_match(self):
        response = self.client.post(
            reverse(
                'customer_care:order_tracking'
            ),
            {
                'order_number': '12345678',
                'phone': '09120000002',
            },
        )
        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertIsNone(
            response.context['order']
        )

        response = self.client.post(
            reverse(
                'customer_care:order_tracking'
            ),
            {
                'order_number': '12345678',
                'phone': '09120000001',
            },
        )
        self.assertEqual(
            response.context['order'].pk,
            self.order.pk,
        )

    def test_user_can_create_support_ticket(self):
        self.client.force_login(
            self.user
        )

        response = self.client.post(
            reverse(
                'customer_care:support_create'
            ),
            {
                'subject': 'سؤال درباره سفارش',
                'order': self.order.pk,
                'priority': 'normal',
                'body': 'سلام، سفارش من چه زمانی ارسال می‌شود؟',
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )
        ticket = SupportTicket.objects.get(
            user=self.user
        )
        self.assertEqual(
            ticket.order_id,
            self.order.pk,
        )
        self.assertEqual(
            ticket.messages.count(),
            1,
        )

    def test_user_cannot_read_another_users_ticket(self):
        ticket = SupportTicket.objects.create(
            user=self.other,
            subject='private',
        )

        self.client.force_login(
            self.user
        )

        response = self.client.get(
            reverse(
                'customer_care:support_detail',
                kwargs={
                    'reference': ticket.reference,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_cancel_request_requires_post_and_eligible_state(self):
        self.client.force_login(
            self.user
        )

        url = reverse(
            'customer_care:cancel_order_request',
            kwargs={
                'order_number': self.order.order_number,
            },
        )

        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            405,
        )

        response = self.client.post(
            url,
            {
                'reason': 'changed_mind',
                'description': 'انصراف',
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )
        self.assertTrue(
            OrderActionRequest.objects.filter(
                order=self.order,
                kind='cancel',
                status='pending',
            ).exists()
        )

    def test_owner_can_answer_support(self):
        ticket = SupportTicket.objects.create(
            user=self.user,
            subject='help',
        )

        self.client.force_login(
            self.owner
        )

        response = self.client.post(
            reverse(
                'customer_care:admin_support_reply',
                kwargs={
                    'reference': ticket.reference,
                },
            ),
            {
                'body': 'پاسخ مدیریت',
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )
        self.assertTrue(
            SupportMessage.objects.filter(
                ticket=ticket,
                is_staff_reply=True,
            ).exists()
        )

    def test_approved_cancel_restores_stock_only_once(self):
        product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price=100000,
            stock=2,
            sales_count=1,
            main_image='products/test.jpg',
        )

        OrderItem.objects.create(
            order=self.order,
            product=product,
            product_name=product.name,
            price=100000,
            quantity=1,
            total=100000,
        )

        action = OrderActionRequest.objects.create(
            user=self.user,
            order=self.order,
            kind='cancel',
            reason='changed_mind',
            refund_amount=100000,
        )

        self.client.force_login(
            self.owner
        )

        url = reverse(
            'customer_care:admin_order_action_update',
            kwargs={
                'pk': action.pk,
            },
        )

        for _ in range(2):
            response = self.client.post(
                url,
                {
                    'status': 'approved',
                    'admin_note': '',
                },
            )
            self.assertEqual(
                response.status_code,
                302,
            )

        product.refresh_from_db()

        self.assertEqual(
            product.stock,
            3,
        )
        self.assertEqual(
            product.sales_count,
            0,
        )

    def test_return_revalidation_blocks_cumulative_over_return(self):
        from customer_care.views import (
            _locked_return_selection,
        )
        from django.db import transaction

        self.order.status = 'delivered'
        self.order.save(
            update_fields=['status']
        )

        product = Product.objects.create(
            name='Return Product',
            slug='return-product',
            price=50000,
            stock=5,
            sales_count=2,
            main_image='products/return.jpg',
        )

        order_item = OrderItem.objects.create(
            order=self.order,
            product=product,
            product_name=product.name,
            price=50000,
            quantity=2,
            total=100000,
        )

        previous = OrderActionRequest.objects.create(
            user=self.user,
            order=self.order,
            kind='return',
            reason='changed_mind',
            status='closed',
            refund_amount=50000,
        )

        OrderActionItem.objects.create(
            request=previous,
            order_item=order_item,
            quantity=1,
            unit_amount=50000,
        )

        with transaction.atomic():
            locked_order = (
                Order.objects
                .select_for_update()
                .get(pk=self.order.pk)
            )

            with self.assertRaises(ValueError):
                _locked_return_selection(
                    locked_order,
                    [(order_item, 2)],
                )

            accepted = _locked_return_selection(
                locked_order,
                [(order_item, 1)],
            )

        self.assertEqual(
            accepted[0][1],
            1,
        )
