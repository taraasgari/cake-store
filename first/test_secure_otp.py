from unittest.mock import patch

from django.contrib.auth.hashers import (
    check_password,
)
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import User


class SecureOTPTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='otp-user',
            email='otp@example.com',
            phone='09125555551',
            password='OldStrongPass123!',
        )

    @patch(
        'first.views._generate_otp',
        return_value='123456',
    )
    @patch('django.core.mail.EmailMultiAlternatives.send', return_value=1)
    def test_otp_is_hashed_not_stored_plaintext(
        self,
        mocked_send_mail,
        mocked_generate,
    ):
        response = self.client.post(
            reverse(
                'first:forgot_password'
            ),
            {
                'email': (
                    self.user.email
                )
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.user.refresh_from_db()

        self.assertNotEqual(
            self.user.otp_code,
            '123456',
        )

        self.assertTrue(
            check_password(
                '123456',
                self.user.otp_code,
            )
        )

        mocked_send_mail.assert_called_once()

    @patch(
        'first.views._generate_otp',
        return_value='123456',
    )
    @patch('django.core.mail.EmailMultiAlternatives.send', return_value=1)
    def test_resend_cooldown_blocks_immediate_second_send(
        self,
        mocked_send_mail,
        mocked_generate,
    ):
        self.client.post(
            reverse(
                'first:forgot_password'
            ),
            {'email': self.user.email},
        )

        response = self.client.post(
            reverse(
                'first:resend_otp'
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            mocked_send_mail.call_count,
            1,
        )

    @patch(
        'first.views._generate_otp',
        return_value='123456',
    )
    @patch('django.core.mail.EmailMultiAlternatives.send', return_value=1)
    def test_resend_get_is_not_allowed(
        self,
        mocked_send_mail,
        mocked_generate,
    ):
        self.client.post(
            reverse(
                'first:forgot_password'
            ),
            {'email': self.user.email},
        )

        response = self.client.get(
            reverse(
                'first:resend_otp'
            )
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    @patch(
        'first.views._generate_otp',
        return_value='123456',
    )
    @patch('django.core.mail.EmailMultiAlternatives.send', return_value=1)
    def test_five_wrong_codes_lock_reset(
        self,
        mocked_send_mail,
        mocked_generate,
    ):
        self.client.post(
            reverse(
                'first:forgot_password'
            ),
            {'email': self.user.email},
        )

        for _ in range(5):
            self.client.post(
                reverse(
                    'first:verify_otp'
                ),
                {
                    'otp_code': '000000'
                },
            )

        self.user.refresh_from_db()

        self.assertGreaterEqual(
            self.user.otp_attempts,
            5,
        )
        self.assertIsNotNone(
            self.user.otp_locked_until
        )
        self.assertGreater(
            self.user.otp_locked_until,
            timezone.now(),
        )
        self.assertIsNone(
            self.user.otp_code
        )

    @patch(
        'first.views._generate_otp',
        return_value='123456',
    )
    @patch('django.core.mail.EmailMultiAlternatives.send', return_value=1)
    def test_correct_code_creates_session_gate(
        self,
        mocked_send_mail,
        mocked_generate,
    ):
        self.client.post(
            reverse(
                'first:forgot_password'
            ),
            {'email': self.user.email},
        )

        response = self.client.post(
            reverse(
                'first:verify_otp'
            ),
            {'otp_code': '123456'},
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        session = self.client.session

        self.assertTrue(
            session.get(
                'password_reset_verified'
            )
        )

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.otp_verified
        )
        self.assertIsNone(
            self.user.otp_code
        )

    def test_db_verified_flag_without_session_is_not_enough(
        self,
    ):
        self.user.otp_verified = True
        self.user.save(
            update_fields=[
                'otp_verified'
            ]
        )

        session = self.client.session
        session['reset_email'] = (
            self.user.email
        )
        session.save()

        response = self.client.get(
            reverse(
                'first:set_new_password'
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse(
                'first:forgot_password'
            ),
        )
