import json
import re
import secrets
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Max, Q, Sum
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from shop_core.catalog.discounts import core_discounts as _core_discounts
from .slider_forms import SliderForm, safe_slider_link
from shop_core.catalog.management import update_named_catalog_item
from shop_core.catalog.detail import core_product_detail as _core_product_detail
from shop_core.catalog.listing import core_product_list as _core_product_list
from shop_core.customization.services import (
    apply_site_settings as _core_apply_site_settings,
    customizer_number as _core_customizer_number,
    customizer_payload as _core_customizer_payload,
    customizer_url as _core_customizer_url,
    clean_customizer_rule as _core_clean_customizer_rule,
    clean_customizer_styles as _core_clean_customizer_styles,
    load_customizer_state as _core_load_customizer_state,
    owner_dashboard_context as _core_owner_dashboard_context,
    reset_customizer_state as _core_reset_customizer_state,
    reset_site_settings as _core_reset_site_settings,
    save_customizer_state as _core_save_customizer_state,
    save_simple_product as _core_save_simple_product,
    set_number_format as _core_set_number_format,
    toggle_number_format as _core_toggle_number_format,
)
from shop_core.commerce.services import (
    CommerceError as _CoreCommerceError,
    add_to_cart as _core_add_to_cart,
    admin_order_queryset as _core_admin_order_queryset,
    cart_context as _core_cart_context,
    checkout_payload as _core_checkout_payload,
    clear_cart as _core_clear_cart,
    get_order_detail as _core_get_order_detail,
    get_order_for_user as _core_get_order_for_user,
    place_order as _core_place_order,
    remove_cart_item as _core_remove_cart_item,
    remove_from_wishlist as _core_remove_from_wishlist,
    transition_order as _core_transition_order,
    update_cart_item as _core_update_cart_item,
    update_product_stock as _core_update_product_stock,
    user_orders_data as _core_user_orders_data,
    warehouse_products_data as _core_warehouse_products_data,
    wishlist_items as _core_wishlist_items,
    add_to_wishlist as _core_add_to_wishlist,
)
from shop_core.catalog.management import (
    admin_product_data as _core_admin_product_data,
    create_named_catalog_item as _core_create_named_catalog_item,
    deactivate_product as _core_deactivate_product,
    delete_catalog_item as _core_delete_catalog_item,
    unique_catalog_slug as _core_unique_catalog_slug,
    upsert_color as _core_upsert_color,
)
from shop_core.catalog.product_writes import (
    admin_product_form_context as _core_admin_product_form_context,
    create_product_from_request as _core_create_product_from_request,
    parse_nonnegative_decimal as _core_parse_nonnegative_decimal,
    parse_nonnegative_int as _core_parse_nonnegative_int,
    update_product_from_request as _core_update_product_from_request,
)
from shop_core.catalog.reviews import (
    admin_review_data as _core_admin_review_data,
    create_product_review as _core_create_product_review,
    delete_product_review as _core_delete_product_review,
    verify_product_review as _core_verify_product_review,
)
from shop_core.catalog.read_views import (
    core_best_sellers as _core_best_sellers,
    core_brand_products as _core_brand_products,
    core_category_products as _core_category_products,
    core_search_products as _core_search_products,
)
from shop_core.catalog.slugs import build_unique_product_slug

from .analytics_views import (
    analytics_dashboard,
    analytics_download_pdf,
    analytics_export_csv,
)
from .customer_service_content import CUSTOMER_SERVICE_PAGES
from .decorators import (
    admin_required,
    get_effective_admin_permissions,
    owner_required,
    permission_required,
)
from .forms import (
    ForgotPasswordForm,
    LoginForm,
    OTPVerificationForm,
    ProfileUpdateForm,
    SetNewPasswordForm,
    SignUpForm,
)
from .image_utils import prepare_uploaded_image
from .models import (
    AdminPermission,
    AdminRole,
    AdminUserPermission,
    Brand,
    Cart,
    CartItem,
    Category,
    Color,
    Coupon,
    InventoryBatch,
    Order,
    OrderItem,
    Product,
    ProductImage,
    ProductReview,
    ProductType,
    ProductVariant,
    SiteSettings,
    SliderImage,
    Tag,
    Wishlist,
)

User = get_user_model()


def _is_safe_local_redirect(request, candidate):
    """Return True only for same-host redirect targets."""
    if not candidate:
        return False

    return url_has_allowed_host_and_scheme(
        url=candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )


# ============================================
# توابع کمکی OTP و بازیابی رمز عبور
# ============================================

OTP_VALID_SECONDS = 300
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_ATTEMPTS = 5
OTP_LOCK_MINUTES = 15
RESET_VERIFIED_SECONDS = 600


def _generate_otp():
    return ''.join(
        secrets.choice('0123456789')
        for _ in range(6)
    )
def _clear_reset_session(request):
    for key in (
        'reset_email',
        'password_reset_verified',
        'password_reset_verified_at',
    ):
        request.session.pop(
            key,
            None,
        )


def _reset_user_otp(user):
    user.otp_code = None
    user.otp_created_at = None
    user.otp_verified = False
    user.otp_attempts = 0
    user.otp_locked_until = None
    user.save(
        update_fields=[
            'otp_code',
            'otp_created_at',
            'otp_verified',
            'otp_attempts',
            'otp_locked_until',
        ]
    )


def _send_password_reset_otp(user):
    from django.contrib.auth.hashers import make_password
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags

    with transaction.atomic():
        locked_user = (
            User.objects
            .select_for_update()
            .get(pk=user.pk)
        )

        now = timezone.now()

        if (
            locked_user.otp_last_sent_at
            and (
                now
                - locked_user.otp_last_sent_at
            ).total_seconds()
            < OTP_RESEND_COOLDOWN_SECONDS
        ):
            return False

        if (
            locked_user.otp_locked_until
            and locked_user.otp_locked_until
            > now
        ):
            return False

        otp_code = _generate_otp()

        locked_user.otp_code = (
            make_password(
                otp_code
            )
        )
        locked_user.otp_created_at = now
        locked_user.otp_last_sent_at = now
        locked_user.otp_verified = False
        locked_user.otp_attempts = 0
        locked_user.otp_locked_until = None

        locked_user.save(
            update_fields=[
                'otp_code',
                'otp_created_at',
                'otp_last_sent_at',
                'otp_verified',
                'otp_attempts',
                'otp_locked_until',
            ]
        )

        html_message = render_to_string(
            'emails/otp_code.html',
            {
                'user': locked_user,
                'otp_code': otp_code,
                'site_name': (
                    settings.SITE_NAME
                ),
                'valid_minutes': 5,
            },
        )

        message = EmailMultiAlternatives(
            subject=(
                '🔐 کد تأیید بازیابی رمز عبور'
            ),
            body=strip_tags(
                html_message
            ),
            from_email=(
                settings.DEFAULT_FROM_EMAIL
            ),
            to=[locked_user.email],
        )

        message.attach_alternative(
            html_message,
            'text/html',
        )

        sent_count = message.send(
            fail_silently=False
        )

        if sent_count != 1:
            raise RuntimeError(
                (
                    'Email backend did not '
                    'accept reset email.'
                )
            )

    user.refresh_from_db()
    return True


# ============================================
# ثابت‌های ویرایشگر بصری
# ============================================

_CUSTOMIZER_COLORS = re.compile(
    r'^#[0-9a-fA-F]{6}$'
)

_CUSTOMIZER_IDS = re.compile(
    r'^[a-zA-Z0-9_-]{1,120}$'
)

_CUSTOMIZER_LENGTH = re.compile(
    (
        r'^(?:0|\d{1,4}'
        r'(?:\.\d{1,2})?)'
        r'(?:px|%|rem|em|vw|vh)?$'
    )
)

_CUSTOMIZER_STYLES = {
    'color',
    'backgroundColor',
    'fontSize',
    'fontWeight',
    'fontFamily',
    'textAlign',
    'lineHeight',
    'letterSpacing',
    'borderRadius',
    'opacity',
    'padding',
    'margin',
    'objectFit',
    'boxShadow',
}

_CUSTOMIZER_DEFAULT_THEME = {
    'primary': '#c9954d',
    'secondary': '#75471f',
    'accent': '#e3c286',
    'bg': '#090706',
    'text': '#f7f0e7',
}


# ============================================
# ویوهای اصلی و احراز هویت
# ============================================

# The first perfume hero is a theme asset, not a SliderImage database record.
# Older local installs may still contain the same image as an uploaded slider from
# before it became part of the theme.  Ignore only those known legacy records so
# the built-in slide stays visible until the merchant adds a genuinely custom one.
_THEME_DEFAULT_SLIDER_BASENAMES = {
    'perfume-default-slider.png',
    'ChatGPT_Image_Sep_12_2026_01_02_26_AM.png',
}


def _is_legacy_theme_slider(slider):
    image_name = str(getattr(getattr(slider, 'image', None), 'name', '') or '')
    basename = image_name.replace('\\', '/').rsplit('/', 1)[-1]
    return basename in _THEME_DEFAULT_SLIDER_BASENAMES


