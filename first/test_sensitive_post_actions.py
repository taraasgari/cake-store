from django.test import TestCase
from django.urls import reverse

from .models import (
    Cart,
    CartItem,
    Product,
    ProductReview,
    SiteSettings,
    User,
)


class SensitivePostOnlyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='post-user',
            email='post-user@example.com',
            phone='09125555551',
            password='StrongPass123!',
        )

        self.owner = User.objects.create_user(
            username='post-owner',
            email='post-owner@example.com',
            phone='09125555552',
            password='StrongPass123!',
            role='owner',
            is_staff=True,
            is_superuser=True,
        )

        self.product = Product.objects.create(
            name='Protected product',
            slug='protected-product-post',
            price=100000,
            stock=5,
            main_image='products/test.webp',
        )

    def test_remove_cart_get_is_rejected(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1,
            price=self.product.price,
        )

        self.client.force_login(self.user)
        response = self.client.get(
            reverse('first:remove_from_cart', args=[item.pk])
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(CartItem.objects.filter(pk=item.pk).exists())

    def test_remove_cart_post_works(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1,
            price=self.product.price,
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse('first:remove_from_cart', args=[item.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_clear_cart_get_is_rejected(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1,
            price=self.product.price,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('first:clear_cart'))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(cart.items.exists())

    def test_product_delete_get_is_rejected(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse('first:admin_delete_product', args=[self.product.pk])
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

    def test_product_delete_post_works_for_owner(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('first:admin_delete_product', args=[self.product.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)
        self.assertFalse(self.product.is_available)

    def test_review_verify_get_is_rejected(self):
        review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            comment='test',
            is_verified=False,
        )

        self.client.force_login(self.owner)
        response = self.client.get(
            reverse('first:review_verify', args=[review.pk])
        )

        self.assertEqual(response.status_code, 405)
        review.refresh_from_db()
        self.assertFalse(review.is_verified)

    def test_make_admin_get_is_rejected(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse('first:make_admin', args=[self.user.pk])
        )

        self.assertEqual(response.status_code, 405)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'user')

    def test_reset_settings_get_is_rejected(self):
        SiteSettings.get_settings()
        self.client.force_login(self.owner)
        response = self.client.get(reverse('first:reset_site_settings'))
        self.assertEqual(response.status_code, 405)
