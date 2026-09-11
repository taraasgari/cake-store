"""
Create or update the owner account using environment variables.

No username, password, email or phone number is stored directly
inside this file.
"""

import os

import django


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "base.settings",
)

django.setup()


from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction


User = get_user_model()


def required_env(name):
    """
    دریافت مقدار الزامی از متغیرهای محیطی.
    """

    value = os.environ.get(
        name,
        "",
    ).strip()

    if not value:
        raise RuntimeError(
            f"{name} environment variable is required."
        )

    return value


@transaction.atomic
def create_owner():
    """
    ساخت یا به‌روزرسانی حساب مالک سایت.
    """

    username = os.environ.get(
        "OWNER_USERNAME",
        "owner",
    ).strip() or "owner"

    email = required_env(
        "OWNER_EMAIL"
    )

    phone = required_env(
        "OWNER_PHONE"
    )

    password = required_env(
        "OWNER_PASSWORD"
    )

    user, created = User.objects.update_or_create(
        username=username,
        defaults={
            "email": email,
            "phone": phone,
            "role": "owner",
            "is_superuser": True,
            "is_staff": True,
            "is_active": True,
        },
    )

    validate_password(
        password,
        user=user,
    )

    user.set_password(password)

    user.save(
        update_fields=[
            "password",
        ]
    )

    action = (
        "created"
        if created
        else "updated"
    )

    print(
        f"Owner account {action}: {username}"
    )

    print(
        "Password was loaded securely from "
        "OWNER_PASSWORD and was not displayed."
    )


if __name__ == "__main__":
    create_owner()