def home(request):
    """صفحه اصلی فروشگاه با اسلایدر ثابت قالب یا اسلایدرهای سفارشی فروشنده."""
    slider_rows = SliderImage.objects.filter(is_active=True).order_by('order', 'id')
    sliders = [slider for slider in slider_rows if not _is_legacy_theme_slider(slider)]
    for slider in sliders:
        try:
            slider.safe_link = safe_slider_link(slider.link)
        except (ValidationError, ValueError):
            slider.safe_link = ''
    active_products = Product.objects.filter(is_active=True).exclude(slug__isnull=True).exclude(slug='')

    featured_products = active_products.filter(is_featured=True).select_related('category', 'brand')[:8]
    new_products = active_products.filter(is_new=True).select_related('category', 'brand')[:8]
    best_sellers = active_products.filter(is_best_seller=True).select_related('category', 'brand').order_by('-sales_count', '-updated_at', '-id')[:8]
    discounted_products = active_products.filter(
        Q(is_featured=True) |
        Q(discount_price__isnull=False, discount_price__lt=F('price')) |
        Q(
            variants__is_active=True,
            variants__discount_price__isnull=False,
            variants__discount_price__lt=F('variants__price')
        )
    ).select_related('category', 'brand').distinct()[:8]

    categories = Category.objects.filter(
        is_active=True,
        parent=None,
    ).exclude(slug__isnull=True).exclude(slug='')[:8]
    brands = Brand.objects.filter(is_active=True).exclude(slug__isnull=True).exclude(slug='')[:10]

    context = {
        'sliders': sliders,
        'latest_products': active_products.select_related('category', 'brand').order_by('-created_at', '-id')[:8],
        'featured_products': featured_products,
        'new_products': new_products,
        'best_sellers': best_sellers,
        'discounted_products': discounted_products,
        'categories': categories,
        'brands': brands,
    }
    return render(request, 'index.html', context)

