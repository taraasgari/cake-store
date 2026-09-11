from django.core import mail
from django.test import (
    TestCase,
    override_settings,
)
from django.urls import reverse

from .models import User


@override_settings(
    EMAIL_BACKEND=(
        'django.core.mail.backends.'
        'locmem.EmailBackend'
    ),
)
class PasswordResetEmailV4Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='mail-v4-user',
            email='mail-v4@example.com',
            phone='09124445551',
            password='StrongPass123!',
        )

    def test_forgot_password_sends_one_email(self):
        response = self.client.post(
            reverse('first:forgot_password'),
            {
                'email': self.user.email,
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        self.assertEqual(
            mail.outbox[0].to,
            [self.user.email],
        )
