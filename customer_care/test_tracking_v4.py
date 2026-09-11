from django.test import TestCase
from django.urls import reverse

from first.models import Order, User


class TrackingV4Tests(TestCase):
    def setUp(self):
        self.password = 'StrongPass123!'

        self.user = User.objects.create_user(
            username='tracking-v4-user',
            email='tracking-v4@example.com',
            phone='09125556661',
            password=self.password,
        )

        self.other = User.objects.create_user(
            username='tracking-v4-other',
            email='tracking-v4-other@example.com',
            phone='09125556662',
            password=self.password,
        )

        self.order = Order.objects.create(
            user=self.user,
            order_number='12344321',
            subtotal=100000,
            discount=0,
            shipping_cost=0,
            total=100000,
            address='Tehran',
            postal_code='1234567890',
            phone=self.user.phone,
            status='processing',
            payment_method='online',
            is_paid=True,
        )

        self.other_order = Order.objects.create(
            user=self.other,
            order_number='87655678',
            subtotal=100000,
            discount=0,
            shipping_cost=0,
            total=100000,
            address='Tehran',
            postal_code='1234567890',
            phone=self.other.phone,
            status='processing',
            payment_method='online',
            is_paid=True,
        )

    def test_logged_in_user_can_track_with_code_only(self):
        self.client.force_login(
            self.user
        )

        response = self.client.post(
            reverse(
                'customer_care:order_tracking'
            ),
            {
                'order_number': '۱۲۳۴۴۳۲۱',
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.context[
                'order'
            ].pk,
            self.order.pk,
        )

    def test_logged_in_user_cannot_track_another_users_order(self):
        self.client.force_login(
            self.user
        )

        response = self.client.post(
            reverse(
                'customer_care:order_tracking'
            ),
            {
                'order_number': (
                    self.other_order.order_number
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIsNone(
            response.context[
                'order'
            ]
        )

    def test_public_tracking_still_requires_matching_phone(self):
        response = self.client.post(
            reverse(
                'customer_care:order_tracking'
            ),
            {
                'order_number': (
                    self.order.order_number
                ),
                'phone': '09120000000',
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIsNone(
            response.context[
                'order'
            ]
        )