def login_view(request):
    from django.core.cache import cache
    from django.utils.http import url_has_allowed_host_and_scheme
    import hashlib

    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('first:owner_panel')
        return redirect('first:home')

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            identifier = form.cleaned_data['username']
            password = form.cleaned_data['password']

            remote_addr = request.META.get('REMOTE_ADDR', 'unknown')
            raw_key = f'{settings.SECRET_KEY}:{remote_addr}:{identifier.casefold()}'
            throttle_key = (
                'perfume-login:'
                + hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
            )
            attempts = int(cache.get(throttle_key, 0) or 0)

            if attempts >= 8:
                messages.error(
                    request,
                    'تعداد تلاش‌های ورود بیش از حد مجاز است. ۱۵ دقیقه بعد دوباره تلاش کنید.',
                )
                return render(
                    request,
                    'login.html',
                    {'form': form},
                    status=429,
                )

            # Resolve the real username case-insensitively so old owner/admin
            # accounts continue to work even if their stored casing differs.
            user_obj = (
                User.objects
                .filter(username__iexact=identifier, is_active=True)
                .only('id', 'username')
                .first()
            )

            user = None
            if user_obj is not None:
                user = authenticate(
                    request,
                    username=user_obj.username,
                    password=password,
                )

            if user is not None:
                cache.delete(throttle_key)
                login(request, user)

                # Honour the existing "remember me" checkbox.
                if request.POST.get('remember'):
                    request.session.set_expiry(60 * 60 * 24 * 30)
                else:
                    request.session.set_expiry(0)

                messages.success(request, '✨ خوش آمدید!')

                next_page = request.GET.get('next')
                if (
                    next_page
                    and url_has_allowed_host_and_scheme(
                        url=next_page,
                        allowed_hosts={request.get_host()},
                        require_https=request.is_secure(),
                    )
                ):
                    return redirect(next_page)

                if user.is_superuser:
                    return redirect('first:owner_panel')
                return redirect('first:home')

            cache.set(throttle_key, attempts + 1, timeout=900)
            messages.error(request, '❌ نام کاربری یا رمز عبور اشتباه است')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def signup_view(request):
    if request.user.is_authenticated:
        messages.warning(request, "شما قبلاً وارد حساب کاربری خود شده‌اید")
        return redirect('first:home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                pass  # external notification hook removed
                messages.success(request, f"🎉 ثبت‌نام با موفقیت انجام شد! خوش آمدید {user.username}")
                return redirect('first:home')
            except Exception:
                messages.error(request, "❌ ثبت‌نام انجام نشد. دوباره تلاش کنید.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignUpForm()

    return render(request, 'signup.html', {'form': form})

@require_POST
def logout_view(request):
    logout(request)

    messages.info(
        request,
        '👋 با موفقیت خارج شدید',
    )

    return redirect('first:home')

@login_required
def profile_view(request):
    return render(request, 'profile.html', {'user': request.user})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ پروفایل شما با موفقیت به‌روزرسانی شد")
            return redirect('first:profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'edit_profile.html', {'form': form})


# ============================================
# ویوهای OTP برای بازیابی رمز عبور
# ============================================

def mask_email(email):
    """مخفی کردن بخشی از ایمیل برای نمایش"""
    if not email:
        return email
    parts = email.split('@')
    if len(parts) == 2:
        username, domain = parts
        if len(username) > 3:
            masked_username = username[:3] + '***' + username[-1:]
        else:
            masked_username = username[0] + '***'
        return f"{masked_username}@{domain}"
    return email

def forgot_password(request):
    import logging

    logger = logging.getLogger(
        __name__
    )

    if request.user.is_authenticated:
        return redirect('first:home')

    if request.method == 'POST':
        form = ForgotPasswordForm(
            request.POST
        )

        if form.is_valid():
            email = (
                form.cleaned_data[
                    'email'
                ]
                .strip()
                .lower()
            )

            _clear_reset_session(
                request
            )

            request.session[
                'reset_email'
            ] = email

            user = (
                User.objects
                .filter(
                    email__iexact=email
                )
                .first()
            )

            if user is not None:
                now = timezone.now()

                if (
                    user.otp_locked_until
                    and user.otp_locked_until
                    <= now
                ):
                    user.otp_locked_until = None
                    user.otp_attempts = 0
                    user.save(
                        update_fields=[
                            'otp_locked_until',
                            'otp_attempts',
                        ]
                    )

                try:
                    _send_password_reset_otp(
                        user
                    )
                except Exception:
                    logger.exception(
                        (
                            'Password reset email '
                            'failed for user_id=%s'
                        ),
                        user.pk,
                    )

            messages.success(
                request,
                (
                    'اگر حسابی با این ایمیل وجود '
                    'داشته باشد، کد بازیابی برای '
                    'آن ارسال می‌شود.'
                ),
            )

            return redirect(
                'first:verify_otp'
            )
    else:
        form = ForgotPasswordForm()

    return render(
        request,
        'forgot_password.html',
        {'form': form},
    )

def verify_otp(request):
    from datetime import timedelta
    from django.contrib.auth.hashers import check_password

    if request.user.is_authenticated:
        return redirect('first:home')

    email = request.session.get('reset_email')

    if not email:
        messages.error(
            request,
            "❌ لطفاً ابتدا فرآیند بازیابی رمز عبور را شروع کنید",
        )
        return redirect('first:forgot_password')

    user = User.objects.filter(
        email__iexact=email
    ).first()

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)

        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            now = timezone.now()

            valid = False
            expired = False
            locked = False

            if user is not None:
                if (
                    user.otp_locked_until
                    and user.otp_locked_until > now
                ):
                    locked = True
                elif not user.otp_code or not user.otp_created_at:
                    valid = False
                elif (
                    (now - user.otp_created_at).total_seconds()
                    > OTP_VALID_SECONDS
                ):
                    expired = True
                else:
                    valid = check_password(
                        otp_code,
                        user.otp_code,
                    )

            if valid:
                user.otp_verified = True
                user.otp_code = None
                user.otp_created_at = None
                user.otp_attempts = 0
                user.otp_locked_until = None
                user.save(
                    update_fields=[
                        'otp_verified',
                        'otp_code',
                        'otp_created_at',
                        'otp_attempts',
                        'otp_locked_until',
                    ]
                )

                request.session[
                    'password_reset_verified'
                ] = True
                request.session[
                    'password_reset_verified_at'
                ] = int(now.timestamp())

                messages.success(
                    request,
                    (
                        "✅ کد تأیید صحیح است. "
                        "اکنون رمز عبور جدید را تنظیم کنید."
                    ),
                )
                return redirect('first:set_new_password')

            if user is not None:
                if expired:
                    _reset_user_otp(user)
                elif not locked:
                    user.otp_attempts += 1

                    if (
                        user.otp_attempts
                        >= OTP_MAX_ATTEMPTS
                    ):
                        user.otp_locked_until = (
                            now
                            + timedelta(
                                minutes=OTP_LOCK_MINUTES
                            )
                        )
                        user.otp_code = None
                        user.otp_created_at = None

                    user.save(
                        update_fields=[
                            'otp_attempts',
                            'otp_locked_until',
                            'otp_code',
                            'otp_created_at',
                        ]
                    )

            if locked:
                messages.error(
                    request,
                    (
                        "❌ به دلیل تلاش‌های ناموفق زیاد، "
                        "بازیابی موقتاً قفل شده است."
                    ),
                )
            elif expired:
                messages.error(
                    request,
                    (
                        "❌ کد تأیید منقضی شده است. "
                        "یک کد جدید درخواست کنید."
                    ),
                )
            elif (
                user is not None
                and user.otp_attempts
                >= OTP_MAX_ATTEMPTS
            ):
                messages.error(
                    request,
                    (
                        "❌ تعداد تلاش‌های مجاز تمام شد. "
                        "بازیابی برای ۱۵ دقیقه قفل شد."
                    ),
                )
            else:
                messages.error(
                    request,
                    "❌ کد تأیید صحیح نیست",
                )
    else:
        form = OTPVerificationForm()

    return render(
        request,
        'verify_otp.html',
        {
            'form': form,
            'email': email,
            'masked_email': mask_email(email),
        },
    )

def set_new_password(request):
    if request.user.is_authenticated:
        return redirect('first:home')

    email = request.session.get('reset_email')
    verified = request.session.get(
        'password_reset_verified'
    )
    verified_at = request.session.get(
        'password_reset_verified_at'
    )

    if not email or not verified or not verified_at:
        messages.error(
            request,
            "❌ ابتدا کد تأیید را با موفقیت وارد کنید",
        )
        return redirect('first:forgot_password')

    try:
        verified_at = int(verified_at)
    except (TypeError, ValueError):
        verified_at = 0

    if (
        int(timezone.now().timestamp()) - verified_at
        > RESET_VERIFIED_SECONDS
    ):
        _clear_reset_session(request)
        messages.error(
            request,
            (
                "❌ زمان تغییر رمز عبور منقضی شده است. "
                "دوباره درخواست دهید."
            ),
        )
        return redirect('first:forgot_password')

    user = User.objects.filter(
        email__iexact=email
    ).first()

    if user is None or not user.otp_verified:
        _clear_reset_session(request)
        messages.error(
            request,
            (
                "❌ نشست بازیابی معتبر نیست. "
                "دوباره درخواست دهید."
            ),
        )
        return redirect('first:forgot_password')

    if request.method == 'POST':
        form = SetNewPasswordForm(
            user,
            request.POST,
        )

        if form.is_valid():
            form.save()

            user.otp_code = None
            user.otp_created_at = None
            user.otp_verified = False
            user.otp_attempts = 0
            user.otp_locked_until = None
            user.save(
                update_fields=[
                    'otp_code',
                    'otp_created_at',
                    'otp_verified',
                    'otp_attempts',
                    'otp_locked_until',
                ]
            )

            _clear_reset_session(request)

            messages.success(
                request,
                (
                    "✅ رمز عبور با موفقیت تغییر کرد. "
                    "اکنون می‌توانید وارد شوید."
                ),
            )
            return redirect('first:login')
    else:
        form = SetNewPasswordForm(user)

    return render(
        request,
        'set_new_password.html',
        {'form': form},
    )

@require_POST
def resend_otp(request):
    import logging

    logger = logging.getLogger(
        __name__
    )

    if request.user.is_authenticated:
        return redirect('first:home')

    email = request.session.get(
        'reset_email'
    )

    if not email:
        messages.error(
            request,
            "❌ ابتدا ایمیل خود را وارد کنید",
        )
        return redirect(
            'first:forgot_password'
        )

    user = User.objects.filter(
        email__iexact=email
    ).first()

    sent = False

    if user is not None:
        now = timezone.now()

        if (
            user.otp_locked_until
            and user.otp_locked_until > now
        ):
            messages.error(
                request,
                (
                    "❌ بازیابی موقتاً قفل شده است. "
                    "کمی بعد دوباره تلاش کنید."
                ),
            )
            return redirect(
                'first:verify_otp'
            )

        try:
            sent = bool(
                _send_password_reset_otp(
                    user
                )
            )
        except Exception:
            logger.exception(
                (
                    "Password reset OTP resend "
                    "failed for user_id=%s"
                ),
                user.pk,
            )

    request.session.pop(
        'password_reset_verified',
        None,
    )
    request.session.pop(
        'password_reset_verified_at',
        None,
    )

    if sent:
        messages.success(
            request,
            (
                "✅ کد جدید ارسال شد. "
                "این کد ۵ دقیقه اعتبار دارد."
            ),
        )
    else:
        messages.info(
            request,
            (
                "اگر امکان ارسال کد جدید وجود داشته باشد، "
                "کد برای شما ارسال می‌شود. بین ارسال‌ها "
                "حداقل ۶۰ ثانیه فاصله لازم است."
            ),
        )

    return redirect(
        'first:verify_otp'
    )


# ============================================
# ویوهای پنل مالک
# ============================================

@owner_required
def owner_panel(request):
    context = _core_owner_dashboard_context(
        product_model=Product,
        user_model=User,
        order_model=Order,
        review_model=ProductReview,
        wishlist_model=Wishlist,
    )
    return render(
        request,
        'dashboard/owner_panel.html',
        context,
    )


@owner_required
def owner_profile_edit(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.address = request.POST.get('address', user.address)

        if request.FILES.get('profile_image'):
            user.profile_image = request.FILES['profile_image']

        user.save()
        messages.success(request, "✅ پروفایل شما با موفقیت به‌روزرسانی شد")
        return redirect('first:owner_panel')

    return render(request, 'dashboard/owner_profile_edit.html', {'user': request.user})

@owner_required
@require_POST
def owner_change_password(request):
    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.password_validation import validate_password

    old_password = request.POST.get('old_password') or ''
    new_password = request.POST.get('new_password') or ''
    confirm_password = request.POST.get('confirm_password') or ''

    if not request.user.check_password(old_password):
        messages.error(
            request,
            "❌ رمز عبور فعلی اشتباه است",
        )
        return redirect('first:owner_panel')

    if new_password != confirm_password:
        messages.error(
            request,
            "❌ رمز عبور جدید و تکرار آن مطابقت ندارد",
        )
        return redirect('first:owner_panel')

    try:
        validate_password(
            new_password,
            user=request.user,
        )
    except ValidationError as exc:
        for error in exc.messages:
            messages.error(
                request,
                f"❌ {error}",
            )
        return redirect('first:owner_panel')

    request.user.set_password(
        new_password
    )
    request.user.save(
        update_fields=['password']
    )

    update_session_auth_hash(
        request,
        request.user,
    )

    messages.success(
        request,
        "✅ رمز عبور با موفقیت تغییر کرد",
    )
    return redirect('first:owner_panel')


# ============================================
# ویوهای مدیریت ظاهر سایت
# ============================================

@permission_required('site_settings')
def site_settings(request):
    site = SiteSettings.get_settings()
    sliders = [
        slider for slider in SliderImage.objects.all().order_by('order')
        if not _is_legacy_theme_slider(slider)
    ]

    status = 200
    if request.method == 'POST':
        action = request.POST.get('slider_action')
        if action:
            if action not in ('add_slider', 'edit_slider', 'delete_slider'):
                messages.error(request, 'عملیات اسلایدر معتبر نیست.')
                status = 400
            else:
                slider = None
                if action != 'add_slider':
                    slider = get_object_or_404(SliderImage, pk=request.POST.get('slider_id'))
                if action == 'delete_slider':
                    slider.delete()
                    messages.success(request, 'اسلایدر حذف شد.')
                    return redirect('first:site_settings')
                data = {field: request.POST.get('slider_' + field, '') for field in SliderForm.Meta.fields}
                data['order'] = data['order'] or '0'
                files = {'image': request.FILES['slider_image']} if request.FILES.get('slider_image') else None
                form = SliderForm(data, files, instance=slider)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'اسلایدر ذخیره شد.')
                    return redirect('first:site_settings')
                for field, errors in form.errors.items():
                    messages.error(request, f'{form.fields[field].label}: {" ".join(errors)}')
                status = 400
        else:
            _core_apply_site_settings(site, request.POST, request.FILES)
            messages.success(request, 'تنظیمات سایت ذخیره شد.')
            return redirect('first:site_settings')
    return render(request, 'dashboard/site_settings.html', {
        'settings': site, 'sliders': sliders,
        'slider_form_data': request.POST if status == 400 else None,
    }, status=status)


@permission_required('site_settings')
@require_POST
def reset_site_settings(request):
    site = SiteSettings.get_settings()
    _core_reset_site_settings(site)
    messages.success(
        request,
        "✅ تنظیمات به حالت پیش‌فرض بازنشانی شد",
    )
    return redirect(
        'first:site_settings'
    )



# ============================================
# تنظیمات فرمت اعداد
# ============================================

@permission_required('site_settings')
@require_POST
def toggle_number_format(request):
    site = _core_toggle_number_format(
        SiteSettings.get_settings()
    )
    messages.success(
        request,
        (
            "✅ فرمت اعداد به "
            f"{site.get_number_format_display()} "
            "تغییر کرد"
        ),
    )
    return redirect(
        request.META.get(
            'HTTP_REFERER',
            'first:home',
        )
    )


@permission_required('site_settings')
def number_format_settings(request):
    site = SiteSettings.get_settings()
    return render(
        request,
        'dashboard/number_format_settings.html',
        {
            'settings': site,
            'current_format': site.number_format,
        },
    )


@permission_required('site_settings')
@require_POST
def update_number_format(request):
    try:
        site = _core_set_number_format(
            SiteSettings.get_settings(),
            request.POST.get('number_format'),
        )
    except ValidationError:
        messages.error(
            request,
            "❌ مقدار نامعتبر",
        )
        return redirect(
            'first:number_format_settings'
        )

    messages.success(
        request,
        (
            "✅ فرمت اعداد به "
            f"{site.get_number_format_display()} "
            "تغییر کرد"
        ),
    )
    return redirect(
        'first:number_format_settings'
    )


# ============================================
# ویوهای محصولات
# ============================================

def product_list(request, *args, **kwargs):
    return _core_product_list(
        request,
        *args,
        **kwargs,
        product_model=Product,
        category_model=Category,
        brand_model=Brand,
    )


def product_detail(request, slug):
    return _core_product_detail(
        request,
        slug,
        product_model=Product,
    )

@login_required
@require_POST
def add_review(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True,
    )

    _, error = _core_create_product_review(
        review_model=ProductReview,
        product=product,
        user=request.user,
        rating=request.POST.get('rating', ''),
        comment=request.POST.get('comment'),
    )

    if error == 'duplicate':
        messages.warning(
            request,
            "شما قبلاً برای این محصول نظر ثبت کرده‌اید",
        )
    elif error == 'invalid_rating':
        messages.error(request, "❌ امتیاز باید بین ۱ تا ۵ باشد")
    elif error == 'empty_comment':
        messages.error(request, "❌ لطفاً نظر خود را وارد کنید")
    elif error == 'comment_too_long':
        messages.error(request, "❌ متن نظر بیش از حد طولانی است")
    else:
        messages.success(
            request,
            "✅ نظر شما ثبت شد و پس از تایید نمایش داده می‌شود.",
        )

    return redirect('first:product_detail', slug=product.slug)


def category_products(request, *args, **kwargs):
    return _core_category_products(
        request,
        *args,
        **kwargs,
        category_model=Category,
        product_model=Product,
    )


def brand_products(request, *args, **kwargs):
    return _core_brand_products(
        request,
        *args,
        **kwargs,
        brand_model=Brand,
        product_model=Product,
    )


def search_products(request, *args, **kwargs):
    return _core_search_products(
        request,
        *args,
        **kwargs,
        product_model=Product,
    )



# ============================================
# ویوهای محصولات ویژه
# ============================================

def best_sellers(request, *args, **kwargs):
    """Public best-seller listing driven only by real Product rows."""
    products = (
        Product.objects.filter(is_active=True, is_best_seller=True)
        .exclude(slug__isnull=True)
        .exclude(slug='')
        .select_related('category', 'brand')
        .prefetch_related('variants')
        .order_by('-sales_count', '-updated_at', '-id')
    )
    page_obj = Paginator(products, 12).get_page(request.GET.get('page'))
    return render(
        request,
        'products/best_sellers.html',
        {
            'page_obj': page_obj,
            'title': 'پرفروش‌ترین محصولات',
        },
    )


def discounts(request, *args, **kwargs):
    """Show manually featured offers plus products with a real discount."""
    public_products = (
        Product.objects.filter(is_active=True)
        .exclude(slug__isnull=True)
        .exclude(slug='')
        .select_related('category', 'brand')
        .prefetch_related('variants')
        .order_by('-updated_at', '-id')
    )

    offer_products = []
    for product in public_products:
        has_discount = bool(
            product.discount_price is not None
            and product.discount_price < product.price
        )

        if not has_discount and product.has_variants:
            for variant in product.variants.all():
                if not getattr(variant, 'is_active', True):
                    continue
                variant_discount = getattr(variant, 'discount_price', None)
                if variant_discount is None:
                    continue
                base_price = getattr(variant, 'price', None) or product.price
                if variant_discount < base_price:
                    has_discount = True
                    break

        # The admin's "پیشنهاد ویژه" checkbox must also place the product
        # in this public offers collection, even when no reduced price is set.
        if product.is_featured or has_discount:
            offer_products.append(product)

    offer_products.sort(
        key=lambda product: (
            1 if product.is_featured else 0,
            int(getattr(product, 'discount_percent', 0) or 0),
            product.updated_at,
            product.id,
        ),
        reverse=True,
    )
    page_obj = Paginator(offer_products, 12).get_page(request.GET.get('page'))
    return render(
        request,
        'products/discounts.html',
        {
            'page_obj': page_obj,
            'title': 'تخفیف‌ها و پیشنهادهای ویژه',
        },
    )


# ============================================
# ویوهای سبد خرید
# ============================================

@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(
        user=request.user
    )
    return render(
        request,
        'cart/cart.html',
        _core_cart_context(cart),
    )


@require_POST
@login_required
def add_to_cart(request, product_id):
    variant_id = (
        request.POST.get('variant')
        or request.GET.get('variant')
    )
    color_id = (
        request.POST.get('color')
        or request.GET.get('color')
    )
    raw_quantity = (
        request.POST.get('qty')
        or request.GET.get('qty', 1)
    )

    try:
        result = _core_add_to_cart(
            cart_model=Cart,
            cart_item_model=CartItem,
            product_model=Product,
            variant_model=ProductVariant,
            user=request.user,
            product_id=product_id,
            quantity=raw_quantity,
            variant_id=variant_id,
            color_id=color_id,
        )
    except _CoreCommerceError as exc:
        product = exc.context.get('product')

        if exc.code == 'invalid_quantity':
            messages.error(
                request,
                "تعداد انتخاب‌شده معتبر نیست",
            )
        elif exc.code == 'color_unavailable':
            messages.error(
                request,
                "رنگ انتخاب شده موجود نیست",
            )
        elif exc.code == 'variant_required':
            messages.error(
                request,
                "لطفاً تنوع محصول را انتخاب کنید",
            )
        elif exc.code == 'variant_stock':
            variant = exc.context.get('variant')
            messages.error(
                request,
                f"موجودی کافی برای {variant} وجود ندارد",
            )
        elif exc.code == 'product_stock':
            messages.error(
                request,
                "موجودی کافی وجود ندارد",
            )
        else:
            raise

        return redirect(
            'first:product_detail',
            slug=product.slug,
        )

    product = result['product']

    if result['result'] == 'created':
        messages.success(
            request,
            f"{product.name} به سبد خرید اضافه شد",
        )
    elif result['result'] == 'increased':
        messages.success(
            request,
            f"تعداد {product.name} در سبد خرید افزایش یافت",
        )
    else:
        messages.warning(
            request,
            "موجودی کافی نیست",
        )

    next_url = request.GET.get('next')
    if _is_safe_local_redirect(
        request,
        next_url,
    ):
        return redirect(next_url)

    return redirect('first:cart')




@login_required
@require_POST
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user,
    )
    item_name = _core_remove_cart_item(
        cart_item
    )
    messages.success(
        request,
        f"{item_name} از سبد خرید حذف شد",
    )
    return redirect('first:cart')


@login_required
@require_POST
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(
        CartItem.objects.select_related(
            'product',
            'variant',
        ),
        id=item_id,
        cart__user=request.user,
    )

    try:
        result = _core_update_cart_item(
            cart_item,
            request.POST.get('quantity', ''),
        )
    except _CoreCommerceError as exc:
        if exc.code == 'invalid_quantity':
            messages.error(
                request,
                "تعداد واردشده معتبر نیست",
            )
        elif exc.code == 'insufficient_stock':
            messages.error(
                request,
                "موجودی کافی نیست",
            )
        else:
            raise
        return redirect('first:cart')

    if result['result'] == 'deleted':
        messages.success(
            request,
            f"{result['item_name']} از سبد خرید حذف شد",
        )
    else:
        messages.success(
            request,
            (
                f"تعداد {result['item_name']} "
                "به‌روزرسانی شد"
            ),
        )

    return redirect('first:cart')


@login_required
@require_POST
def clear_cart(request):
    cart = get_object_or_404(
        Cart,
        user=request.user,
    )
    _core_clear_cart(cart)
    messages.info(
        request,
        "سبد خرید شما خالی شد",
    )
    return redirect('first:cart')



# ============================================
# ویوهای سفارشات
# ============================================

@login_required
def checkout(request):
    cart = get_object_or_404(
        Cart,
        user=request.user,
    )

    if cart.items.count() == 0:
        messages.warning(
            request,
            "سبد خرید شما خالی است",
        )
        return redirect('first:cart')

    def _checkout_context(*, field_errors=None, values=None):
        if values is None:
            values = request.session.pop(
                'checkout_draft',
                None,
            )

        if field_errors is None:
            field_errors = request.session.pop(
                'checkout_errors',
                {},
            )

        if values is None:
            values = {
                'address': request.user.address or '',
                'postal_code': '',
                'phone': request.user.phone or '',
                'payment_method': 'cash',
                'note': '',
            }

        return {
            'cart': cart,
            'items': cart.items.all(),
            'final_price': cart.final_price,
            'total_items': cart.total_items,
            'user': request.user,
            'checkout_values': values,
            'checkout_errors': field_errors or {},
        }

    if request.method == 'POST':
        submitted_values = {
            'address': request.POST.get('address', ''),
            'postal_code': request.POST.get('postal_code', ''),
            'phone': request.POST.get('phone', ''),
            'payment_method': request.POST.get('payment_method', 'cash'),
            'note': request.POST.get('note', ''),
        }

        try:
            payload = _core_checkout_payload(
                address=submitted_values['address'],
                postal_code=submitted_values['postal_code'],
                phone=submitted_values['phone'],
                payment_method=submitted_values['payment_method'],
                note=submitted_values['note'],
                allowed_payment_methods=dict(
                    Order.PAYMENT_METHODS
                ),
            )
        except _CoreCommerceError as exc:
            error_messages = {
                'required_fields': (
                    "لطفاً تمام فیلدهای الزامی را پر کنید"
                ),
                'invalid_address': (
                    "آدرس تحویل باید حداقل ۱۰ کاراکتر باشد"
                ),
                'invalid_phone': (
                    "شماره تماس باید یک شماره موبایل "
                    "۱۱ رقمی معتبر باشد"
                ),
                'invalid_postal': (
                    "کد پستی باید دقیقاً ۱۰ رقم باشد"
                ),
                'note_too_long': (
                    "توضیحات سفارش بیش از حد طولانی است"
                ),
                'invalid_payment': (
                    "روش پرداخت معتبر نیست"
                ),
                'online_disabled': (
                    "پرداخت آنلاین هنوز به درگاه واقعی "
                    "متصل نشده است. فعلاً پرداخت در محل "
                    "را انتخاب کنید."
                ),
            }

            field_by_code = {
                'invalid_address': 'address',
                'invalid_phone': 'phone',
                'invalid_postal': 'postal_code',
                'note_too_long': 'note',
                'invalid_payment': 'payment_method',
                'online_disabled': 'payment_method',
            }

            field_errors = {}
            if exc.code == 'required_fields':
                if not str(submitted_values['address']).strip():
                    field_errors['address'] = 'آدرس تحویل را وارد کنید.'
                if not str(submitted_values['postal_code']).strip():
                    field_errors['postal_code'] = 'کد پستی را وارد کنید.'
                if not str(submitted_values['phone']).strip():
                    field_errors['phone'] = 'شماره تماس را وارد کنید.'
            elif exc.code in field_by_code:
                field_errors[field_by_code[exc.code]] = error_messages[exc.code]

            messages.error(
                request,
                error_messages.get(
                    exc.code,
                    'اطلاعات واردشده معتبر نیست.',
                ),
            )

            # Keep the submitted values across the redirect so a single
            # invalid field never clears the customer's address/phone/note.
            # The redirect preserves the existing PRG behaviour and tests.
            request.session['checkout_draft'] = submitted_values
            request.session['checkout_errors'] = field_errors
            return redirect('first:checkout')

        try:
            order = _core_place_order(
                cart_model=Cart,
                cart_item_model=CartItem,
                order_model=Order,
                order_item_model=OrderItem,
                product_model=Product,
                variant_model=ProductVariant,
                user=request.user,
                cart=cart,
                payload=payload,
            )
        except _CoreCommerceError as exc:
            data = exc.context
            errors = {
                'empty_cart': "سبد خرید شما خالی است",
                'invalid_item': (
                    "یکی از اقلام سبد خرید معتبر نیست"
                ),
                'product_inactive': (
                    f"محصول «{data.get('product_name')}» "
                    "دیگر فعال نیست"
                ),
                'variant_missing': (
                    f"تنوع انتخاب‌شده برای "
                    f"«{data.get('product_name')}» "
                    "دیگر موجود نیست"
                ),
                'variant_stock': (
                    f"موجودی «{data.get('variant_name')}» "
                    "کافی نیست"
                ),
                'variant_required': (
                    f"برای «{data.get('product_name')}» "
                    "باید تنوع محصول انتخاب شود"
                ),
                'product_stock': (
                    f"موجودی «{data.get('product_name')}» "
                    "کافی نیست"
                ),
            }
            messages.error(
                request,
                "❌ " + errors[exc.code],
            )
            return redirect('first:cart')

        return redirect(
            'first:order_success',
            order_number=order.order_number,
        )

    return render(
        request,
        'cart/checkout.html',
        _checkout_context(),
    )




@login_required
def order_success(request, order_number):
    order = _core_get_order_for_user(
        Order,
        order_number=order_number,
        user=request.user,
    )
    return render(
        request,
        'cart/order_success.html',
        {'order': order},
    )


@login_required
def order_detail(request, order_number):
    (
        order,
        open_cancel_request,
        open_return_request,
    ) = _core_get_order_detail(
        Order,
        order_number=order_number,
        user=request.user,
    )

    status_flow = ['pending', 'paid', 'processing', 'shipped', 'delivered']
    status_index = (
        status_flow.index(order.status)
        if order.status in status_flow
        else -1
    )

    return render(
        request,
        'cart/order_detail.html',
        {
            'order': order,
            'open_cancel_request': (
                open_cancel_request
            ),
            'open_return_request': (
                open_return_request
            ),
            'status_index': status_index,
        },
    )


@login_required
def user_orders(request):
    raw_code = (
        request.GET.get('order_code')
        or request.GET.get('order_number')
        or request.GET.get('q')
        or ''
    )

    context = _core_user_orders_data(
        Order,
        user=request.user,
        raw_code=raw_code,
    )

    return render(
        request,
        'cart/user_orders.html',
        context,
    )



# ============================================
# ویوهای علاقه‌مندی‌ها
# ============================================

@login_required
def wishlist_view(request):
    return render(
        request,
        'products/wishlist.html',
        {
            'wishlist_items': (
                _core_wishlist_items(
                    Wishlist,
                    request.user,
                )
            ),
        },
    )


@require_POST
@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True,
    )

    created = _core_add_to_wishlist(
        Wishlist,
        user=request.user,
        product=product,
    )

    if created:
        messages.success(
            request,
            f"❤️ {product.name} به علاقه‌مندی‌های شما اضافه شد",
        )
    else:
        messages.info(
            request,
            f"{product.name} قبلاً در علاقه‌مندی‌های شما وجود دارد",
        )

    return redirect(
        request.META.get(
            'HTTP_REFERER',
            'first:product_list',
        )
    )


