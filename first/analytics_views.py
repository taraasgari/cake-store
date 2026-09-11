import csv

from django.http import FileResponse, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .analytics_pdf import build_pdf
from .analytics_service import build_analytics, resolve_period
from .decorators import owner_required


@owner_required
def analytics_dashboard(request):
    """
    نمایش صفحه اصلی آمار و گزارش‌ها
    """
    context = build_analytics(request)
    return render(request, 'dashboard/analytics.html', context)


@owner_required
def analytics_export_csv(request):
    """
    خروجی CSV از آمار فروشگاه
    """
    data = build_analytics(request)

    response = HttpResponse(
        content_type='text/csv; charset=utf-8'
    )

    filename = f'analytics_{timezone.localdate():%Y%m%d}.csv'

    response['Content-Disposition'] = (
        f'attachment; filename="{filename}"'
    )

    # برای نمایش صحیح فارسی در Excel
    response.write('\ufeff')

    writer = csv.writer(response)

    writer.writerow([
        'گزارش جامع آماری فروشگاه',
        data.get('period_label', '')
    ])

    writer.writerow([])

    # ==========================================================
    # شاخص‌های کلیدی
    # ==========================================================
    writer.writerow(['شاخص‌های کلیدی'])
    writer.writerow(['شاخص', 'مقدار'])

    kpi_labels = {
        'revenue': 'درآمد نهایی',
        'gross': 'فروش ناخالص',
        'discounts': 'کل تخفیف',
        'shipping': 'هزینه ارسال',
        'orders': 'تعداد سفارش',
        'paid_orders': 'سفارش پرداخت‌شده',
        'payment_success_rate': 'نرخ پرداخت موفق',
        'average_order': 'میانگین مبلغ سفارش',
        'sold_items': 'تعداد کالای فروخته‌شده',
        'unique_buyers': 'خریدار یکتا',
        'new_customers': 'مشتری جدید',
        'returning_customers': 'مشتری بازگشتی',
        'return_rate': 'نرخ بازگشت مشتری',
        'cancel_rate': 'نرخ لغو سفارش',
    }

    kpis = data.get('kpis', {})
    finance = data.get('finance', {})

    for key, label in kpi_labels.items():
        value = kpis.get(key, finance.get(key, 0))
        writer.writerow([label, value])

    writer.writerow([])

    # ==========================================================
    # روند فروش
    # ==========================================================
    writer.writerow(['روند زمانی فروش'])
    writer.writerow([
        'تاریخ',
        'درآمد',
        'تعداد سفارش'
    ])

    timeline = data.get('chart_data', {}).get('timeline', [])

    for row in timeline:
        writer.writerow([
            row.get('label', ''),
            row.get('revenue', 0),
            row.get('orders', 0),
        ])

    writer.writerow([])

    # ==========================================================
    # محصولات پرفروش
    # ==========================================================
    writer.writerow(['پرفروش‌ترین محصولات'])
    writer.writerow([
        'محصول',
        'تعداد فروش',
        'تعداد سفارش',
        'درآمد',
        'تغییر نسبت به دوره قبل'
    ])

    for row in data.get('top_products', []):
        writer.writerow([
            row.get('name', ''),
            row.get('quantity', 0),
            row.get('orders', 0),
            row.get('revenue', 0),
            row.get('change', 0),
        ])

    writer.writerow([])

    # ==========================================================
    # فروش دسته‌بندی‌ها
    # ==========================================================
    writer.writerow(['آمار دسته‌بندی‌ها'])
    writer.writerow([
        'دسته‌بندی',
        'تعداد فروش',
        'تعداد سفارش',
        'درآمد',
        'سهم درآمد'
    ])

    for row in data.get('category_sales', []):
        writer.writerow([
            row.get('name', ''),
            row.get('quantity', 0),
            row.get('orders', 0),
            row.get('revenue', 0),
            row.get('share', 0),
        ])

    writer.writerow([])

    # ==========================================================
    # مشتریان برتر
    # ==========================================================
    writer.writerow(['مشتریان برتر'])
    writer.writerow([
        'نام کاربری',
        'شماره تلفن',
        'تعداد سفارش',
        'جمع خرید',
        'میانگین سفارش'
    ])

    for row in data.get('top_customers', []):
        writer.writerow([
            row.get('username', ''),
            row.get('phone', ''),
            row.get('orders', 0),
            row.get('spent', 0),
            row.get('average', 0),
        ])

    writer.writerow([])

    # ==========================================================
    # وضعیت انبار
    # ==========================================================
    writer.writerow(['محصولات نیازمند توجه'])
    writer.writerow([
        'محصول',
        'موجودی',
        'ارزش فروش موجودی',
        'وضعیت'
    ])

    for row in data.get('inventory_rows', []):
        writer.writerow([
            row.get('name', ''),
            row.get('stock', 0),
            row.get('value', 0),
            row.get('status', ''),
        ])

    return response


@owner_required
def analytics_pdf_preview(request):
    fallback_url = reverse(
        'first:analytics_dashboard'
    )

    return_url = (
        request.GET.get('return_to')
        or request.META.get('HTTP_REFERER')
        or fallback_url
    )

    if not url_has_allowed_host_and_scheme(
        url=return_url,
        allowed_hosts={
            request.get_host()
        },
        require_https=request.is_secure(),
    ):
        return_url = fallback_url

    inline_query = request.GET.copy()
    inline_query.pop('download', None)
    inline_query.pop('return_to', None)
    inline_query['inline'] = '1'

    download_query = request.GET.copy()
    download_query.pop('inline', None)
    download_query.pop('return_to', None)
    download_query['download'] = '1'

    pdf_base_url = reverse('first:analytics_download_pdf')

    pdf_url = pdf_base_url
    download_url = pdf_base_url

    if inline_query:
        pdf_url = f'{pdf_base_url}?{inline_query.urlencode()}'

    if download_query:
        download_url = (
            f'{pdf_base_url}?{download_query.urlencode()}'
        )

    period_data = resolve_period(request)

    context = {
        'pdf_url': pdf_url,
        'download_url': download_url,
        'period_label': period_data.get('label', ''),
        'return_url': return_url,
    }

    return render(
        request,
        'dashboard/analytics_pdf_preview.html',
        context
    )


@owner_required
def analytics_download_pdf(request):
    """
    ساخت و نمایش یا دانلود گزارش PDF.

    بدون download=1:
        PDF داخل مرورگر نمایش داده می‌شود.

    با download=1:
        PDF دانلود می‌شود.
    """

    data = build_analytics(request)
    buffer = build_pdf(data)

    # مطمئن می‌شویم ابتدای فایل خوانده می‌شود
    if hasattr(buffer, 'seek'):
        buffer.seek(0)

    filename = (
        f'analytics_report_'
        f'{timezone.localdate():%Y%m%d}.pdf'
    )

    force_download = (
        request.GET.get('download') == '1'
    )

    response = FileResponse(
        buffer,
        content_type='application/pdf',
        as_attachment=force_download,
        filename=filename,
    )

    response['Cache-Control'] = (
        'private, no-store, no-cache, must-revalidate, max-age=0'
    )
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = "frame-ancestors 'self'"

    return response