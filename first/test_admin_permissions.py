from django.test import TestCase
from django.urls import reverse

from .decorators import (
    check_admin_permission,
    get_effective_admin_permissions,
)
from .models import (
    AdminPermission,
    AdminRole,
    AdminUserPermission,
    Product,
    User,
)


class AdminPermissionCoreTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='permission-admin',
            email='permission-admin@example.com',
            phone='09123333331',
            password='StrongPass123!',
            role='admin',
            is_staff=True,
        )

        self.owner = User.objects.create_user(
            username='permission-owner',
            email='permission-owner@example.com',
            phone='09123333332',
            password='StrongPass123!',
            role='owner',
            is_staff=True,
            is_superuser=True,
        )

        self.products_view = (
            AdminPermission.objects.create(
                name='products_view',
                label='مشاهده محصولات',
                is_active=True,
            )
        )

        self.products_delete = (
            AdminPermission.objects.create(
                name='products_delete',
                label='حذف محصولات',
                is_active=True,
            )
        )

    def test_admin_without_permission_is_denied(self):
        self.assertFalse(
            check_admin_permission(
                self.admin,
                'products_view',
            )
        )

    def test_direct_user_permission_allows(self):
        AdminUserPermission.objects.create(
            user=self.admin,
            permission=self.products_view,
            is_allowed=True,
        )

        self.assertTrue(
            check_admin_permission(
                self.admin,
                'products_view',
            )
        )

    def test_role_permission_allows(self):
        role = AdminRole.objects.create(
            name='product_manager',
            display_name='Product Manager',
            is_active=True,
        )

        role.permissions.add(
            self.products_view
        )

        self.admin.admin_roles.add(
            role
        )

        self.assertTrue(
            check_admin_permission(
                self.admin,
                'products_view',
            )
        )

    def test_explicit_deny_overrides_role(self):
        role = AdminRole.objects.create(
            name='product_manager',
            display_name='Product Manager',
            is_active=True,
        )

        role.permissions.add(
            self.products_view
        )

        self.admin.admin_roles.add(
            role
        )

        AdminUserPermission.objects.create(
            user=self.admin,
            permission=self.products_view,
            is_allowed=False,
        )

        self.assertFalse(
            check_admin_permission(
                self.admin,
                'products_view',
            )
        )

        self.assertNotIn(
            'products_view',
            get_effective_admin_permissions(
                self.admin
            ),
        )

    def test_inactive_permission_never_grants_access(self):
        self.products_view.is_active = False
        self.products_view.save(
            update_fields=[
                'is_active'
            ]
        )

        AdminUserPermission.objects.create(
            user=self.admin,
            permission=self.products_view,
            is_allowed=True,
        )

        self.assertFalse(
            check_admin_permission(
                self.admin,
                'products_view',
            )
        )

    def test_owner_always_has_access(self):
        self.assertTrue(
            check_admin_permission(
                self.owner,
                'products_delete',
            )
        )


class AdminPermissionViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='view-admin',
            email='view-admin@example.com',
            phone='09124444441',
            password='StrongPass123!',
            role='admin',
            is_staff=True,
        )

        self.owner = User.objects.create_user(
            username='view-owner',
            email='view-owner@example.com',
            phone='09124444442',
            password='StrongPass123!',
            role='owner',
            is_staff=True,
            is_superuser=True,
        )

        self.products_view = (
            AdminPermission.objects.create(
                name='products_view',
                label='مشاهده محصولات',
                is_active=True,
            )
        )

        self.products_delete = (
            AdminPermission.objects.create(
                name='products_delete',
                label='حذف محصولات',
                is_active=True,
            )
        )

    def test_direct_admin_url_is_blocked_without_permission(self):
        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse(
                'first:admin_products'
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse('first:home'),
        )

    def test_admin_url_works_with_permission(self):
        AdminUserPermission.objects.create(
            user=self.admin,
            permission=self.products_view,
            is_allowed=True,
        )

        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse(
                'first:admin_products'
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_owner_bypasses_admin_permission(self):
        self.client.force_login(
            self.owner
        )

        response = self.client.get(
            reverse(
                'first:admin_products'
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_delete_url_does_not_bypass_permission(self):
        product = Product.objects.create(
            name='Protected product',
            slug='protected-product',
            price=100000,
            stock=3,
            main_image='products/test.webp',
        )

        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse(
                'first:admin_delete_product',
                args=[product.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertTrue(
            Product.objects.filter(
                pk=product.pk
            ).exists()
        )