@require_POST
@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
    )

    _core_remove_from_wishlist(
        Wishlist,
        user=request.user,
        product=product,
    )

    messages.success(
        request,
        f"💔 {product.name} از علاقه‌مندی‌های شما حذف شد",
    )

    return redirect(
        request.META.get(
            'HTTP_REFERER',
            'first:wishlist',
        )
    )



# ============================================
# ویوهای مدیریت (ادمین و مالک)
# ============================================

def get_user_permissions(user):
    """دریافت لیست دسترسی‌های یک کاربر"""
    if user.is_owner:
        return list(AdminPermission.objects.filter(is_active=True).values_list('name', flat=True))

    if not user.is_admin:
        return []

    # دسترسی‌های شخصی
    custom_perms = list(AdminUserPermission.objects.filter(
        user=user,
        is_allowed=True
    ).values_list('permission__name', flat=True))

    # دسترسی‌های از طریق نقش
    role_perms = []
    for role in user.admin_roles.filter(is_active=True):
        role_perms.extend(role.permissions.values_list('name', flat=True))

    return list(set(custom_perms + role_perms))

@permission_required('dashboard')
def admin_dashboard(request):
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_users = User.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()

    recent_orders = Order.objects.all().order_by('-created_at')[:10]

    # دریافت دسترسی‌های کاربر جاری
    user_permissions = get_user_permissions(request.user)

    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_users': total_users,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
        'user_permissions': user_permissions,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)

