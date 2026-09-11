from django.test import TestCase
from django.urls import reverse

from .models import Order, User


class AccountOrdersV4Tests(TestCase):
    def setUp(self):
        self.password = 'StrongPass123!'

        self.user = User.objects.create_user(
            username='orders-v4-user',
            email='orders-v4@example.com',
            phone='09123334441',
            password=self.password,
        )

        self.other = User.objects.create_user(
            username='orders-v4-other',
            email='orders-v4-other@example.com',
            phone='09123334442',
            password=self.password,
        )

        self.order = Order.objects.create(
            user=self.user,
            order_number='42857508',
            subtotal=200000,
            discount=0,
            shipping_cost=0,
            total=200000,
            address='Tehran',
            postal_code='1234567890',
            phone=self.user.phone,
            status='processing',
            payment_method='online',
            is_paid=True,
        )

        self.other_order = Order.objects.create(
            user=self.other,
            order_number='99999999',
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

        self.client.force_login(self.user)

    def test_order_code_search_finds_own_order(self):
        response = self.client.get(
            reverse('first:user_orders'),
            {
                'order_code': '۴۲۸۵۷۵۰۸',
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            '42857508',
        )

    def test_order_code_search_does_not_leak_other_users_order(self):
        response = self.client.get(
            reverse('first:user_orders'),
            {
                'order_code': '99999999',
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertNotContains(
            response,
            '#99999999',
        )

    def test_order_detail_only_allows_owner(self):
        response = self.client.get(
            reverse(
                'first:order_detail',
                args=[
                    self.other_order.order_number
                ],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )
