from django.conf import settings
from django.core.mail import (
    EmailMessage,
    get_connection,
)
from django.core.management.base import (
    BaseCommand,
    CommandError,
)


class Command(BaseCommand):
    help = (
        'Validate email backend and optionally '
        'send a real test message.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            dest='to_email',
            default='',
        )

    def handle(
        self,
        *args,
        **options,
    ):
        backend = settings.EMAIL_BACKEND

        self.stdout.write(
            f'EMAIL_BACKEND={backend}'
        )
        self.stdout.write(
            (
                'EMAIL_HOST='
                + (
                    getattr(
                        settings,
                        'EMAIL_HOST',
                        '',
                    )
                    or '(empty)'
                )
            )
        )
        self.stdout.write(
            (
                'EMAIL_HOST_USER='
                + (
                    '(configured)'
                    if getattr(
                        settings,
                        'EMAIL_HOST_USER',
                        '',
                    )
                    else '(empty)'
                )
            )
        )

        if 'console.EmailBackend' in backend:
            raise CommandError(
                (
                    'ConsoleEmailBackend is active. '
                    'Emails are printed in the terminal '
                    'and are NOT delivered.'
                )
            )

        if (
            'smtp.EmailBackend' in backend
            and (
                not getattr(
                    settings,
                    'EMAIL_HOST',
                    '',
                )
                or not getattr(
                    settings,
                    'EMAIL_HOST_USER',
                    '',
                )
                or not getattr(
                    settings,
                    'EMAIL_HOST_PASSWORD',
                    '',
                )
            )
        ):
            raise CommandError(
                (
                    'SMTP configuration is incomplete. '
                    'EMAIL_HOST, EMAIL_HOST_USER and '
                    'EMAIL_HOST_PASSWORD are required.'
                )
            )

        connection = get_connection(
            fail_silently=False
        )

        try:
            connection.open()
        except Exception as exc:
            raise CommandError(
                (
                    'Email connection/authentication '
                    f'failed: {exc}'
                )
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                'Email connection/authentication: OK'
            )
        )

        to_email = (
            options.get('to_email')
            or ''
        ).strip()

        if to_email:
            sent = EmailMessage(
                subject='Arayeshi email test',
                body=(
                    'ارسال ایمیل سایت درست کار می‌کند.'
                ),
                from_email=(
                    settings.DEFAULT_FROM_EMAIL
                ),
                to=[to_email],
                connection=connection,
            ).send(
                fail_silently=False
            )

            if sent != 1:
                raise CommandError(
                    (
                        'Backend did not accept '
                        'test email.'
                    )
                )

            self.stdout.write(
                self.style.SUCCESS(
                    (
                        'Test message accepted for '
                        f'{to_email}'
                    )
                )
            )

        connection.close()