\
@permission_required('products_view')
def admin_products(request):
    products, categories = _core_admin_product_data(
        Product,
        Category,
        search=request.GET.get('search'),
        category_id=request.GET.get('category'),
        status=request.GET.get('status'),
    )

    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'dashboard/admin_products.html',
        {
            'page_obj': page_obj,
            'categories': categories,
        },
    )


@permission_required('products_add')
def admin_add_product(request):
    context = _core_admin_product_form_context(
        category_model=Category,
        brand_model=Brand,
        product_type_model=ProductType,
        tag_model=Tag,
        color_model=Color,
        form_data=(
            request.POST
            if request.method == 'POST'
            else None
        ),
    )

    if request.method != 'POST':
        return render(
            request,
            'dashboard/admin_add_product.html',
            context,
        )

    try:
        product = _core_create_product_from_request(
            request,
            product_model=Product,
            product_image_model=ProductImage,
            product_variant_model=ProductVariant,
            tag_model=Tag,
            color_model=Color,
            prepare_image=prepare_uploaded_image,
        )
        messages.success(
            request,
            f'✅ محصول «{product.name}» با موفقیت اضافه شد.',
        )
        return redirect('first:admin_products')

    except ValidationError as exc:
        messages.error(
            request,
            f"❌ {' '.join(exc.messages)}",
        )
    except (ValueError, TypeError) as exc:
        messages.error(
            request,
            f'❌ اطلاعات واردشده معتبر نیست: {exc}',
        )
    except Exception:
        messages.error(
            request,
            '❌ ثبت محصول انجام نشد. اطلاعات و تصاویر را بررسی کنید.',
        )

    return render(
        request,
        'dashboard/admin_add_product.html',
        context,
        status=400,
    )



def _v7_decimal(value, label, required=False):
    return _core_parse_nonnegative_decimal(
        value,
        label,
        required=required,
    )



def _v7_int(value, label, default=0):
    return _core_parse_nonnegative_int(
        value,
        label,
        default=default,
    )



def _v7_slug(*args, **kwargs):
    return build_unique_product_slug(Product, *args, **kwargs)


def _v7_edit_product(
    request,
    product_id,
    return_to_site=False,
):
    product = get_object_or_404(
        Product.objects.prefetch_related(
            'variants',
            'images',
            'tags',
        ),
        pk=product_id,
    )

    template = 'dashboard/admin_edit_product_site.html'

    context = _core_admin_product_form_context(
        category_model=Category,
        brand_model=Brand,
        product_type_model=ProductType,
        tag_model=Tag,
        color_model=Color,
        product=product,
    )

    if request.method != 'POST':
        return render(
            request,
            template,
            context,
        )

    try:
        product = _core_update_product_from_request(
            request,
            product,
            product_model=Product,
            product_image_model=ProductImage,
            product_variant_model=ProductVariant,
            category_model=Category,
            brand_model=Brand,
            product_type_model=ProductType,
            tag_model=Tag,
            color_model=Color,
            prepare_image=prepare_uploaded_image,
            slug_builder=_v7_slug,
        )

        messages.success(
            request,
            (
                f"✅ محصول «{product.name}» "
                "با موفقیت ویرایش شد"
            ),
        )

        if return_to_site and product.is_active:
            return redirect(
                'first:product_detail',
                slug=product.slug,
            )

        return redirect('first:admin_products')

    except ValidationError as exc:
        messages.error(
            request,
            "❌ " + " ".join(exc.messages),
        )
    except Exception:
        messages.error(
            request,
            (
                "❌ ذخیره محصول انجام نشد. "
                "اطلاعات واردشده را بررسی کنید."
            ),
        )

    product.refresh_from_db()
    context['product'] = product
    context['form_data'] = request.POST

    return render(
        request,
        template,
        context,
        status=400,
    )


@permission_required('products_edit')
def admin_edit_product(
    request,
    product_id,
):
    return _v7_edit_product(
        request,
        product_id,
        return_to_site=False,
    )

@permission_required('products_edit')
def admin_edit_product_from_site(
    request,
    product_id,
):
    return _v7_edit_product(
        request,
        product_id,
        return_to_site=True,
    )

\
@permission_required('products_delete')
@require_POST
def admin_delete_product(request, product_id):
    product_name = _core_deactivate_product(
        Product,
        ProductVariant,
        product_id,
    )

    messages.success(
        request,
        (
            f"✅ محصول {product_name} "
            "غیرفعال شد"
        ),
    )

    return redirect(
        'first:admin_products'
    )


def _admin_orders_for_request(request):
    orders = (
        _core_admin_order_queryset(Order)
        .select_related('user')
        .prefetch_related('items')
    )

    query = (request.GET.get('q') or '').strip()
    status = (request.GET.get('status') or '').strip()
    payment = (request.GET.get('payment') or '').strip()
    sort = (request.GET.get('sort') or 'newest').strip()

    if query:
        orders = orders.filter(
            Q(order_number__icontains=query)
            | Q(user__username__icontains=query)
            | Q(user__email__icontains=query)
            | Q(phone__icontains=query)
        )

    valid_statuses = {value for value, _ in Order.STATUS_CHOICES}
    if status in valid_statuses:
        orders = orders.filter(status=status)
    else:
        status = ''

    if payment == 'paid':
        orders = orders.filter(is_paid=True)
    elif payment == 'unpaid':
        orders = orders.filter(is_paid=False)
    else:
        payment = ''

    sort_map = {
        'newest': ('-created_at',),
        'oldest': ('created_at',),
        'amount_desc': ('-total', '-created_at'),
        'amount_asc': ('total', '-created_at'),
        'paid_first': ('-is_paid', '-created_at'),
        'unpaid_first': ('is_paid', '-created_at'),
    }
    ordering = sort_map.get(sort, sort_map['newest'])
    if sort not in sort_map:
        sort = 'newest'
    orders = orders.order_by(*ordering)

    return orders, {
        'q': query,
        'status': status,
        'payment': payment,
        'sort': sort,
    }


