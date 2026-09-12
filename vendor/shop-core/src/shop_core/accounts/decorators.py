"""Reusable access-control decorators."""
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect

def admin_required(view_func):
    """Allow any authenticated admin or owner."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(
                request,
                "❌ لطفاً ابتدا وارد شوید",
            )
            return redirect('first:login')

        if not request.user.is_admin:
            messages.error(
                request,
                "⛔ شما دسترسی ادمین ندارید",
            )
            return redirect('first:home')

        return view_func(
            request,
            *args,
            **kwargs,
        )

    return wrapper

def owner_required(view_func):
    """Allow only the authenticated shop owner."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(
                request,
                "❌ لطفاً ابتدا وارد شوید",
            )
            return redirect('first:login')

        if not request.user.is_owner:
            messages.error(
                request,
                (
                    "⛔ فقط مالک سایت به این بخش "
                    "دسترسی دارد"
                ),
            )
            return redirect('first:home')

        return view_func(
            request,
            *args,
            **kwargs,
        )

    return wrapper
