from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import (
    AdminPermission,
    AdminUserPermission,
    Cart,
    CartItem,
    Product,
    ProductReview,
    User,
)


class V8PublicRobustnessTests(TestCase):
    def test_invalid_price_filters_do_not_500(self):
        Product.objects.create(
            name='Filter product',
            slug='filter-product',
            price=Decimal('10000'),
            stock=1,
            is_available=True,
            main_image='products/test.webp',
        )

        response = self.client.get(
            reverse('first:product_list'),
            {
                'min_price': 'bad',
                'max_price': '-50',
            },
        )

        self.assertEqual(response.status_code, 200)

    def test_discount_variant_without_own_price_does_not_500(self):
        from .models import Color, ProductVariant

        product = Product.objects.create(
            name='Variant discount product',
            slug='variant-discount-product',
            price=Decimal('10000'),
            stock=0,
            has_variants=True,
            is_available=True,
            main_image='products/test.webp',
        )

        color = Color.objects.create(
            name='Red V8',
            code='#FF0000',
        )

        ProductVariant.objects.create(
            product=product,
            color=color,
            price=None,
            discount_price=Decimal('9000'),
            stock=2,
            is_active=True,
        )

        response = self.client.get(
            reverse('first:discounts')
        )

        self.assertEqual(response.status_code, 200)


class V8AuthenticatedRobustnessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='v8-user',
            email='v8-user@example.com',
            phone='09126660001',
            password='StrongPass123!',
        )

        self.product = Product.objects.create(
            name='V8 product',
            slug='v8-product',
            price=Decimal('10000'),
            stock=5,
            is_available=True,
            main_image='products/test.webp',
        )

    def test_review_get_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                'first:add_review',
                args=[self.product.pk],
            )
        )

        self.assertEqual(response.status_code, 405)

    def test_bad_review_rating_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                'first:add_review',
                args=[self.product.pk],
            ),
            {
                'rating': '999',
                'comment': 'test',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ProductReview.objects.filter(
                user=self.user,
                product=self.product,
            ).exists()
        )

    def test_checkout_rejects_bad_phone(self):
        cart = Cart.objects.create(user=self.user)

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1,
            price=self.product.price,
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse('first:checkout'),
            {
                'address': 'Tehran valid address test',
                'postal_code': '1234567890',
                'phone': '123',
                'payment_method': 'cash',
                'note': '',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.user.orders.count(), 0)


class V8OwnerRobustnessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='v8-owner',
            email='v8-owner@example.com',
            phone='09126660002',
            password='StrongPass123!',
            role='owner',
            is_staff=True,
        )

        self.product = Product.objects.create(
            name='Owner stock product',
            slug='owner-stock-product',
            price=Decimal('10000'),
            stock=4,
            is_available=True,
            main_image='products/test.webp',
        )

    def test_negative_stock_is_rejected(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                'first:update_stock',
                args=[self.product.pk],
            ),
            {'stock': '-5'},
        )

        self.assertEqual(response.status_code, 302)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 4)

    def test_customizer_invalid_price_returns_400(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse('first:customizer_product_save'),
            {
                'name': 'Bad customizer product',
                'price': 'bad',
                'stock': '1',
            },
        )

        self.assertEqual(response.status_code, 400)


class V8AjaxCatalogTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='v8-admin',
            email='v8-admin@example.com',
            phone='09126660003',
            password='StrongPass123!',
            role='admin',
            is_staff=True,
        )

        permission = AdminPermission.objects.create(
            name='products_edit',
            label='Edit products',
            is_active=True,
        )

        AdminUserPermission.objects.create(
            user=self.admin,
            permission=permission,
            is_allowed=True,
        )

    def test_persian_category_gets_nonempty_slug(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('first:ajax_add_category'),
            data='{"name":"مراقبت پوست"}',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)

        from .models import Category

        category = Category.objects.get(
            name='مراقبت پوست'
        )

        self.assertTrue(category.slug)