@permission_required('orders_view')
def admin_orders(request):
    orders, filters = _admin_orders_for_request(request)

    paginator = Paginator(orders, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    return render(
        request,
        'dashboard/admin_orders.html',
        {
            'page_obj': page_obj,
            'filters': filters,
            'status_choices': Order.STATUS_CHOICES,
            'query_string': query_params.urlencode(),
        },
    )


@permission_required('orders_view')
def admin_orders_pdf(request):
    from .order_pdf import build_orders_pdf

    orders, filters = _admin_orders_for_request(request)

    raw_selected = (request.GET.get('selected') or '').strip()
    selected_ids = []
    if raw_selected:
        for value in raw_selected.split(','):
            value = value.strip()
            if value.isdigit():
                selected_ids.append(int(value))

    if selected_ids:
        orders = orders.filter(pk__in=selected_ids)

    pdf_bytes = build_orders_pdf(
        orders,
        filters=filters,
        selected=bool(selected_ids),
    )
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    stamp = timezone.localtime().strftime('%Y%m%d-%H%M')
    response['Content-Disposition'] = (
        f'attachment; filename="orders-{stamp}.pdf"'
    )
    return response


@permission_required('orders_view')
def admin_order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('user').prefetch_related('items'),
        pk=order_id,
    )

    return render(
        request,
        'dashboard/admin_order_detail.html',
        {'order': order},
    )


@permission_required('users_view')
def admin_users(request):
    users = User.objects.all().order_by('-created_at')

    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'dashboard/admin_users.html', context)

@permission_required('orders_update')
@require_POST
def update_order_status(request, order_id):
    try:
        order, result = _core_transition_order(
            Order,
            order_id=order_id,
            requested=request.POST.get('status'),
        )
    except _CoreCommerceError as exc:
        if exc.code != 'invalid_transition':
            raise

        messages.error(
            request,
            (
                "❌ این تغییر وضعیت مجاز نیست. "
                "لغو و مرجوعی باید از بخش "
                "مربوطه انجام شود."
            ),
        )
        return redirect(
            'first:admin_orders'
        )

    if result == 'unchanged':
        return redirect(
            'first:admin_orders'
        )

    messages.success(
        request,
        (
            f"✅ وضعیت سفارش "
            f"#{order.order_number} "
            f"به {order.get_status_display()} "
            "تغییر کرد"
        ),
    )

    return redirect(
        'first:admin_orders'
    )


@permission_required('reviews_view')
def admin_reviews(request):
    reviews, counts = _core_admin_review_data(
        ProductReview,
        request.GET.get('status'),
    )

    paginator = Paginator(reviews, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        **counts,
    }
    return render(request, 'dashboard/admin_reviews.html', context)


@permission_required('reviews_verify')
@require_POST
def review_verify(request, review_id):
    review = get_object_or_404(ProductReview, id=review_id)
    _core_verify_product_review(review)

    messages.success(
        request,
        f"✅ نظر {review.user.username} برای محصول {review.product.name} تایید شد",
    )
    return redirect('first:admin_reviews')


@permission_required('reviews_delete')
@require_POST
def review_delete(request, review_id):
    review = get_object_or_404(ProductReview, id=review_id)
    _core_delete_product_review(review)

    messages.success(request, "✅ نظر با موفقیت حذف شد")
    return redirect('first:admin_reviews')



# ============================================
# ویوهای مدیریت ادمین‌ها (فقط مالک)
# ============================================

@owner_required
def manage_admins(request):
    admins = User.objects.filter(role='admin')
    users = User.objects.filter(role='user')
    roles_count = AdminRole.objects.filter(is_active=True).count()

    context = {
        'admins': admins,
        'users': users,
        'roles_count': roles_count,
    }
    return render(request, 'dashboard/manage_admins.html', context)

