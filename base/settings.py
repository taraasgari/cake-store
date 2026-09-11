import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent


# بارگذاری متغیرهای فایل .env
try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass


def env_bool(name, default=False):
    """خواندن مقدارهای True و False از متغیر محیطی."""
    raw_value = os.environ.get(name)

    if raw_value is None:
        return default

    return raw_value.strip().lower() in {
        '1',
        'true',
        'yes',
        'on',
    }


def env_list(name, default=''):
    """تبدیل مقادیر جداشده با کاما به لیست."""
    return [
        item.strip()
        for item in os.environ.get(name, default).split(',')
        if item.strip()
    ]


# ==========================================================
# محیط اجرا و تنظیمات امنیتی اصلی
# ==========================================================

APP_ENV = os.environ.get(
    'DJANGO_ENV',
    'development',
).strip().lower()

if APP_ENV not in {
    'development',
    'production',
}:
    raise ImproperlyConfigured(
        "DJANGO_ENV must be either 'development' or 'production'."
    )

IS_PRODUCTION = APP_ENV == 'production'

_DEVELOPMENT_SECRET_KEY = (
    'django-insecure-development-only-change-me'
)

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    _DEVELOPMENT_SECRET_KEY,
)

DEBUG = env_bool(
    'DEBUG',
    not IS_PRODUCTION,
)

ALLOWED_HOSTS = env_list(
    'ALLOWED_HOSTS',
    (
        ''
        if IS_PRODUCTION
        else 'localhost,127.0.0.1,[::1]'
    ),
)

CSRF_TRUSTED_ORIGINS = env_list(
    'CSRF_TRUSTED_ORIGINS'
)


def _validate_production_environment():
    if not IS_PRODUCTION:
        return

    errors = []

    if (
        not SECRET_KEY
        or SECRET_KEY == _DEVELOPMENT_SECRET_KEY
        or SECRET_KEY.startswith('django-insecure-')
        or len(SECRET_KEY) < 50
    ):
        errors.append(
            'DJANGO_SECRET_KEY must be a unique random value '
            'of at least 50 characters.'
        )

    if DEBUG:
        errors.append(
            'DEBUG must be False in production.'
        )

    if (
        not ALLOWED_HOSTS
        or '*' in ALLOWED_HOSTS
        or any(
            host in {
                'localhost',
                '127.0.0.1',
                '[::1]',
            }
            for host in ALLOWED_HOSTS
        )
    ):
        errors.append(
            'ALLOWED_HOSTS must contain only real production hosts '
            'and must not use * or localhost.'
        )

    if not os.environ.get('DB_HOST', '').strip():
        errors.append(
            'DB_HOST is required in production; SQLite fallback '
            'is not allowed.'
        )

    if not os.environ.get(
        'POSTGRES_PASSWORD',
        '',
    ).strip():
        errors.append(
            'POSTGRES_PASSWORD is required in production.'
        )

    if errors:
        raise ImproperlyConfigured(
            'Unsafe production configuration:\n- '
            + '\n- '.join(errors)
        )


_validate_production_environment()


# ==========================================================
# برنامه‌های نصب‌شده
# ==========================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'first',
    'customer_care',
]


# ==========================================================
# Middleware
# ==========================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # مدیریت فایل‌های Static در سرور
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'base.urls'


# ==========================================================
# قالب‌ها
# ==========================================================

TEMPLATES = [
    {
        'BACKEND': (
            'django.template.backends.django.'
            'DjangoTemplates'
        ),

        'DIRS': [
            BASE_DIR / 'first' / 'templates',
        ],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                (
                    'django.template.context_processors.'
                    'request'
                ),
                (
                    'django.contrib.auth.context_processors.'
                    'auth'
                ),
                (
                    'django.contrib.messages.context_processors.'
                    'messages'
                ),
                'first.context_processors.site_settings',
            ],
        },
    },
]


WSGI_APPLICATION = 'base.wsgi.application'
ASGI_APPLICATION = 'base.asgi.application'


# ==========================================================
# دیتابیس
# ==========================================================

# اگر DB_HOST تعریف شده باشد از PostgreSQL استفاده می‌شود.
# در غیر این صورت برای اجرای محلی SQLite فعال می‌ماند.

if os.environ.get('DB_HOST'):
    DATABASES = {
        'default': {
            'ENGINE': (
                'django.db.backends.postgresql'
            ),

            'NAME': os.environ.get(
                'POSTGRES_DB',
                'arayeshi',
            ),

            'USER': os.environ.get(
                'POSTGRES_USER',
                'arayeshi',
            ),

            'PASSWORD': os.environ.get(
                'POSTGRES_PASSWORD',
                '',
            ),

            'HOST': os.environ.get(
                'DB_HOST',
                '',
            ),

            'PORT': os.environ.get(
                'DB_PORT',
                '5432',
            ),

            'CONN_MAX_AGE': int(
                os.environ.get(
                    'DB_CONN_MAX_AGE',
                    '60',
                )
            ),

            'OPTIONS': {
                'connect_timeout': int(
                    os.environ.get(
                        'DB_CONNECT_TIMEOUT',
                        '10',
                    )
                ),
            },
        }
    }

else:
    DATABASES = {
        'default': {
            'ENGINE': (
                'django.db.backends.sqlite3'
            ),

            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ==========================================================
# اعتبارسنجی رمز عبور
# ==========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'UserAttributeSimilarityValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'MinimumLengthValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'CommonPasswordValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'NumericPasswordValidator'
        ),
    },
]


# مدل کاربر سفارشی
AUTH_USER_MODEL = 'first.User'


