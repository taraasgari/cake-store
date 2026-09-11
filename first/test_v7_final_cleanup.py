import ast
from decimal import Decimal
from pathlib import Path

from django.db import models
from django.test import TestCase
from django.urls import reverse

from .models import (
    AdminPermission,
    AdminUserPermission,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Product,
    SiteSettings,
    User,
)


class V7StructureTests(TestCase):
    def test_no_shadowed_top_level_views(self):
        source = (
            Path(__file__)
            .with_name('views.py')
            .read_text(
                encoding='utf-8'
            )
        )

        tree = ast.parse(source)
        names = []

        for node in tree.body:
            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):
                names.append(node.name)

        duplicates = sorted({
            name
            for name in names
            if names.count(name) > 1
        })

        self.assertEqual(
            duplicates,
            [],
        )

    def test_order_history_uses_set_null(self):
        self.assertIs(
            OrderItem._meta.get_field(
                'product'
            ).remote_field.on_delete,
            models.SET_NULL,
        )

        self.assertIs(
            OrderItem._meta.get_field(
                'variant'
            ).remote_field.on_delete,
            models.SET_NULL,
        )


class V7SecurityTests(TestCase):
    def setUp(self):
        self.user = (
            User.objects.create_user(
                username='v7-user',
                email='v7-user@example.com',
                phone='09127770001',
                password='StrongPass123!',
            )
        )

        self.owner = (
            User.objects.create_user(
                username='v7-owner',
                email='v7-owner@example.com',
                phone='09127770002',
                password='StrongPass123!',
                role='owner',
                is_staff=True,
            )
        )

    def test_number_toggle_is_owner_post_only(self):
        site = SiteSettings.get_settings()
        original = site.number_format

        self.client.force_login(
            self.user
        )

        response = self.client.post(
            reverse(
                'first:toggle_number_format'
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        site.refresh_from_db()

        self.assertEqual(
            site.number_format,
            original,
        )

        self.client.force_login(
            self.owner
        )

        response = self.client.get(
            reverse(
                'first:toggle_number_format'
            )
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_owner_password_uses_validators(self):
        self.client.force_login(
            self.owner
        )

        response = self.client.post(
            reverse(
                'first:owner_change_password'
            ),
            {
                'old_password': (
                    'StrongPass123!'
                ),
                'new_password': '123456',
                'confirm_password': '123456',
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.owner.refresh_from_db()

        self.assertFalse(
            self.owner.check_password(
                '123456'
            )
        )

    def test_bad_cart_quantity_is_safe(self):
        product = Product.objects.create(
            name='Cart product',
            slug='v7-cart-product',
            price=Decimal('10000'),
            stock=5,
            is_available=True,
            main_image=(
                'products/test.webp'
            ),
        )

        cart = Cart.objects.create(
            user=self.user
        )

        item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1,
            price=product.price,
        )

        self.client.force_login(
            self.user
        )

        response = self.client.post(
            reverse(
                'first:update_cart_item',
                args=[item.pk],
            ),
            {
                'quantity': (
                    'not-a-number'
                )
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )


class V7OrderTests(TestCase):
    def setUp(self):
        self.admin = (
            User.objects.create_user(
                username='v7-admin',
                email='v7-admin@example.com',
                phone='09127770003',
                password='StrongPass123!',
                role='admin',
                is_staff=True,
            )
        )

        self.customer = (
            User.objects.create_user(
                username='v7-customer',
                email='v7-customer@example.com',
                phone='09127770004',
                password='StrongPass123!',
            )
        )

        update_permission = (
            AdminPermission.objects.create(
                name='orders_update',
                label='Update orders',
                is_active=True,
            )
        )

        delete_permission = (
            AdminPermission.objects.create(
                name='products_delete',
                label='Delete products',
                is_active=True,
            )
        )

        for permission in (
            update_permission,
            delete_permission,
        ):
            AdminUserPermission.objects.create(
                user=self.admin,
                permission=permission,
                is_allowed=True,
            )

        self.product = Product.objects.create(
            name='V7 product',
            slug='v7-product',
            price=Decimal('50000'),
            stock=5,
            is_available=True,
            main_image=(
                'products/test.webp'
            ),
        )

    def make_order(self, status='pending'):
        return Order.objects.create(
            user=self.customer,
            subtotal=Decimal('50000'),
            total=Decimal('50000'),
            address='Tehran',
            postal_code='1234567890',
            phone='09127770004',
            payment_method='cash',
            status=status,
        )

    def test_invalid_status_jump_is_rejected(self):
        order = self.make_order()

        self.client.force_login(
            self.admin
        )

        response = self.client.post(
            reverse(
                'first:update_order_status',
                args=[order.pk],
            ),
            {'status': 'delivered'},
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            'pending',
        )

    def test_product_deactivation_preserves_order_item(self):
        order = self.make_order(
            status='processing'
        )

        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=(
                self.product.name
            ),
            price=self.product.price,
            quantity=1,
            total=self.product.price,
        )

        self.client.force_login(
            self.admin
        )

        response = self.client.post(
            reverse(
                'first:admin_delete_product',
                args=[self.product.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.product.refresh_from_db()
        item.refresh_from_db()

        self.assertFalse(
            self.product.is_active
        )

        self.assertEqual(
            item.product_id,
            self.product.pk,
        )


class V7CheckoutAndCounterTests(TestCase):
    def setUp(self):
        self.user = (
            User.objects.create_user(
                username='v7-shopper',
                email='v7-shopper@example.com',
                phone='09127770005',
                password='StrongPass123!',
            )
        )

    def test_product_views_increment(self):
        product = Product.objects.create(
            name='View product',
            slug='view-product',
            price=Decimal('10000'),
            stock=1,
            is_available=True,
            main_image=(
                'products/test.webp'
            ),
        )

        self.client.get(
            reverse(
                'first:product_detail',
                args=[product.slug],
            )
        )

        product.refresh_from_db()

        self.assertEqual(
            product.views_count,
            1,
        )

    def test_online_checkout_rejected_without_gateway(self):
        product = Product.objects.create(
            name='Gateway product',
            slug='gateway-product',
            price=Decimal('10000'),
            stock=2,
            is_available=True,
            main_image=(
                'products/test.webp'
            ),
        )

        cart = Cart.objects.create(
            user=self.user
        )

        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1,
            price=product.price,
        )

        self.client.force_login(
            self.user
        )

        response = self.client.post(
            reverse('first:checkout'),
            {
                'address': 'Tehran',
                'postal_code': (
                    '1234567890'
                ),
                'phone': '09127770005',
                'payment_method': 'online',
                'note': '',
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertFalse(
            Order.objects.filter(
                user=self.user
            ).exists()
        )
