from io import BytesIO
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

GOLD = colors.HexColor('#C9954D')
DARK = colors.HexColor('#17110D')
CREAM = colors.HexColor('#F6EADC')
MUTED = colors.HexColor('#75685D')
LINE = colors.HexColor('#D8C8B7')
SOFT = colors.HexColor('#FAF6F1')
RED = colors.HexColor('#B94A48')
GREEN = colors.HexColor('#247A52')


def _rtl(value):
    text = '' if value is None else str(value)
    if not text:
        return ''
    return get_display(arabic_reshaper.reshape(text))


def _money(value):
    try:
        return f'{int(value):,}'
    except (TypeError, ValueError):
        return '0'


def _register_font():
    regular_candidates = [
        Path('C:/Windows/Fonts/tahoma.ttf'),
        Path('C:/Windows/Fonts/arial.ttf'),
        Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
    ]
    bold_candidates = [
        Path('C:/Windows/Fonts/tahomabd.ttf'),
        Path('C:/Windows/Fonts/arialbd.ttf'),
        Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
    ]

    regular = next((p for p in regular_candidates if p.exists()), None)
    bold = next((p for p in bold_candidates if p.exists()), regular)

    if not regular:
        return 'Helvetica', 'Helvetica-Bold'

    if 'OrderFa' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('OrderFa', str(regular)))
    if 'OrderFaBold' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('OrderFaBold', str(bold)))
    return 'OrderFa', 'OrderFaBold'


