from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import (
    AdminPermission,
    AdminRole,
    AdminUserPermission,
)
from shop_core.accounts.decorators import admin_required, owner_required






def check_admin_permission(
    user,
    permission_name,
):
    """
    Return the effective permission for an admin.

    Priority:
    1) owner -> always allowed
    2) explicit user override -> allow/deny
    3) active role permission
    4) otherwise denied

    Inactive AdminPermission records never grant access.
    """
    if (
        not user
        or not user.is_authenticated
    ):
        return False

    if user.is_owner or user.is_superuser:
        return True

    if not user.is_admin:
        return False

    override = (
        AdminUserPermission.objects
        .select_related('permission')
        .filter(
            user=user,
            permission__name=permission_name,
            permission__is_active=True,
        )
        .first()
    )

    if override is not None:
        return bool(
            override.is_allowed
        )

    return user.admin_roles.filter(
        is_active=True,
        permissions__name=permission_name,
        permissions__is_active=True,
    ).exists()


def get_effective_admin_permissions(user):
    """
    Return active permission names after applying
    role grants and per-user allow/deny overrides.
    """
    if (
        not user
        or not user.is_authenticated
    ):
        return []

    if user.is_owner or user.is_superuser:
        return list(
            AdminPermission.objects.filter(
                is_active=True
            ).values_list(
                'name',
                flat=True,
            )
        )

    if not user.is_admin:
        return []

    permissions = set(
        AdminPermission.objects.filter(
            is_active=True,
            roles__in=user.admin_roles.filter(
                is_active=True
            ),
        ).values_list(
            'name',
            flat=True,
        )
    )

    overrides = (
        AdminUserPermission.objects
        .filter(
            user=user,
            permission__is_active=True,
        )
        .values_list(
            'permission__name',
            'is_allowed',
        )
    )

    for name, is_allowed in overrides:
        if is_allowed:
            permissions.add(name)
        else:
            permissions.discard(name)

    return sorted(permissions)


def permission_required(
    permission_name,
    redirect_url='first:home',
):
    """
    Enforce a named admin permission server-side.

    Hiding a button in HTML is not enough; this
    decorator also blocks direct URL access.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(
            request,
            *args,
            **kwargs,
        ):
            if not request.user.is_authenticated:
                messages.error(
                    request,
                    "❌ لطفاً ابتدا وارد شوید",
                )
                return redirect('first:login')

            if request.user.is_owner:
                return view_func(
                    request,
                    *args,
                    **kwargs,
                )

            if not request.user.is_admin:
                messages.error(
                    request,
                    "⛔ شما دسترسی ادمین ندارید",
                )
                return redirect('first:home')

            if check_admin_permission(
                request.user,
                permission_name,
            ):
                return view_func(
                    request,
                    *args,
                    **kwargs,
                )

            messages.error(
                request,
                (
                    "⛔ شما دسترسی لازم برای "
                    "این بخش را ندارید"
                ),
            )
            return redirect(
                redirect_url
            )

        return wrapper

    return decorator

# ==========================================================
# PERFUME SHOP LOCAL ACCESS POLICY
# ==========================================================

def admin_required(view_func):
    from functools import wraps
    from django.contrib import messages
    from django.shortcuts import redirect

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(
                request,
                '❌ لطفاً ابتدا وارد شوید',
            )
            return redirect('first:login')

        if not (
            getattr(request.user, 'is_admin', False)
            or request.user.is_superuser
        ):
            messages.error(
                request,
                '⛔ شما دسترسی ادمین ندارید',
            )
            return redirect('first:home')

        return view_func(request, *args, **kwargs)

    return wrapper


def owner_required(view_func):
    from functools import wraps
    from django.contrib import messages
    from django.shortcuts import redirect

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(
                request,
                '❌ لطفاً ابتدا وارد شوید',
            )
            return redirect('first:login')

        if not (
            getattr(request.user, 'is_owner', False)
            or request.user.is_superuser
        ):
            messages.error(
                request,
                '⛔ فقط مالک سایت به این بخش دسترسی دارد',
            )
            return redirect('first:home')

        return view_func(request, *args, **kwargs)

    return wrapper

# ============================================================
# PERFUME OWNER SUPERUSER POLICY V3
# ============================================================
from functools import wraps as _p10_wraps
from django.contrib import messages as _p10_messages
from django.shortcuts import redirect as _p10_redirect

_p10_old_admin_required = globals().get("admin_required")
_p10_old_permission_required = globals().get("permission_required")
_p10_old_check = globals().get("check_admin_permission")
_p10_old_get_permissions = globals().get("get_effective_admin_permissions")

def _p10_is_owner(user):
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and (
            getattr(user, "is_superuser", False)
            or getattr(user, "is_owner", False)
        )
    )

def admin_required(view_func):
    old_wrapped = (
        _p10_old_admin_required(view_func)
        if callable(_p10_old_admin_required)
        else None
    )
    @_p10_wraps(view_func)
    def wrapper(request,*args,**kwargs):
        if not request.user.is_authenticated:
            _p10_messages.error(request,"❌ لطفاً ابتدا وارد شوید")
            return _p10_redirect("first:login")
        if _p10_is_owner(request.user):
            return view_func(request,*args,**kwargs)
        if old_wrapped:
            return old_wrapped(request,*args,**kwargs)
        _p10_messages.error(request,"⛔ شما دسترسی ادمین ندارید")
        return _p10_redirect("first:home")
    return wrapper

def owner_required(view_func):
    @_p10_wraps(view_func)
    def wrapper(request,*args,**kwargs):
        if not request.user.is_authenticated:
            _p10_messages.error(request,"❌ لطفاً ابتدا وارد شوید")
            return _p10_redirect("first:login")
        if not _p10_is_owner(request.user):
            _p10_messages.error(request,"⛔ فقط مالک سایت به این بخش دسترسی دارد")
            return _p10_redirect("first:home")
        return view_func(request,*args,**kwargs)
    return wrapper

def check_admin_permission(user, permission_name):
    if _p10_is_owner(user):
        return True
    if callable(_p10_old_check):
        return bool(_p10_old_check(user, permission_name))
    return False

def get_effective_admin_permissions(user):
    if _p10_is_owner(user):
        model = globals().get("AdminPermission")
        if model is not None:
            try:
                return list(
                    model.objects.filter(is_active=True)
                    .values_list("name",flat=True)
                )
            except Exception:
                pass
        return []
    if callable(_p10_old_get_permissions):
        return _p10_old_get_permissions(user)
    return []

def permission_required(permission_name, redirect_url="first:home"):
    old_decorator = (
        _p10_old_permission_required(permission_name, redirect_url)
        if callable(_p10_old_permission_required)
        else None
    )
    def decorator(view_func):
        old_wrapped = old_decorator(view_func) if old_decorator else None
        @_p10_wraps(view_func)
        def wrapper(request,*args,**kwargs):
            if not request.user.is_authenticated:
                _p10_messages.error(request,"❌ لطفاً ابتدا وارد شوید")
                return _p10_redirect("first:login")
            if _p10_is_owner(request.user):
                return view_func(request,*args,**kwargs)
            if old_wrapped:
                return old_wrapped(request,*args,**kwargs)
            if not check_admin_permission(request.user, permission_name):
                _p10_messages.error(request,"⛔ شما دسترسی لازم برای این بخش را ندارید")
                return _p10_redirect(redirect_url)
            return view_func(request,*args,**kwargs)
        return wrapper
    return decorator