@owner_required
@require_POST
def make_admin(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user.role == 'owner' or user.is_superuser:
        messages.error(request, "❌ نمی‌توانید مالک را تغییر دهید")
        return redirect('first:manage_admins')

    user.role = 'admin'
    user.is_staff = True
    user.save()
    messages.success(request, f"✅ {user.username} به ادمین ارتقا یافت")
    return redirect('first:manage_admins')

@owner_required
@require_POST
def remove_admin(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user.role == 'owner' or user.is_superuser:
        messages.error(request, "❌ نمی‌توانید مالک را تغییر دهید")
        return redirect('first:manage_admins')

    user.role = 'user'
    user.is_staff = False
    user.save()
    messages.success(request, f"✅ نقش ادمین از {user.username} حذف شد")
    return redirect('first:manage_admins')

@owner_required
@require_POST
def toggle_user_active(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user.role == 'owner' or user.is_superuser:
        messages.error(request, "❌ نمی‌توانید مالک را تغییر دهید")
        return redirect('first:manage_admins')

    user.is_active = not user.is_active
    user.save()
    status = "فعال" if user.is_active else "غیرفعال"
    messages.success(request, f"✅ کاربر {user.username} {status} شد")
    return redirect('first:manage_admins')


# ============================================
# ویوهای مدیریت دسترسی (فقط مالک)
# ============================================

@owner_required
def manage_admin_permissions(request):
    default_permissions = [
        ('dashboard', 'داشبورد مدیریت'),
        ('products_view', 'مشاهده محصولات'),
        ('products_add', 'افزودن محصول'),
        ('products_edit', 'ویرایش محصول'),
        ('products_delete', 'حذف محصول'),
        ('orders_view', 'مشاهده سفارشات'),
        ('orders_update', 'تغییر وضعیت سفارش'),
        ('support_view', 'مشاهده تیکت‌های پشتیبانی'),
        ('support_reply', 'پاسخگویی به تیکت‌های پشتیبانی'),
        ('returns_manage', 'مدیریت لغو و مرجوعی سفارش‌ها'),
        ('reviews_view', 'مشاهده نظرات'),
        ('reviews_verify', 'تایید نظرات'),
        ('reviews_delete', 'حذف نظرات'),
        ('users_view', 'مشاهده کاربران'),
        ('users_manage', 'مدیریت کاربران'),
        ('admins_manage', 'مدیریت ادمین‌ها'),
        ('warehouse_view', 'مشاهده انبار'),
        ('warehouse_edit', 'ویرایش انبار'),
        ('site_settings', 'تنظیمات ظاهر'),
        ('reports_view', 'مشاهده گزارشات'),
    ]

    for name, label in default_permissions:
        permission, _ = (
            AdminPermission.objects
            .get_or_create(
                name=name,
                defaults={
                    'label': label,
                    'is_active': True,
                },
            )
        )

        changed = []

        if permission.label != label:
            permission.label = label
            changed.append('label')

        if not permission.is_active:
            permission.is_active = True
            changed.append('is_active')

        if changed:
            permission.save(
                update_fields=changed
            )

    admins = (
        User.objects
        .filter(role='admin')
        .order_by('username')
    )

    roles = (
        AdminRole.objects
        .filter(is_active=True)
        .prefetch_related(
            'permissions'
        )
    )

    if request.method == 'POST':
        admin = get_object_or_404(
            User,
            id=request.POST.get(
                'admin_id'
            ),
            role='admin',
        )

        role_ids = [
            value
            for value
            in request.POST.getlist(
                'roles'
            )
            if str(value).isdigit()
        ]

        selected_names = set(
            request.POST.getlist(
                'permissions'
            )
        )

        selected_permissions = list(
            AdminPermission.objects.filter(
                name__in=selected_names,
                is_active=True,
            )
        )

        with transaction.atomic():
            admin.admin_roles.set(
                AdminRole.objects.filter(
                    id__in=role_ids,
                    is_active=True,
                )
            )

            AdminUserPermission.objects.filter(
                user=admin
            ).delete()

            AdminUserPermission.objects.bulk_create(
                [
                    AdminUserPermission(
                        user=admin,
                        permission=permission,
                        is_allowed=True,
                    )
                    for permission
                    in selected_permissions
                ]
            )

        messages.success(
            request,
            (
                f"✅ دسترسی‌های {admin.username} "
                "با موفقیت به‌روزرسانی شد"
            ),
        )

        return redirect(
            'first:manage_admin_permissions'
        )

    groups = {
        'داشبورد': [],
        'محصولات': [],
        'سفارشات': [],
        'پشتیبانی': [],
        'لغو و مرجوعی': [],
        'نظرات': [],
        'کاربران': [],
        'ادمین‌ها': [],
        'انبار': [],
        'تنظیمات': [],
        'گزارشات': [],
    }

    all_permissions = list(
        AdminPermission.objects.filter(
            is_active=True
        ).order_by('id')
    )

    for permission in all_permissions:
        name = permission.name

        if name == 'dashboard':
            groups['داشبورد'].append(
                permission
            )
        elif name.startswith('products'):
            groups['محصولات'].append(
                permission
            )
        elif name.startswith('orders'):
            groups['سفارشات'].append(
                permission
            )
        elif name.startswith('support'):
            groups['پشتیبانی'].append(
                permission
            )
        elif name.startswith('returns'):
            groups[
                'لغو و مرجوعی'
            ].append(permission)
        elif name.startswith('reviews'):
            groups['نظرات'].append(
                permission
            )
        elif name.startswith('users'):
            groups['کاربران'].append(
                permission
            )
        elif name.startswith('admins'):
            groups['ادمین‌ها'].append(
                permission
            )
        elif name.startswith('warehouse'):
            groups['انبار'].append(
                permission
            )
        elif name.startswith('site'):
            groups['تنظیمات'].append(
                permission
            )
        elif name.startswith('reports'):
            groups['گزارشات'].append(
                permission
            )

    grouped_permissions = {
        key: values
        for key, values
        in groups.items()
        if values
    }

    admin_permissions = {}

    for admin in admins:
        custom_names = set(
            AdminUserPermission.objects
            .filter(
                user=admin,
                is_allowed=True,
            )
            .values_list(
                'permission__name',
                flat=True,
            )
        )

        role_ids = list(
            admin.admin_roles
            .filter(is_active=True)
            .values_list(
                'id',
                flat=True,
            )
        )

        role_names = set(
            AdminPermission.objects
            .filter(
                roles__users=admin,
                roles__is_active=True,
                is_active=True,
            )
            .values_list(
                'name',
                flat=True,
            )
        )

        admin_permissions[
            admin.id
        ] = {
            'custom': sorted(
                custom_names
            ),
            'roles': role_ids,
            'all': sorted(
                custom_names
                | role_names
            ),
        }

    return render(
        request,
        (
            'dashboard/'
            'manage_admin_permissions.html'
        ),
        {
            'admins': admins,
            'grouped_permissions': (
                grouped_permissions
            ),
            'admin_permissions': (
                admin_permissions
            ),
            'owner_only_permissions': [
                'users_view',
                'users_manage',
                'admins_manage',
                'warehouse_view',
                'warehouse_edit',
                'site_settings',
            ],
            'roles': roles,
        },
    )

@owner_required
@require_POST
def toggle_admin_permission(request, user_id, permission_id):
    admin = get_object_or_404(User, id=user_id, role='admin')
    permission = get_object_or_404(AdminPermission, id=permission_id)

    perm, created = AdminUserPermission.objects.get_or_create(
        user=admin,
        permission=permission
    )
    perm.is_allowed = not perm.is_allowed
    perm.save()

    status = "فعال" if perm.is_allowed else "غیرفعال"
    messages.success(request, f"✅ دسترسی {permission.label} برای {admin.username} {status} شد")
    return redirect('first:manage_admin_permissions')


# ============================================
# ویوهای انبار (فقط مالک)
# ============================================

def _effective_product_stock(product):
    if not product.has_variants:
        return product.stock

    cache = getattr(product, '_prefetched_objects_cache', {})
    variants = cache.get('variants')

    if variants is None:
        variants = product.variants.all()

    return sum(
        variant.stock
        for variant in variants
        if variant.is_active
    )

@permission_required('warehouse_view')
def warehouse(request):
    products = list(
        Product.objects
        .filter(is_active=True)
        .prefetch_related('variants')
    )

    for product in products:
        product.display_stock = _effective_product_stock(product)

    low_stock_products = sorted(
        [
            product
            for product in products
            if 0 < product.display_stock <= 5
        ],
        key=lambda item: item.display_stock,
    )[:10]

    out_of_stock_products = [
        product
        for product in products
        if product.display_stock == 0
    ]

    return render(
        request,
        'dashboard/warehouse.html',
        {
            'total_products': len(products),
            'total_stock': sum(
                product.display_stock
                for product in products
            ),
            'total_sales': (
                Product.objects.aggregate(
                    total=Sum('sales_count')
                )['total']
                or 0
            ),
            'total_orders': Order.objects.count(),
            'total_revenue': (
                Order.objects
                .filter(is_paid=True)
                .aggregate(total=Sum('total'))['total']
                or 0
            ),
            'in_stock_count': (
                len(products) - len(out_of_stock_products)
            ),
            'out_of_stock_count': len(out_of_stock_products),
            'low_stock_count': len(low_stock_products),
            'low_stock_products': low_stock_products,
            'best_selling_products': (
                Product.objects
                .filter(is_active=True)
                .order_by('-sales_count')[:10]
            ),
            'out_of_stock_products': out_of_stock_products,
            'recent_orders': (
                Order.objects
                .filter(is_paid=True)
                .order_by('-created_at')[:10]
            ),
        },
    )

@permission_required('warehouse_view')
def warehouse_products(request):
    products = _core_warehouse_products_data(
        Product,
        effective_stock=_effective_product_stock,
        search=request.GET.get('search'),
        stock_status=request.GET.get(
            'stock_status'
        ),
    )

    page_obj = Paginator(
        products,
        20,
    ).get_page(
        request.GET.get('page')
    )

    return render(
        request,
        'dashboard/warehouse_products.html',
        {'page_obj': page_obj},
    )


@permission_required('warehouse_edit')
@require_POST
def update_stock(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
    )

    try:
        new_stock = _core_update_product_stock(
            product,
            request.POST.get('stock', ''),
        )
    except _CoreCommerceError as exc:
        if (
            exc.code
            == 'variant_stock_managed_separately'
        ):
            messages.error(
                request,
                (
                    "❌ موجودی محصول دارای تنوع باید "
                    "از ویرایش تنوع‌ها تغییر کند"
                ),
            )
        elif exc.code == 'invalid_stock':
            messages.error(
                request,
                (
                    "❌ موجودی باید عددی صفر "
                    "یا بیشتر باشد"
                ),
            )
        else:
            raise

        return redirect(
            'first:warehouse_products'
        )

    messages.success(
        request,
        (
            f"✅ موجودی {product.name} "
            f"به {new_stock} به‌روزرسانی شد"
        ),
    )
    return redirect(
        'first:warehouse_products'
    )



# ============================================
# ویوهای Ajax
# ============================================

\
def _unique_catalog_slug(model, name, exclude_pk=None):
    return _core_unique_catalog_slug(
        model,
        name,
        exclude_pk=exclude_pk,
    )



\
def _ajax_catalog_payload(request):
    if len(request.body) > 64 * 1024:
        raise ValidationError('حجم درخواست بیش از حد مجاز است.')
    data = json.loads(request.body or b'{}')
    if not isinstance(data, dict):
        raise ValidationError('داده ارسالی معتبر نیست.')
    return data


def _catalog_response(item, status=200, existing=False):
    return JsonResponse(dict(success=True, id=item.pk, name=item.name, slug=item.slug,
                             parent_id=getattr(item, 'parent_id', None), existing=existing), status=status)


def _ajax_create_named_item(request, model, label):
    try:
        data = _ajax_catalog_payload(request)
        with transaction.atomic():
            item, error, existing = _core_create_named_catalog_item(
                model, data.get('name'), slug=data.get('slug'), parent_id=data.get('parent_id'))
            if error:
                raise ValidationError(f'نام {label} الزامی است و باید در محدوده طول مجاز باشد.')
        return _catalog_response(item, 200 if existing else 201, existing)
    except ValidationError as exc:
        return JsonResponse({'success': False, 'error': ' '.join(exc.messages)}, status=400)
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'داده ارسالی معتبر نیست.'}, status=400)


def _ajax_edit_named_item(request, model, item_id):
    item = get_object_or_404(model, pk=item_id)
    try:
        data = _ajax_catalog_payload(request)
        with transaction.atomic():
            item = model.objects.select_for_update().get(pk=item_id)
            update_named_catalog_item(item, name=data.get('name'), slug=data.get('slug'),
                                      parent_id=data.get('parent_id', getattr(item, 'parent_id', None)))
        return _catalog_response(item)
    except ValidationError as exc:
        return JsonResponse({'success': False, 'error': ' '.join(exc.messages)}, status=400)
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'داده ارسالی معتبر نیست.'}, status=400)


@permission_required('products_edit')
@require_POST
def ajax_add_category(request):
    return _ajax_create_named_item(
        request,
        Category,
        'دسته‌بندی',
    )


\
@permission_required('products_edit')
@require_POST
def ajax_add_brand(request):
    return _ajax_create_named_item(
        request,
        Brand,
        'برند',
    )


\
@permission_required('products_edit')
@require_POST
def ajax_add_product_type(request):
    return _ajax_create_named_item(
        request,
        ProductType,
        'نوع محصول',
    )


\
@permission_required('products_edit')
@require_POST
def ajax_add_color(request):
    try:
        if (
            request.content_type
            and request.content_type.startswith(
                'application/json'
            )
        ):
            data = json.loads(request.body)
            color_image = None
        else:
            data = request.POST
            color_image = request.FILES.get('image')

        prepared_image = None
        if color_image:
            prepared_image = prepare_uploaded_image(
                color_image,
                min_width=80,
                min_height=80,
                max_dimension=600,
                max_file_size=4 * 1024 * 1024,
                name_prefix='color',
            )

        color, error, existing = _core_upsert_color(
            Color,
            name=data.get('name'),
            code=data.get('code'),
            image=prepared_image,
        )

        if error == 'required':
            return JsonResponse(
                {
                    'success': False,
                    'error': 'نام رنگ الزامی است',
                },
                status=400,
            )

        if error == 'invalid_code':
            return JsonResponse(
                {
                    'success': False,
                    'error': (
                        'کد رنگ باید دقیقاً به شکل '
                        '#RRGGBB باشد؛ مثال #FF0000'
                    ),
                },
                status=400,
            )

        return JsonResponse(
            {
                'success': True,
                'id': color.id,
                'name': color.name,
                'code': color.code,
                'image_url': (
                    color.image.url
                    if color.image
                    else ''
                ),
                'existing': existing,
            },
            status=200 if existing else 201,
        )

    except ValidationError as exc:
        return JsonResponse(
            {
                'success': False,
                'error': ' '.join(exc.messages),
            },
            status=400,
        )
    except json.JSONDecodeError:
        return JsonResponse(
            {
                'success': False,
                'error': 'بدنه JSON معتبر نیست',
            },
            status=400,
        )
    except Exception:
        return JsonResponse(
            {
                'success': False,
                'error': (
                    'ثبت رنگ انجام نشد. '
                    'دوباره تلاش کنید.'
                ),
            },
            status=500,
        )