def build_orders_pdf(orders, *, filters=None, selected=False):
    orders = list(orders)
    font, bold_font = _register_font()
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title='Orders report',
        author='Perfume Shop',
    )

    title_style = ParagraphStyle(
        'order-title',
        fontName=bold_font,
        fontSize=16,
        leading=24,
        textColor=DARK,
        alignment=TA_RIGHT,
        spaceAfter=5 * mm,
    )
    body_style = ParagraphStyle(
        'order-body',
        fontName=font,
        fontSize=9,
        leading=15,
        textColor=DARK,
        alignment=TA_RIGHT,
    )
    small_style = ParagraphStyle(
        'order-small',
        fontName=font,
        fontSize=7.6,
        leading=12,
        textColor=MUTED,
        alignment=TA_RIGHT,
    )
    strong_style = ParagraphStyle(
        'order-strong',
        fontName=bold_font,
        fontSize=9,
        leading=15,
        textColor=DARK,
        alignment=TA_RIGHT,
    )

    story = [
        Paragraph(_rtl('گزارش سفارش‌ها و مشتریان'), title_style),
        Paragraph(
            _rtl(
                f"تعداد سفارش‌ها: {len(orders)} | "
                f"زمان تهیه: {timezone.localtime():%Y/%m/%d %H:%M}"
                + (' | فقط سفارش‌های انتخاب‌شده' if selected else '')
            ),
            small_style,
        ),
        Spacer(1, 5 * mm),
    ]

    if filters:
        filter_labels = []
        if filters.get('q'):
            filter_labels.append(f"جستجو: {filters['q']}")
        if filters.get('status'):
            filter_labels.append(f"وضعیت: {filters['status']}")
        if filters.get('payment'):
            filter_labels.append(
                'پرداخت: پرداخت‌شده'
                if filters['payment'] == 'paid'
                else 'پرداخت: پرداخت‌نشده'
            )
        sort_labels = {
            'newest': 'جدیدترین',
            'oldest': 'قدیمی‌ترین',
            'amount_desc': 'مبلغ بیشتر',
            'amount_asc': 'مبلغ کمتر',
            'paid_first': 'پرداخت‌شده‌ها اول',
            'unpaid_first': 'پرداخت‌نشده‌ها اول',
        }
        filter_labels.append(
            f"ترتیب: {sort_labels.get(filters.get('sort'), 'جدیدترین')}"
        )
        story.extend([
            Paragraph(_rtl(' | '.join(filter_labels)), small_style),
            Spacer(1, 4 * mm),
        ])

    if not orders:
        story.append(Paragraph(_rtl('سفارشی برای این فیلتر پیدا نشد.'), body_style))
    else:
        summary_rows = [[
            Paragraph(_rtl('شماره'), strong_style),
            Paragraph(_rtl('مشتری'), strong_style),
            Paragraph(_rtl('وضعیت'), strong_style),
            Paragraph(_rtl('پرداخت'), strong_style),
            Paragraph(_rtl('مبلغ'), strong_style),
            Paragraph(_rtl('تاریخ'), strong_style),
        ]]
        for order in orders:
            summary_rows.append([
                f'#{order.order_number}',
                Paragraph(_rtl(order.user.username), small_style),
                Paragraph(_rtl(order.get_status_display()), small_style),
                Paragraph(_rtl('پرداخت شده' if order.is_paid else 'پرداخت نشده'), small_style),
                _money(order.total),
                timezone.localtime(order.created_at).strftime('%Y/%m/%d'),
            ])

        summary = Table(
            summary_rows,
            colWidths=[28 * mm, 31 * mm, 29 * mm, 29 * mm, 29 * mm, 29 * mm],
            repeatRows=1,
        )
        summary.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), DARK),
            ('TEXTCOLOR', (0, 0), (-1, 0), CREAM),
            ('FONTNAME', (0, 0), (-1, -1), font),
            ('FONTSIZE', (0, 0), (-1, -1), 7.4),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, SOFT]),
            ('GRID', (0, 0), (-1, -1), 0.4, LINE),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.extend([summary, Spacer(1, 7 * mm)])

        for order in orders:
            user_name = order.user.get_full_name() or order.user.username
            customer_text = (
                f"مشتری: {user_name} | ایمیل: {order.user.email or '-'} | "
                f"تلفن: {order.phone} | کد پستی: {order.postal_code}"
            )
            header = Table([
                [
                    Paragraph(_rtl(f'سفارش #{order.order_number}'), strong_style),
                    Paragraph(_rtl(order.get_status_display()), strong_style),
                    Paragraph(_rtl(_money(order.total) + ' تومان'), strong_style),
                ]
            ], colWidths=[65 * mm, 52 * mm, 58 * mm])
            header.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0E3D2')),
                ('BOX', (0, 0), (-1, -1), 0.7, GOLD),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('TOPPADDING', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ]))

            detail_story = [
                header,
                Spacer(1, 2.5 * mm),
                Paragraph(_rtl(customer_text), small_style),
                Paragraph(_rtl(f'آدرس: {order.address}'), small_style),
                Spacer(1, 2 * mm),
            ]

            item_rows = [[
                Paragraph(_rtl('کالا'), strong_style),
                Paragraph(_rtl('تعداد'), strong_style),
                Paragraph(_rtl('قیمت'), strong_style),
                Paragraph(_rtl('جمع'), strong_style),
            ]]
            for item in order.items.all():
                item_rows.append([
                    Paragraph(_rtl(item.product_name), small_style),
                    str(item.quantity),
                    _money(item.price),
                    _money(item.total),
                ])
            items_table = Table(
                item_rows,
                colWidths=[85 * mm, 23 * mm, 34 * mm, 34 * mm],
                repeatRows=1,
            )
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), SOFT),
                ('GRID', (0, 0), (-1, -1), 0.35, LINE),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('FONTNAME', (0, 0), (-1, -1), font),
                ('FONTSIZE', (0, 0), (-1, -1), 7.4),
            ]))
            detail_story.extend([
                items_table,
                Spacer(1, 2.5 * mm),
                Paragraph(
                    _rtl(
                        f"روش پرداخت: {order.get_payment_method_display()} | "
                        f"وضعیت پرداخت: {'پرداخت شده' if order.is_paid else 'پرداخت نشده'} | "
                        f"تخفیف: {_money(order.discount)} تومان | "
                        f"هزینه ارسال: {_money(order.shipping_cost)} تومان"
                    ),
                    small_style,
                ),
                Spacer(1, 6 * mm),
            ])
            story.append(KeepTogether(detail_story))

    doc.build(story)
    return buffer.getvalue()
