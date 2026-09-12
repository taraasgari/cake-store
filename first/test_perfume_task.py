import io
import json
import tempfile

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Product, User, SliderImage, SiteSettings, Category, Brand, ProductType, Tag, AdminPermission, AdminUserPermission


class PerfumeTaskTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        self.addCleanup(self.media.cleanup)
        self.addCleanup(self.override.disable)
        self.owner = User.objects.create_user(username='owner-task', email='owner-task@example.com', phone='09121110000', role='owner')
        self.client.force_login(self.owner)

    def image(self):
        data = io.BytesIO()
        Image.new('RGB', (600, 600), 'white').save(data, 'PNG')
        return SimpleUploadedFile('perfume.png', data.getvalue(), content_type='image/png')

    def create_product(self, **extra):
        data = dict(name='Normal fragrance', price='100', stock='0', is_active='on', product_images=self.image())
        data.update(extra)
        return self.client.post(reverse('first:admin_add_product'), data)

    def test_normal_product_is_published_and_latest_with_zero_stock(self):
        self.assertEqual(self.create_product().status_code, 302)
        product = Product.objects.get()
        self.assertTrue(product.is_active)
        self.assertTrue(product.slug)
        self.assertContains(self.client.get(reverse('first:product_list')), product.name)
        home = self.client.get(reverse('first:home'))
        self.assertIn(product, home.context['latest_products'])
        self.assertContains(home, product.get_absolute_url())
        product.is_available = False
        product.save()
        self.assertEqual(self.client.get(product.get_absolute_url()).status_code, 200)
        product.is_active = False
        product.save()
        self.assertEqual(self.client.get(product.get_absolute_url()).status_code, 404)

    def test_manual_product_slug_and_edit_links(self):
        self.create_product(slug='test-fragrance-100')
        product = Product.objects.get()
        self.assertEqual(product.slug, 'test-fragrance-100')
        self.create_product(slug='test-fragrance-100')
        self.assertEqual(Product.objects.values('slug').distinct().count(), Product.objects.count())
        response = self.client.post(reverse('first:admin_edit_product_site', args=[product.pk]), dict(name=product.name, slug='changed-fragrance', price='100', stock='0', is_active='on'))
        self.assertRedirects(response, '/product/changed-fragrance/')
        self.assertContains(self.client.get(reverse('first:home')), '/product/changed-fragrance/')
        self.assertEqual(self.client.get('/product/test-fragrance-100/').status_code, 404)

    def test_invalid_manual_slug_preserved(self):
        response = self.create_product(slug='bad/slug')
        self.assertFalse(Product.objects.exists())
        self.assertContains(response, 'bad/slug', status_code=400)

    def test_catalog_crud(self):
        for kind, model in [('category', Category), ('brand', Brand), ('product_type', ProductType), ('tag', Tag)]:
            with self.subTest(kind=kind):
                response = self.client.post(reverse('first:ajax_add_' + kind), json.dumps(dict(name='Scent', slug='scent')), content_type='application/json')
                self.assertEqual(response.status_code, 201, response.content)
                item = model.objects.get(pk=response.json()['id'])
                self.assertEqual(item.slug, 'scent')
                url = reverse('first:ajax_edit_' + kind, args=[item.pk])
                self.assertEqual(self.client.post(url, json.dumps(dict(name='Renamed')), content_type='application/json').status_code, 200)
                item.refresh_from_db()
                self.assertEqual(item.slug, 'scent')
                self.assertEqual(self.client.post(url, json.dumps(dict(name='Renamed', slug='new-scent')), content_type='application/json').status_code, 200)
                item.refresh_from_db()
                self.assertEqual(item.slug, 'new-scent')
                self.assertEqual(self.client.post(reverse('first:ajax_delete_' + kind, args=[item.pk])).status_code, 200)
                self.assertFalse(model.objects.filter(pk=item.pk).exists())

    def test_slider_fields_and_settings_isolation(self):
        site = SiteSettings.get_settings()
        site.site_name = 'Preserved perfume house'
        site.save()
        response = self.client.post(reverse('first:site_settings'), dict(slider_action='add_slider', slider_title='Campaign', slider_subtitle='Perfume subtitle', slider_button_text='Discover', slider_link='/products/', slider_order='2', slider_is_active='on', slider_image=self.image()))
        self.assertEqual(response.status_code, 302)
        site.refresh_from_db()
        self.assertEqual(site.site_name, 'Preserved perfume house')
        slider = SliderImage.objects.get()
        self.assertEqual(slider.subtitle, 'Perfume subtitle')
        page = self.client.get(reverse('first:home')).content.decode()
        top = page.split('data-home-slider', 1)[1].split('class="lux-home-hero"', 1)[0]
        self.assertIn('Campaign', top)
        self.assertIn(slider.image.url, top)
        self.assertEqual(top.count('data-home-slide='), 1)
        for n in range(4):
            SliderImage.objects.create(title=f'Slide {n}', image='slider/test.png', order=n)
        page = self.client.get(reverse('first:home')).content.decode()
        self.assertEqual(page.count('data-home-slide='), 5)
        self.assertEqual(page.count('data-home-slider-dot='), 5)
        SliderImage.objects.update(is_active=False)
        page = self.client.get(reverse('first:home')).content.decode()
        self.assertEqual(page.count('data-home-slide='), 1)
        self.assertIn('perfume-default-slider.png', page)
        self.assertNotIn('Campaign', page)

    def test_slider_validation(self):
        for values in [dict(slider_order='-1'), dict(slider_link='javascript:alert(1)'), dict(slider_title='x' * 201)]:
            response = self.client.post(reverse('first:site_settings'), dict(slider_action='add_slider', slider_image=self.image(), **values))
            self.assertEqual(response.status_code, 400)
            self.assertFalse(SliderImage.objects.exists())

    def test_admin_menu_and_granted_routes(self):
        user = User.objects.create_user(username='limited', email='limited@example.com', phone='09121110001', role='admin')
        permission, _ = AdminPermission.objects.get_or_create(name='products_view', defaults={'label': 'Products'})
        AdminUserPermission.objects.create(user=user, permission=permission, is_allowed=True)
        self.client.force_login(user)
        response = self.client.get(reverse('first:admin_products'))
        self.assertEqual(response.status_code, 200)
        for route in ['admin_orders', 'admin_users', 'site_settings', 'warehouse', 'analytics_dashboard']:
            self.assertNotContains(response, 'href="' + reverse('first:' + route) + '"')
            self.assertNotEqual(self.client.get(reverse('first:' + route)).status_code, 200)
        for permission_name, route in [('orders_view', 'admin_orders'), ('warehouse_view', 'warehouse'), ('site_settings', 'site_settings'), ('reports_view', 'analytics_dashboard')]:
            permission, _ = AdminPermission.objects.get_or_create(name=permission_name, defaults={'label': permission_name})
            AdminUserPermission.objects.create(user=user, permission=permission, is_allowed=True)
            self.assertEqual(self.client.get(reverse('first:' + route)).status_code, 200)
