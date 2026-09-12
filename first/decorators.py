from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import AdminPermission, AdminUserPermission


def _is_owner(user):
    return bool(
        user
        and getattr(user, 'is_authenticated', False)
        and (
            getattr(user, 'is_superuser', False)
            or getattr(user, 'is_owner', False)
        )
    )


def _is_admin(user):
    return bool(
        user
        and getattr(user, 'is_authenticated', False)
        and (
            _is_owner(user)
            or getattr(user, 'is_admin', False)
        )
    )


def check_admin_permission(user, permission_name):
    """Return the effective permission for an admin."""
    if _is_owner(user):
        return True
    if not _is_admin(user):
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
        return bool(override.is_allowed)

    return user.admin_roles.filter(
        is_active=True,
        permissions__name=permission_name,
        permissions__is_active=True,
    ).exists()


def get_effective_admin_permissions(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return []

    if _is_owner(user):
        return list(
            AdminPermission.objects.filter(is_active=True)
            .values_list('name', flat=True)
        )

    if not _is_admin(user):
        return []

    permissions = set(
        AdminPermission.objects.filter(
            is_active=True,
            roles__in=user.admin_roles.filter(is_active=True),
        ).values_list('name', flat=True)
    )

    for name, allowed in AdminUserPermission.objects.filter(
        user=user,
        permission__is_active=True,
    ).values_list('permission__name', 'is_allowed'):
        if allowed:
            permissions.add(name)
        else:
            permissions.discard(name)

    return sorted(permissions)


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '❌ لطفاً ابتدا وارد شوید')
            return redirect('first:login')
        if not _is_admin(request.user):
            messages.error(request, '⛔ شما دسترسی ادمین ندارید')
            return redirect('first:home')
        return view_func(request, *args, **kwargs)

    return wrapper


def owner_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '❌ لطفاً ابتدا وارد شوید')
            return redirect('first:login')
        if not _is_owner(request.user):
            messages.error(request, '⛔ فقط مالک سایت به این بخش دسترسی دارد')
            return redirect('first:home')
        return view_func(request, *args, **kwargs)

    return wrapper


def permission_required(permission_name, redirect_url='first:home'):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, '❌ لطفاً ابتدا وارد شوید')
                return redirect('first:login')
            if _is_owner(request.user):
                return view_func(request, *args, **kwargs)
            if not _is_admin(request.user):
                messages.error(request, '⛔ شما دسترسی ادمین ندارید')
                return redirect('first:home')
            if not check_admin_permission(request.user, permission_name):
                messages.error(request, '⛔ شما دسترسی لازم برای این بخش را ندارید')
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
