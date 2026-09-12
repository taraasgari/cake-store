from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .models import Product, User


class SecurityV3Tests(TestCase):
    def setUp(self):
        cache.clear()

        self.password = 'StrongPass123!'

        self.user = User.objects.create_user(
            username='security-v3-user',
            email='security-v3@example.com',
            phone='09127770001',
            password=self.password,
        )

        self.product = Product.objects.create(
            name='Security V3 Product',
            slug='security-v3-product',
            price=100000,
            stock=5,
            main_image='products/security-v3.webp',
        )

    def test_logout_get_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('first:logout')
        )
        self.assertEqual(response.status_code, 405)

    def test_logout_post_works(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('first:logout')
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(
            '_auth_user_id',
            self.client.session,
        )

    def test_add_to_cart_get_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                'first:add_to_cart',
                args=[self.product.pk],
            )
        )
        self.assertEqual(response.status_code, 405)

    def test_wishlist_add_get_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                'first:add_to_wishlist',
                args=[self.product.pk],
            )
        )
        self.assertEqual(response.status_code, 405)

    def test_external_login_redirect_is_blocked(self):
        response = self.client.post(
            reverse('first:login')
            + '?next=https://evil.example/phish',
            {
                'username': self.user.username,
                'password': self.password,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(
            response.url,
            'https://evil.example/phish',
        )

    def test_bad_logins_are_throttled(self):
        url = reverse('first:login')
        last_response = None

        for _ in range(9):
            last_response = self.client.post(
                url,
                {
                    'username': self.user.username,
                    'password': 'wrong-password',
                },
            )

        self.assertEqual(
            last_response.status_code,
            429,
        )
