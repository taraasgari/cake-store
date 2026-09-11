from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import User


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@test.local',
)
class PasswordResetDeliveryV5Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='mail-v5-user',
            email='mail-v5@example.com',
            phone='09129990001',
            password='StrongPass123!',
        )

    def test_password_reset_sends_one_message(self):
        response = self.client.post(
            reverse('first:forgot_password'),
            {'email': self.user.email},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].to,
            [self.user.email],
        )
