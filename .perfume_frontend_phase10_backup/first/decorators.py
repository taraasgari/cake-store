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
