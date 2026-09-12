from django.test import TestCase
from django.urls import reverse

from .models import User


class SafeRedirectTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='redirect-user',
            email='redirect@example.com',
            phone='09126666661',
            password='StrongPass123!',
        )

        self.owner = User.objects.create_user(
            username='redirect-owner',
            email='redirect-owner@example.com',
            phone='09126666662',
            password='StrongPass123!',
            role='owner',
            is_staff=True,
            is_superuser=True,
        )

    def test_login_allows_local_next(self):
        response = self.client.post(
            reverse('first:login') + '?next=/profile/',
            {
                'username': self.user.username,
                'password': 'StrongPass123!',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/profile/')

    def test_login_blocks_external_next(self):
        response = self.client.post(
            reverse('first:login')
            + '?next=https://evil.example/phish',
            {
                'username': self.user.username,
                'password': 'StrongPass123!',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('first:home'),
        )

    def test_login_blocks_scheme_relative_next(self):
        response = self.client.post(
            reverse('first:login')
            + '?next=//evil.example/phish',
            {
                'username': self.user.username,
                'password': 'StrongPass123!',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('first:home'),
        )

    def test_pdf_preview_blocks_external_return_to(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse('first:analytics_pdf_preview'),
            {
                'return_to': (
                    'https://evil.example/steal'
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['return_url'],
            reverse('first:analytics_dashboard'),
        )

    def test_pdf_preview_allows_local_return_to(self):
        self.client.force_login(self.owner)

        local_url = '/analytics/?period=30d'

        response = self.client.get(
            reverse('first:analytics_pdf_preview'),
            {
                'return_to': local_url,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['return_url'],
            local_url,
        )
