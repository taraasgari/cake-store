import os
import subprocess
import sys

from django.test import SimpleTestCase


class ProductionSettingsTests(SimpleTestCase):
    def _run_settings_import(self, **overrides):
        env = os.environ.copy()

        env.update({
            'DJANGO_ENV': 'production',
            'DEBUG': 'False',
            'DJANGO_SECRET_KEY': 'x' * 64,
            'ALLOWED_HOSTS': 'shop.example.com',
            'CSRF_TRUSTED_ORIGINS': 'https://shop.example.com',
            'DB_HOST': 'db',
            'POSTGRES_DB': 'arayeshi',
            'POSTGRES_USER': 'arayeshi',
            'POSTGRES_PASSWORD': 'strong-test-db-password',
        })

        env.update(overrides)

        return subprocess.run(
            [
                sys.executable,
                '-c',
                (
                    'import os; '
                    'os.environ["DJANGO_SETTINGS_MODULE"]="base.settings"; '
                    'import django; django.setup(); '
                    'from django.conf import settings; '
                    'print(settings.APP_ENV)'
                ),
            ],
            cwd=os.getcwd(),
            env=env,
            text=True,
            capture_output=True,
        )

    def test_valid_production_environment_loads(self):
        result = self._run_settings_import()
        self.assertEqual(
            result.returncode,
            0,
            msg=result.stderr,
        )
        self.assertIn(
            'production',
            result.stdout,
        )

    def test_production_rejects_debug_true(self):
        result = self._run_settings_import(
            DEBUG='True',
        )
        self.assertNotEqual(
            result.returncode,
            0,
        )
        self.assertIn(
            'DEBUG must be False',
            result.stderr,
        )

    def test_production_rejects_weak_secret(self):
        result = self._run_settings_import(
            DJANGO_SECRET_KEY='short',
        )
        self.assertNotEqual(
            result.returncode,
            0,
        )
        self.assertIn(
            'DJANGO_SECRET_KEY',
            result.stderr,
        )

    def test_production_rejects_wildcard_host(self):
        result = self._run_settings_import(
            ALLOWED_HOSTS='*',
        )
        self.assertNotEqual(
            result.returncode,
            0,
        )
        self.assertIn(
            'ALLOWED_HOSTS',
            result.stderr,
        )

    def test_production_rejects_sqlite_fallback(self):
        result = self._run_settings_import(
            DB_HOST='',
        )
        self.assertNotEqual(
            result.returncode,
            0,
        )
        self.assertIn(
            'DB_HOST',
            result.stderr,
        )

    def test_production_requires_database_password(self):
        result = self._run_settings_import(
            POSTGRES_PASSWORD='',
        )
        self.assertNotEqual(
            result.returncode,
            0,
        )
        self.assertIn(
            'POSTGRES_PASSWORD',
            result.stderr,
        )
