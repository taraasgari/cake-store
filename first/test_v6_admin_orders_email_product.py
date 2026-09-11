import json

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import (
    TestCase,
    override_settings,
)
from django.urls import reverse

from .models import (
    AdminPermission,
    Color,
    Order,
)


User = get_user_model()


class V6PermissionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner-v6',
            email='owner-v6@example.com',
            phone='09126660001',
            password='StrongPass123!',
            role='owner',
            is_staff=True,
            is_superuser=True,
        )

        User.objects.create_user(
            username='admin-v6',
            email='admin-v6@example.com',
            phone='09126660002',
            password='StrongPass123!',
            role='admin',
            is_staff=True,
        )

        self.client.force_login(self.owner)

    def test_support_and_returns_permissions_exist(self):
        response = self.client.get(
            reverse(
                'first:manage_admin_permissions'
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'پشتیبانی')
        self.assertContains(
            response,
            'لغو و مرجوعی',
        )

        for name in (
            'support_view',
            'support_reply',
            'returns_manage',
        ):
            self.assertTrue(
                AdminPermission.objects.filter(
                    name=name,
                    is_active=True,
                ).exists()
            )


class V6OrderTrackingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='order-v6',
            email='order-v6@example.com',
            phone='09126660003',
            password='StrongPass123!',
        )

        self.order = Order.objects.create(
            user=self.user,
            order_number='42587508',
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

        self.client.force_login(self.user)

    def test_persian_code_returns_status(self):
        response = self.client.get(
            reverse('first:user_orders'),
            {'order_code': '۴۲۵۸۷۵۰۸'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context[
                'tracked_order'
            ].pk,
            self.order.pk,
        )
        self.assertContains(
            response,
            self.order.get_status_display(),
        )


class V6ColorTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='color-v6',
            email='color-v6@example.com',
            phone='09126660004',
            password='StrongPass123!',
            role='owner',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.owner)

    def test_get_rejected(self):
        response = self.client.get(
            reverse('first:ajax_add_color')
        )
        self.assertEqual(response.status_code, 405)

    def test_invalid_hex_rejected(self):
        response = self.client.post(
            reverse('first:ajax_add_color'),
            data=json.dumps(
                {
                    'name': 'Bad',
                    'code': 'red',
                }
            ),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_duplicate_returns_existing(self):
        color = Color.objects.create(
            name='Rose',
            code='#FF0066',
            is_active=True,
        )

        response = self.client.post(
            reverse('first:ajax_add_color'),
            data=json.dumps(
                {
                    'name': 'rose',
                    'code': '#ff0066',
                }
            ),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['id'],
            color.pk,
        )


@override_settings(
    EMAIL_BACKEND=(
        'django.core.mail.backends.'
        'locmem.EmailBackend'
    ),
    DEFAULT_FROM_EMAIL='noreply@test.local',
)
class V6EmailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='mail-v6',
            email='mail-v6@example.com',
            phone='09126660005',
            password='StrongPass123!',
        )

    def test_reset_sends_one_message(self):
        response = self.client.post(
            reverse('first:forgot_password'),
            {'email': self.user.email},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
