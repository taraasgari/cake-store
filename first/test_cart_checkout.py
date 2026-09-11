from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    Product,
    ProductVariant,
    User,
)


class CartPricingRegressionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='cart-test-user',
            email='cart-test@example.com',
            phone='09121111111',
            password='StrongPass123!',
        )

    def test_simple_product_discount_is_not_applied_twice(self):
        product = Product.objects.create(
            name='Discounted product',
            slug='discounted-product',
            price=Decimal('100000'),
            discount_price=Decimal('80000'),
            stock=5,
            main_image='products/test.webp',
        )
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1,
            price=Decimal('80000'),
        )

        self.assertEqual(
            cart.total_price,
            Decimal('100000'),
        )
        self.assertEqual(
            cart.total_discount,
            Decimal('20000'),
        )
        self.assertEqual(
            cart.final_price,
            Decimal('80000'),
        )

    def test_variant_discount_is_not_applied_twice(self):
        product = Product.objects.create(
            name='Variant product',
            slug='variant-product',
            price=Decimal('100000'),
            stock=0,
            has_variants=True,
            main_image='products/test.webp',
        )
        variant = ProductVariant.objects.create(
            product=product,
            price=Decimal('120000'),
            discount_price=Decimal('90000'),
            stock=5,
            is_active=True,
            is_default=True,
        )
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variant,
            quantity=2,
            price=Decimal('90000'),
        )

        self.assertEqual(
            cart.total_price,
            Decimal('240000'),
        )
        self.assertEqual(
            cart.total_discount,
            Decimal('60000'),
        )
        self.assertEqual(
            cart.final_price,
            Decimal('180000'),
        )


class CheckoutRegressionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='checkout-test-user',
            email='checkout-test@example.com',
            phone='09122222222',
            password='StrongPass123!',
        )
        self.client.force_login(self.user)

    def checkout_payload(self):
        return {
            'address': 'Tehran, Test Street 1',
            'postal_code': '1234567890',
            'phone': '09122222222',
            'payment_method': 'cash',
            'note': '',
        }

    def test_checkout_uses_correct_discounted_total(self):
        product = Product.objects.create(
            name='Checkout product',
            slug='checkout-product',
            price=Decimal('100000'),
            discount_price=Decimal('80000'),
            stock=3,
            main_image='products/test.webp',
        )
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1,
            price=Decimal('80000'),
        )

        response = self.client.post(
            reverse('first:checkout'),
            self.checkout_payload(),
        )
        self.assertEqual(response.status_code, 302)

        order = Order.objects.get(user=self.user)
        self.assertEqual(
            order.subtotal,
            Decimal('100000'),
        )
        self.assertEqual(
            order.discount,
            Decimal('20000'),
        )
        self.assertEqual(
            order.total,
            Decimal('80000'),
        )

        order_item = OrderItem.objects.get(order=order)
        self.assertEqual(
            order_item.price,
            Decimal('80000'),
        )
        self.assertEqual(
            order_item.total,
            Decimal('80000'),
        )

        product.refresh_from_db()
        self.assertEqual(product.stock, 2)
        self.assertEqual(product.sales_count, 1)
        self.assertFalse(
            CartItem.objects.filter(cart=cart).exists()
        )

    def test_checkout_rechecks_stock_before_order(self):
        product = Product.objects.create(
            name='Low stock product',
            slug='low-stock-product',
            price=Decimal('50000'),
            stock=1,
            main_image='products/test.webp',
        )
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2,
            price=Decimal('50000'),
        )

        response = self.client.post(
            reverse('first:checkout'),
            self.checkout_payload(),
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Order.objects.filter(user=self.user).exists()
        )

        product.refresh_from_db()
        self.assertEqual(product.stock, 1)
        self.assertTrue(
            CartItem.objects.filter(cart=cart).exists()
        )