# آدرس‌های ورود و خروج
LOGIN_URL = 'first:login'
LOGIN_REDIRECT_URL = 'first:home'
LOGOUT_REDIRECT_URL = 'first:home'


# ==========================================================
# زبان و زمان
# ==========================================================

LANGUAGE_CODE = 'fa'

TIME_ZONE = os.environ.get(
    'TIME_ZONE',
    'Asia/Tehran',
)

USE_I18N = True
USE_TZ = True


# ==========================================================
# فایل‌های Static
# ==========================================================

STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]


# ==========================================================
# فایل‌های Media
# ==========================================================

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'


# ==========================================================
# سیستم ذخیره‌سازی سازگار با Django 5.2
# ==========================================================

STORAGES = {
    'default': {
        'BACKEND': (
            'django.core.files.storage.'
            'FileSystemStorage'
        ),
    },

    'staticfiles': {
        'BACKEND': (
            'whitenoise.storage.'
            'CompressedStaticFilesStorage'
        ),
    },
}


WHITENOISE_MAX_AGE = int(
    os.environ.get(
        'WHITENOISE_MAX_AGE',
        '31536000' if not DEBUG else '0',
    )
)


# ==========================================================
# تنظیمات ایمیل
# ==========================================================

EMAIL_HOST = os.environ.get(
    'EMAIL_HOST',
    'smtp.gmail.com',
)

EMAIL_PORT = int(
    os.environ.get(
        'EMAIL_PORT',
        '587',
    )
)

EMAIL_USE_TLS = env_bool(
    'EMAIL_USE_TLS',
    True,
)

EMAIL_USE_SSL = env_bool(
    'EMAIL_USE_SSL',
    False,
)

EMAIL_HOST_USER = os.environ.get(
    'EMAIL_HOST_USER',
    '',
).strip()

EMAIL_HOST_PASSWORD = os.environ.get(
    'EMAIL_HOST_PASSWORD',
    '',
).strip()

EMAIL_TIMEOUT = int(
    os.environ.get(
        'EMAIL_TIMEOUT',
        '15',
    )
)

_explicit_email_backend = os.environ.get(
    'EMAIL_BACKEND',
    '',
).strip()

if _explicit_email_backend:
    EMAIL_BACKEND = (
        _explicit_email_backend
    )
elif (
    EMAIL_HOST_USER
    and EMAIL_HOST_PASSWORD
):
    # اگر اطلاعات SMTP تنظیم شده باشد، حتی در DEBUG
    # ایمیل واقعی ارسال می‌شود.
    EMAIL_BACKEND = (
        'django.core.mail.backends.'
        'smtp.EmailBackend'
    )
elif DEBUG:
    # فقط برای توسعه بدون SMTP؛ ایمیل در ترمینال چاپ می‌شود.
    EMAIL_BACKEND = (
        'django.core.mail.backends.'
        'console.EmailBackend'
    )
else:
    EMAIL_BACKEND = (
        'django.core.mail.backends.'
        'smtp.EmailBackend'
    )

DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL',
    EMAIL_HOST_USER
    or 'noreply@localhost',
)


# ==========================================================
# تنظیمات امنیتی Production
# ==========================================================

# برای اجرا پشت Nginx یا Traefik
SECURE_PROXY_SSL_HEADER = (
    'HTTP_X_FORWARDED_PROTO',
    'https',
)

SECURE_SSL_REDIRECT = env_bool(
    'SECURE_SSL_REDIRECT',
    not DEBUG,
)

SESSION_COOKIE_SECURE = env_bool(
    'SESSION_COOKIE_SECURE',
    not DEBUG,
)

CSRF_COOKIE_SECURE = env_bool(
    'CSRF_COOKIE_SECURE',
    not DEBUG,
)

SESSION_COOKIE_HTTPONLY = True

SESSION_COOKIE_SAMESITE = os.environ.get(
    'SESSION_COOKIE_SAMESITE',
    'Lax',
)

CSRF_COOKIE_SAMESITE = os.environ.get(
    'CSRF_COOKIE_SAMESITE',
    'Lax',
)

CSRF_COOKIE_HTTPONLY = env_bool(
    'CSRF_COOKIE_HTTPONLY',
    False,
)

SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_REFERRER_POLICY = os.environ.get(
    'SECURE_REFERRER_POLICY',
    'strict-origin-when-cross-origin',
)

X_FRAME_OPTIONS = 'SAMEORIGIN'

SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'


SECURE_HSTS_SECONDS = int(
    os.environ.get(
        'SECURE_HSTS_SECONDS',
        '31536000' if not DEBUG else '0',
    )
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    'SECURE_HSTS_INCLUDE_SUBDOMAINS',
    not DEBUG,
)

SECURE_HSTS_PRELOAD = env_bool(
    'SECURE_HSTS_PRELOAD',
    False,
)


# ==========================================================
# تنظیمات سایت
# ==========================================================

SITE_NAME = os.environ.get(
    'SITE_NAME',
    'آرایشی شاپ',
)

DEFAULT_AUTO_FIELD = (
    'django.db.models.BigAutoField'
)


# ==========================================================
# گزارش خطاها و رویدادها
# ==========================================================

LOGGING = {
    'version': 1,

    'disable_existing_loggers': False,

    'formatters': {
        'standard': {
            'format': (
                '[{levelname}] {asctime} '
                '{name}: {message}'
            ),

            'style': '{',
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },

    'root': {
        'handlers': [
            'console',
        ],

        'level': os.environ.get(
            'LOG_LEVEL',
            'INFO',
        ),
    },
}
