from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.views.static import serve as django_static_serve


def health(request):
    """
    مسیر سبک برای بررسی سلامت سایت توسط
    Docker، Nginx، Traefik و سیستم مانیتورینگ.
    """
    return JsonResponse({
        'status': 'ok',
        'service': 'perfume-shop',
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


# فایل‌های آپلودی عمومی برای استقرار ساده Docker. `static()` در Django فقط
# هنگام DEBUG الگو می‌سازد، بنابراین برای production یک route صریح داریم.
if getattr(settings, 'SERVE_MEDIA', False):
    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$',
            django_static_serve,
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': False},
        ),
    ]
elif settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# WhiteNoise فایل‌های static را در production سرو می‌کند.
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT,
    )
