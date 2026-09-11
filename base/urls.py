from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(request):
    """
    مسیر سبک برای بررسی سلامت سایت توسط
    Docker، Nginx، Traefik و سیستم مانیتورینگ.
    """
    return JsonResponse({
        'status': 'ok',
        'service': 'arayeshi',
    })


urlpatterns = [
    path(
        'health/',
        health,
        name='health',
    ),

    path(
        'admin/',
        admin.site.urls,
    ),

    path(
        '',
        include('first.urls'),
    ),

    path(
        '',
        include('customer_care.urls'),
    ),
]


# فقط در حالت توسعه، Django فایل‌های آپلودی را ارائه می‌کند.
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )

    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT,
    )