\
@permission_required('products_edit')
def ajax_delete_category(request, item_id):
    if request.method != 'POST':
        return JsonResponse(
            {
                'success': False,
                'error': 'فقط درخواست POST مجاز است.',
            },
            status=405,
        )

    result, count = _core_delete_catalog_item(
        Category,
        Product,
        item_id,
        relation_field='category',
        reject_children=True,
    )

    if result == 'not_found':
        return JsonResponse(
            {
                'success': False,
                'error': 'دسته‌بندی پیدا نشد.',
            },
            status=404,
        )

    if result == 'in_use':
        return JsonResponse(
            {
                'success': False,
                'error': (
                    f'این دسته‌بندی در {count} '
                    'محصول استفاده شده است. ابتدا دسته‌بندی '
                    'آن محصولات را تغییر بده.'
                ),
            },
            status=409,
        )

    if result == 'has_children':
        return JsonResponse(
            {
                'success': False,
                'error': (
                    'این دسته‌بندی زیرمجموعه دارد و '
                    'فعلاً قابل حذف نیست.'
                ),
            },
            status=409,
        )

    return JsonResponse({'success': True})


\
@permission_required('products_edit')
def ajax_delete_brand(request, item_id):
    if request.method != 'POST':
        return JsonResponse(
            {
                'success': False,
                'error': 'فقط درخواست POST مجاز است.',
            },
            status=405,
        )

    result, count = _core_delete_catalog_item(
        Brand,
        Product,
        item_id,
        relation_field='brand',
    )

    if result == 'not_found':
        return JsonResponse(
            {
                'success': False,
                'error': 'برند پیدا نشد.',
            },
            status=404,
        )

    if result == 'in_use':
        return JsonResponse(
            {
                'success': False,
                'error': (
                    f'این برند در {count} محصول '
                    'استفاده شده است. ابتدا برند آن '
                    'محصولات را تغییر بده.'
                ),
            },
            status=409,
        )

    return JsonResponse({'success': True})


\
@permission_required('products_edit')
def ajax_delete_product_type(request, item_id):
    if request.method != 'POST':
        return JsonResponse(
            {
                'success': False,
                'error': 'فقط درخواست POST مجاز است.',
            },
            status=405,
        )

    result, count = _core_delete_catalog_item(
        ProductType,
        Product,
        item_id,
        relation_field='product_type',
    )

    if result == 'not_found':
        return JsonResponse(
            {
                'success': False,
                'error': 'نوع محصول پیدا نشد.',
            },
            status=404,
        )

    if result == 'in_use':
        return JsonResponse(
            {
                'success': False,
                'error': (
                    f'این نوع محصول در {count} '
                    'محصول استفاده شده است. ابتدا نوع '
                    'آن محصولات را تغییر بده.'
                ),
            },
            status=409,
        )

    return JsonResponse({'success': True})


# ============================================
# ویوهای ویرایشگر بصری (فقط مالک)
# ============================================

@owner_required
def customizer(request):
    site = SiteSettings.get_settings()
    return render(
        request,
        'dashboard/customizer.html',
        {
            'customizer_payload': (
                _core_customizer_payload(site)
            )
        },
    )



def _customizer_number(value, minimum, maximum, default=0):
    return _core_customizer_number(
        value,
        minimum,
        maximum,
        default,
    )



def _customizer_url(value, *, image=False):
    return _core_customizer_url(
        value,
        image=image,
    )



def _clean_customizer_styles(styles):
    return _core_clean_customizer_styles(
        styles
    )



def _clean_customizer_rule(rule):
    return _core_clean_customizer_rule(
        rule
    )


@owner_required
def customizer_save(request):
    if request.method != 'POST':
        return JsonResponse(
            {
                'success': False,
                'error': 'متد غیرمجاز',
            },
            status=405,
        )

    try:
        if len(request.body) > 1024 * 1024:
            return JsonResponse(
                {
                    'success': False,
                    'error': (
                        'حجم تغییرات بیش از حد مجاز است.'
                    ),
                },
                status=413,
            )

        data = json.loads(request.body)
        result = _core_save_customizer_state(
            SiteSettings.get_settings(),
            data,
        )
        return JsonResponse({
            'success': True,
            **result,
        })

    except ValidationError:
        return JsonResponse(
            {
                'success': False,
                'error': (
                    'ساختار یا تعداد تغییرات معتبر نیست.'
                ),
            },
            status=400,
        )
    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return JsonResponse(
            {
                'success': False,
                'error': 'داده ارسالی معتبر نیست.',
            },
            status=400,
        )
    except Exception:
        return JsonResponse(
            {
                'success': False,
                'error': 'ذخیره تغییرات انجام نشد.',
            },
            status=500,
        )


@owner_required
def customizer_reset(request):
    if request.method != 'POST':
        return JsonResponse(
            {
                'success': False,
                'error': 'متد غیرمجاز',
            },
            status=405,
        )

    try:
        site = SiteSettings.get_settings()
        result = _core_reset_customizer_state(site)

        # shop_core is shared with older storefronts whose reset palette is
        # cosmetics-specific. This perfume app restores its own canonical
        # palette after clearing visual rules.
        theme = _CUSTOMIZER_DEFAULT_THEME.copy()
        site.customizer_theme = theme
        site.primary_color = theme['primary']
        site.secondary_color = theme['secondary']
        site.accent_color = theme['accent']
        site.background_color = theme['bg']
        site.text_color = theme['text']
        site.save(update_fields=[
            'customizer_theme',
            'primary_color',
            'secondary_color',
            'accent_color',
            'background_color',
            'text_color',
            'updated_at',
        ])
        result['theme'] = theme

        return JsonResponse({
            'success': True,
            **result,
        })
    except Exception:
        return JsonResponse(
            {
                'success': False,
                'error': 'بازنشانی انجام نشد.',
            },
            status=500,
        )


@owner_required
def customizer_upload(request):
    """آپلود تصویر در ویرایشگر بصری"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'متد غیرمجاز'}, status=405)

    try:
        uploaded_file = request.FILES.get('file')
        prepared_file = prepare_uploaded_image(
            uploaded_file,
            min_width=80,
            min_height=80,
            max_dimension=2400,
            max_file_size=10 * 1024 * 1024,
            name_prefix='visual',
        )
        from django.core.files.storage import default_storage
        import uuid

        filename = f'customizer/{uuid.uuid4().hex}.webp'
        saved_path = default_storage.save(filename, prepared_file)
        url = default_storage.url(saved_path)
        return JsonResponse({'success': True, 'url': url}, status=201)
    except ValidationError as exc:
        return JsonResponse({'success': False, 'error': ' '.join(exc.messages)}, status=400)
    except Exception:
        return JsonResponse({'success': False, 'error': 'آپلود تصویر انجام نشد.'}, status=500)

@owner_required
@require_POST
def customizer_product_save(request):
    try:
        upload = request.FILES.get(
            'main_image'
        )
        prepared_image = None

        if upload:
            prepared_image = prepare_uploaded_image(
                upload,
                min_width=500,
                min_height=500,
                max_dimension=1800,
                max_file_size=8 * 1024 * 1024,
                name_prefix='product',
            )

        product = _core_save_simple_product(
            product_model=Product,
            category_model=Category,
            brand_model=Brand,
            post=request.POST,
            prepared_image=prepared_image,
        )

        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'price': str(product.price),
                'discount_price': (
                    str(product.discount_price)
                    if product.discount_price
                    is not None
                    else None
                ),
                'stock': product.stock,
                'description': product.description,
                'is_available': product.is_available,
                'is_featured': product.is_featured,
                'is_new': product.is_new,
                'category_id': product.category_id,
                'brand_id': product.brand_id,
                'main_image': (
                    product.main_image.url
                    if product.main_image
                    else None
                ),
            },
        })

    except ValidationError as exc:
        return JsonResponse(
            {
                'success': False,
                'error': ' '.join(exc.messages),
            },
            status=400,
        )
    except Exception:
        return JsonResponse(
            {
                'success': False,
                'error': 'ذخیره محصول انجام نشد',
            },
            status=500,
        )


@owner_required
@require_POST
def customizer_product_delete(request, product_id):
    _core_deactivate_product(
        Product,
        ProductVariant,
        product_id,
    )
    return JsonResponse({
        'success': True,
        'deactivated': True,
    })


@owner_required
def customizer_load(request):
    try:
        result = _core_load_customizer_state(
            SiteSettings.get_settings()
        )
        return JsonResponse({
            'success': True,
            **result,
        })
    except Exception:
        return JsonResponse(
            {
                'success': False,
                'error': 'بارگذاری تنظیمات انجام نشد.',
            },
            status=500,
        )



# ============================================
# صفحات خدمات مشتریان
# ============================================

def customer_service_page(request, page_slug):
    page = CUSTOMER_SERVICE_PAGES.get(page_slug)

    if page is None:
        raise Http404(
            'صفحه خدمات مشتریان پیدا نشد.'
        )

    return render(
        request,
        'customer_service.html',
        {
            'page': page,
            'page_slug': page_slug,
        },
    )


@permission_required('products_edit')
@require_POST
def ajax_edit_category(request, item_id):
    return _ajax_edit_named_item(request, Category, item_id)


@permission_required('products_edit')
@require_POST
def ajax_edit_brand(request, item_id):
    return _ajax_edit_named_item(request, Brand, item_id)


@permission_required('products_edit')
@require_POST
def ajax_edit_product_type(request, item_id):
    return _ajax_edit_named_item(request, ProductType, item_id)


@permission_required('products_edit')
@require_POST
def ajax_edit_tag(request, item_id):
    return _ajax_edit_named_item(request, Tag, item_id)


@permission_required('products_edit')
@require_POST
def ajax_add_tag(request):
    return _ajax_create_named_item(request, Tag, 'تگ')


@permission_required('products_edit')
@require_POST
def ajax_delete_tag(request, item_id):
    result, count = _core_delete_catalog_item(Tag, Product, item_id, relation_field='tags')
    if result == 'deleted':
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'تگ در محصول استفاده شده است.' if count else 'تگ یافت نشد.'}, status=409 if count else 404)
