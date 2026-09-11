import io
import re
from pathlib import Path

from reportlab.graphics.charts.barcharts import (
    HorizontalBarChart,
    VerticalBarChart,
)
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PINK = colors.HexColor('#EC407A')
DARK_PINK = colors.HexColor('#AD1457')
PURPLE = colors.HexColor('#7E57C2')
GREEN = colors.HexColor('#16A36A')
BLUE = colors.HexColor('#3B82F6')
AMBER = colors.HexColor('#F59E0B')
RED = colors.HexColor('#EF4444')

INK = colors.HexColor('#25232B')
MUTED = colors.HexColor('#77727C')
PALE = colors.HexColor('#FFF5FA')
GRID = colors.HexColor('#E8DFE5')


def _register_fonts():
    regular_candidates = [
        Path(
            '/usr/share/fonts/truetype/'
            'dejavu/DejaVuSans.ttf'
        ),
        Path('C:/Windows/Fonts/arial.ttf'),
    ]

    bold_candidates = [
        Path(
            '/usr/share/fonts/truetype/'
            'dejavu/DejaVuSans-Bold.ttf'
        ),
        Path('C:/Windows/Fonts/arialbd.ttf'),
    ]

    regular = next(
        (
            path
            for path in regular_candidates
            if path.exists()
        ),
        None,
    )

    bold = next(
        (
            path
            for path in bold_candidates
            if path.exists()
        ),
        regular,
    )

    if regular:
        pdfmetrics.registerFont(
            TTFont(
                'FaFont',
                str(regular),
            )
        )

        pdfmetrics.registerFont(
            TTFont(
                'FaFontBold',
                str(bold),
            )
        )

        return 'FaFont', 'FaFontBold'

    return 'Helvetica', 'Helvetica-Bold'


FONT, FONT_BOLD = _register_fonts()


# حالت جایگزین در صورت نصب نبودن
# arabic_reshaper و python-bidi
ARABIC_FORMS = {
    'ء': ('\ufe80', None, None, None),
    'آ': ('\ufe81', '\ufe82', None, None),
    'أ': ('\ufe83', '\ufe84', None, None),
    'ؤ': ('\ufe85', '\ufe86', None, None),
    'إ': ('\ufe87', '\ufe88', None, None),

    'ئ': (
        '\ufe89',
        '\ufe8a',
        '\ufe8b',
        '\ufe8c',
    ),

    'ا': ('\ufe8d', '\ufe8e', None, None),

    'ب': (
        '\ufe8f',
        '\ufe90',
        '\ufe91',
        '\ufe92',
    ),

    'ة': ('\ufe93', '\ufe94', None, None),

    'ت': (
        '\ufe95',
        '\ufe96',
        '\ufe97',
        '\ufe98',
    ),

    'ث': (
        '\ufe99',
        '\ufe9a',
        '\ufe9b',
        '\ufe9c',
    ),

    'ج': (
        '\ufe9d',
        '\ufe9e',
        '\ufe9f',
        '\ufea0',
    ),

    'ح': (
        '\ufea1',
        '\ufea2',
        '\ufea3',
        '\ufea4',
    ),

    'خ': (
        '\ufea5',
        '\ufea6',
        '\ufea7',
        '\ufea8',
    ),

    'د': ('\ufea9', '\ufeaa', None, None),
    'ذ': ('\ufeab', '\ufeac', None, None),
    'ر': ('\ufead', '\ufeae', None, None),
    'ز': ('\ufeaf', '\ufeb0', None, None),

    'س': (
        '\ufeb1',
        '\ufeb2',
        '\ufeb3',
        '\ufeb4',
    ),

    'ش': (
        '\ufeb5',
        '\ufeb6',
        '\ufeb7',
        '\ufeb8',
    ),

    'ص': (
        '\ufeb9',
        '\ufeba',
        '\ufebb',
        '\ufebc',
    ),

    'ض': (
        '\ufebd',
        '\ufebe',
        '\ufebf',
        '\ufec0',
    ),

    'ط': (
        '\ufec1',
        '\ufec2',
        '\ufec3',
        '\ufec4',
    ),

    'ظ': (
        '\ufec5',
        '\ufec6',
        '\ufec7',
        '\ufec8',
    ),

    'ع': (
        '\ufec9',
        '\ufeca',
        '\ufecb',
        '\ufecc',
    ),

    'غ': (
        '\ufecd',
        '\ufece',
        '\ufecf',
        '\ufed0',
    ),

    'ف': (
        '\ufed1',
        '\ufed2',
        '\ufed3',
        '\ufed4',
    ),

    'ق': (
        '\ufed5',
        '\ufed6',
        '\ufed7',
        '\ufed8',
    ),

    'ك': (
        '\ufed9',
        '\ufeda',
        '\ufedb',
        '\ufedc',
    ),

    'ل': (
        '\ufedd',
        '\ufede',
        '\ufedf',
        '\ufee0',
    ),

    'م': (
        '\ufee1',
        '\ufee2',
        '\ufee3',
        '\ufee4',
    ),

    'ن': (
        '\ufee5',
        '\ufee6',
        '\ufee7',
        '\ufee8',
    ),

    'ه': (
        '\ufee9',
        '\ufeea',
        '\ufeeb',
        '\ufeec',
    ),

    'و': ('\ufeed', '\ufeee', None, None),
    'ى': ('\ufeef', '\ufef0', None, None),

    'ي': (
        '\ufef1',
        '\ufef2',
        '\ufef3',
        '\ufef4',
    ),

    'پ': (
        '\ufb56',
        '\ufb57',
        '\ufb58',
        '\ufb59',
    ),

    'چ': (
        '\ufb7a',
        '\ufb7b',
        '\ufb7c',
        '\ufb7d',
    ),

    'ژ': ('\ufb8a', '\ufb8b', None, None),

    'ک': (
        '\ufb8e',
        '\ufb8f',
        '\ufb90',
        '\ufb91',
    ),

    'گ': (
        '\ufb92',
        '\ufb93',
        '\ufb94',
        '\ufb95',
    ),

    'ی': (
        '\ufbfc',
        '\ufbfd',
        '\ufbfe',
        '\ufbff',
    ),
}


def _fallback_rtl(value):
    value = str(value or '')
    characters = list(value)
    shaped = []

    for index, character in enumerate(characters):
        forms = ARABIC_FORMS.get(character)

        if not forms:
            shaped.append(character)
            continue

        previous = (
            ARABIC_FORMS.get(
                characters[index - 1]
            )
            if index
            else None
        )

        following = (
            ARABIC_FORMS.get(
                characters[index + 1]
            )
            if index + 1 < len(characters)
            else None
        )

        joins_previous = bool(
            previous
            and previous[2]
            and forms[1]
        )

        joins_next = bool(
            following
            and forms[2]
            and following[1]
        )

        if (
            joins_previous
            and joins_next
            and forms[3]
        ):
            shaped.append(forms[3])

        elif joins_previous and forms[1]:
            shaped.append(forms[1])

        elif joins_next and forms[2]:
            shaped.append(forms[2])

        else:
            shaped.append(forms[0])

    visual = ''.join(reversed(shaped))

    token_pattern = re.compile(
        r'[A-Za-z0-9۰-۹٠-٩]'
        r'[A-Za-z0-9۰-۹٠-٩,.:/%+_\-#]*'
    )

    return token_pattern.sub(
        lambda match: match.group(0)[::-1],
        visual,
    )


try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    def rtl(value):
        return get_display(
            arabic_reshaper.reshape(
                str(value or '')
            )
        )

except ImportError:
    rtl = _fallback_rtl


def money(value):
    return f'{int(float(value or 0)):,}'


def build_pdf(data):
    buffer = io.BytesIO()
    page_size = landscape(A4)

    document = SimpleDocTemplate(
        buffer,
        pagesize=page_size,

        rightMargin=13 * mm,
        leftMargin=13 * mm,
        topMargin=20 * mm,
        bottomMargin=15 * mm,

        title='گزارش جامع مدیریتی فروشگاه',
        author='آرایشی شاپ',
    )

    default_styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'FaTitle',
        parent=default_styles['Title'],
        fontName=FONT_BOLD,
        fontSize=21,
        leading=31,
        textColor=DARK_PINK,
        alignment=TA_CENTER,
    )

    section_style = ParagraphStyle(
        'FaSection',
        parent=default_styles['Heading2'],
        fontName=FONT_BOLD,
        fontSize=14,
        leading=22,
        textColor=INK,
        alignment=TA_RIGHT,
        spaceBefore=5,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        'FaBody',
        parent=default_styles['BodyText'],
        fontName=FONT,
        fontSize=8.5,
        leading=14,
        textColor=INK,
        alignment=TA_RIGHT,
    )

    small_style = ParagraphStyle(
        'FaSmall',
        parent=body_style,
        fontSize=7.3,
        leading=11,
    )

    white_style = ParagraphStyle(
        'FaWhite',
        parent=body_style,
        fontName=FONT_BOLD,
        textColor=colors.white,
        alignment=TA_CENTER,
    )

    kpi_style = ParagraphStyle(
        'Kpi',
        parent=body_style,
        fontName=FONT_BOLD,
        fontSize=13,
        textColor=DARK_PINK,
        alignment=TA_CENTER,
    )

    note_style = ParagraphStyle(
        'KpiNote',
        parent=small_style,
        alignment=TA_CENTER,
        textColor=MUTED,
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=body_style,
        alignment=TA_CENTER,
        textColor=MUTED,
    )

    def paragraph(value, style=body_style):
        return Paragraph(
            rtl(value),
            style,
        )

    def section(value):
        return Paragraph(
            rtl(value),
            section_style,
        )

    def report_table(
        rows,
        widths=None,
        header=True,
        font_size=7.5,
    ):
        prepared = []

        for row_index, row in enumerate(rows):
            prepared.append([
                paragraph(
                    cell,
                    (
                        white_style
                        if header and row_index == 0
                        else small_style
                    ),
                )
                for cell in row
            ])

        result = Table(
            prepared,
            colWidths=widths,
            repeatRows=1 if header else 0,
            hAlign='RIGHT',
        )

        commands = [
            (
                'FONTNAME',
                (0, 0),
                (-1, -1),
                FONT,
            ),
            (
                'FONTSIZE',
                (0, 0),
                (-1, -1),
                font_size,
            ),
            (
                'ALIGN',
                (0, 0),
                (-1, -1),
                'RIGHT',
            ),
            (
                'VALIGN',
                (0, 0),
                (-1, -1),
                'MIDDLE',
            ),
            (
                'GRID',
                (0, 0),
                (-1, -1),
                .35,
                GRID,
            ),
            (
                'TOPPADDING',
                (0, 0),
                (-1, -1),
                5,
            ),
            (
                'BOTTOMPADDING',
                (0, 0),
                (-1, -1),
                5,
            ),
            (
                'ROWBACKGROUNDS',
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor('#FCF7FA'),
                ],
            ),
        ]

        if header:
            commands += [
                (
                    'BACKGROUND',
                    (0, 0),
                    (-1, 0),
                    DARK_PINK,
                ),
                (
                    'TEXTCOLOR',
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
            ]

        result.setStyle(
            TableStyle(commands)
        )

        return result

    def bar_chart(
        labels,
        values,
        color=PINK,
        horizontal=False,
        title='',
    ):
        drawing = Drawing(350, 205)

        chart = (
            HorizontalBarChart()
            if horizontal
            else VerticalBarChart()
        )

        chart.x = 40
        chart.y = 30
        chart.width = 285
        chart.height = 135

        chart.data = [
            values or [0]
        ]

        chart.categoryAxis.categoryNames = (
            [
                rtl(str(label)[:22])
                for label in labels
            ]
            or ['-']
        )

        chart.valueAxis.valueMin = 0

        chart.valueAxis.valueMax = (
            max(values or [1]) * 1.18
            or 1
        )

        chart.valueAxis.valueStep = max(
            1,
            chart.valueAxis.valueMax / 5,
        )

        chart.bars[0].fillColor = color
        chart.bars[0].strokeColor = color

        chart.categoryAxis.labels.fontName = FONT
        chart.categoryAxis.labels.fontSize = 6

        chart.valueAxis.labels.fontName = FONT
        chart.valueAxis.labels.fontSize = 6

        if not horizontal:
            chart.categoryAxis.labels.angle = 35
            chart.categoryAxis.labels.dy = -5

        drawing.add(chart)

        drawing.add(
            String(
                175,
                190,
                rtl(title),
                fontName=FONT_BOLD,
                fontSize=10,
                fillColor=INK,
                textAnchor='middle',
            )
        )

        return drawing

    def pie_chart(
        labels,
        values,
        title='',
    ):
        drawing = Drawing(350, 205)

        pie = Pie()

        pie.x = 95
        pie.y = 30
        pie.width = 145
        pie.height = 145

        pie.data = values or [1]

        if values:
            pie.labels = [
                rtl(f'{label} ({value})')
                for label, value
                in zip(labels, values)
            ]
        else:
            pie.labels = [
                rtl('بدون داده')
            ]

        pie.slices.fontName = FONT
        pie.slices.fontSize = 6.5

        palette = [
            PINK,
            BLUE,
            GREEN,
            AMBER,
            PURPLE,
            RED,
            colors.HexColor('#14B8A6'),
        ]

        for index in range(len(pie.data)):
            pie.slices[index].fillColor = (
                palette[
                    index % len(palette)
                ]
            )

            pie.slices[index].strokeColor = (
                colors.white
            )

        drawing.add(pie)

        drawing.add(
            String(
                175,
                190,
                rtl(title),
                fontName=FONT_BOLD,
                fontSize=10,
                fillColor=INK,
                textAnchor='middle',
            )
        )

        return drawing

    def page_decor(canvas, current_document):
        width, height = page_size

        canvas.saveState()

        canvas.setFillColor(DARK_PINK)

        canvas.rect(
            0,
            height - 12 * mm,
            width,
            12 * mm,
            fill=1,
            stroke=0,
        )

        canvas.setFillColor(colors.white)
        canvas.setFont(FONT_BOLD, 9)

        canvas.drawRightString(
            width - 13 * mm,
            height - 7.5 * mm,
            rtl(
                'گزارش جامع مدیریتی '
                'آرایشی شاپ'
            ),
        )

        canvas.setFillColor(MUTED)
        canvas.setFont(FONT, 7)

        canvas.drawRightString(
            width - 13 * mm,
            7 * mm,
            rtl(
                f'دوره گزارش: '
                f'{data["period_label"]}'
            ),
        )

        canvas.drawString(
            13 * mm,
            7 * mm,
            rtl(
                f'صفحه '
                f'{current_document.page}'
            ),
        )

        canvas.restoreState()

    story = [
        Spacer(1, 10 * mm),

        paragraph(
            'گزارش جامع مدیریتی فروشگاه',
            title_style,
        ),

        paragraph(
            f'دوره: {data["period_label"]}',
            subtitle_style,
        ),

        Spacer(1, 7 * mm),
    ]

    kpis = data['kpis']

    kpi_values = [
        (
            'درآمد نهایی',
            f'{money(kpis["revenue"])} تومان',
            (
                f'{kpis["revenue_change"]:+.1f}٪ '
                f'نسبت به دوره قبل'
            ),
        ),
        (
            'تعداد سفارش',
            f'{kpis["orders"]:,}',
            (
                f'{kpis["orders_change"]:+.1f}٪ '
                f'نسبت به دوره قبل'
            ),
        ),
        (
            'میانگین سفارش',
            (
                f'{money(kpis["average_order"])} '
                f'تومان'
            ),
            (
                f'{kpis["average_order_change"]:+.1f}٪ '
                f'تغییر'
            ),
        ),
        (
            'نرخ پرداخت موفق',
            (
                f'{kpis["payment_success_rate"]:.1f}٪'
            ),
            (
                f'{kpis["paid_orders"]} '
                f'سفارش پرداخت‌شده'
            ),
        ),
        (
            'تعداد کالای فروخته‌شده',
            f'{kpis["sold_items"]:,}',
            (
                f'{kpis["unique_buyers"]} '
                f'خریدار یکتا'
            ),
        ),
        (
            'مشتری جدید',
            f'{kpis["new_customers"]:,}',
            (
                f'{kpis["new_customers_change"]:+.1f}٪ '
                f'تغییر'
            ),
        ),
        (
            'مشتری بازگشتی',
            f'{kpis["returning_customers"]:,}',
            (
                f'نرخ بازگشت '
                f'{kpis["return_rate"]:.1f}٪'
            ),
        ),
        (
            'نرخ لغو سفارش',
            f'{kpis["cancel_rate"]:.1f}٪',
            'نسبت به همه سفارش‌های دوره',
        ),
    ]

    kpi_cells = []

    for title, value, note in kpi_values:
        kpi_cells.append(
            Table(
                [
                    [
                        paragraph(
                            title,
                            small_style,
                        )
                    ],
                    [
                        paragraph(
                            value,
                            kpi_style,
                        )
                    ],
                    [
                        paragraph(
                            note,
                            note_style,
                        )
                    ],
                ],
                colWidths=[62 * mm],
                style=[
                    (
                        'BOX',
                        (0, 0),
                        (-1, -1),
                        .6,
                        GRID,
                    ),
                    (
                        'BACKGROUND',
                        (0, 0),
                        (-1, -1),
                        PALE,
                    ),
                    (
                        'ALIGN',
                        (0, 0),
                        (-1, -1),
                        'CENTER',
                    ),
                    (
                        'TOPPADDING',
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        'BOTTOMPADDING',
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ],
            )
        )

    story.append(
        Table(
            [
                kpi_cells[:4],
                kpi_cells[4:],
            ],
            colWidths=[64 * mm] * 4,
            hAlign='CENTER',
            style=[
                (
                    'VALIGN',
                    (0, 0),
                    (-1, -1),
                    'TOP',
                ),
                (
                    'LEFTPADDING',
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    'RIGHTPADDING',
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    'TOPPADDING',
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    'BOTTOMPADDING',
                    (0, 0),
                    (-1, -1),
                    3,
                ),
            ],
        )
    )

    story.extend([
        Spacer(1, 6 * mm),
        section('خلاصه مالی دقیق'),
    ])

    finance = data['finance']

    story.append(
        report_table(
            [
                [
                    'مبلغ نهایی پرداخت‌شده',
                    'هزینه ارسال',
                    'کل تخفیف',
                    'فروش ناخالص',
                    'میانگین روزانه',
                    'پیش‌بینی ۳۰ روزه',
                ],
                [
                    (
                        f'{money(finance["revenue"])} '
                        f'تومان'
                    ),
                    (
                        f'{money(finance["shipping"])} '
                        f'تومان'
                    ),
                    (
                        f'{money(finance["discounts"])} '
                        f'تومان'
                    ),
                    (
                        f'{money(finance["gross"])} '
                        f'تومان'
                    ),
                    (
                        f'{money(data["daily_average"])} '
                        f'تومان'
                    ),
                    (
                        f'{money(data["forecast_30_days"])} '
                        f'تومان'
                    ),
                ],
            ],
            widths=[43 * mm] * 6,
        )
    )

    story.extend([
        Spacer(1, 4 * mm),

        paragraph(
            (
                f'بیشترین درآمد در بازه نمودار '
                f'مربوط به {data["peak"]["label"]} '
                f'با مبلغ '
                f'{money(data["peak"]["revenue"])} '
                f'تومان بوده است.'
            )
        ),

        PageBreak(),
    ])

    timeline = data['chart_data']['timeline']

    story.append(
        section(
            'روند فروش و وضعیت سفارش‌ها'
        )
    )

    story.append(
        Table(
            [[
                bar_chart(
                    [
                        row['label']
                        for row in timeline
                    ],
                    [
                        row['revenue']
                        for row in timeline
                    ],
                    BLUE,
                    title='روند درآمد',
                ),

                pie_chart(
                    [
                        row['label']
                        for row
                        in data['order_status']
                    ],
                    [
                        row['count']
                        for row
                        in data['order_status']
                    ],
                    'ترکیب وضعیت سفارش‌ها',
                ),
            ]],
            colWidths=[
                132 * mm,
                132 * mm,
            ],
            style=[
                (
                    'VALIGN',
                    (0, 0),
                    (-1, -1),
                    'TOP',
                )
            ],
        )
    )

    story.extend([
        Spacer(1, 3 * mm),

        report_table(
            [
                [
                    'وضعیت',
                    'تعداد',
                    'سهم',
                ]
            ] + [
                [
                    row['label'],
                    f'{row["count"]:,}',
                    f'{row["percent"]:.1f}٪',
                ]
                for row in data['order_status']
            ],
            widths=[
                60 * mm,
                35 * mm,
                35 * mm,
            ],
        ),

        Spacer(1, 5 * mm),
    ])

    payment_section = [
        section('روش‌های پرداخت'),

        Table(
            [[
                pie_chart(
                    [
                        row['label']
                        for row
                        in data['payment_methods']
                    ],
                    [
                        row['count']
                        for row
                        in data['payment_methods']
                    ],
                    'سهم روش‌های پرداخت',
                ),

                report_table(
                    [
                        [
                            'روش',
                            'تعداد',
                            'درآمد',
                            'سهم',
                        ]
                    ] + [
                        [
                            row['label'],
                            row['count'],
                            (
                                f'{money(row["revenue"])} '
                                f'تومان'
                            ),
                            (
                                f'{row["percent"]:.1f}٪'
                            ),
                        ]
                        for row
                        in data['payment_methods']
                    ],
                    widths=[
                        42 * mm,
                        25 * mm,
                        48 * mm,
                        25 * mm,
                    ],
                ),
            ]],
            colWidths=[
                120 * mm,
                144 * mm,
            ],
            style=[
                (
                    'VALIGN',
                    (0, 0),
                    (-1, -1),
                    'TOP',
                )
            ],
        ),
    ]

    story.append(
        KeepTogether(payment_section)
    )

    story.append(PageBreak())

    # ============================================
    # صفحه محصولات
    # ============================================

    top_products = data['top_products']

    story.append(
        section(
            'تحلیل محصولات و دسته‌بندی‌ها'
        )
    )

    story.append(
        Table(
            [[
                bar_chart(
                    [
                        row['name']
                        for row
                        in top_products[:8]
                    ],
                    [
                        row['quantity']
                        for row
                        in top_products[:8]
                    ],
                    PINK,
                    horizontal=True,
                    title='پرفروش‌ترین محصولات',
                ),

                pie_chart(
                    [
                        row['name']
                        for row
                        in data['category_sales'][:7]
                    ],
                    [
                        row['revenue']
                        for row
                        in data['category_sales'][:7]
                    ],
                    'سهم درآمد دسته‌بندی‌ها',
                ),
            ]],
            colWidths=[
                132 * mm,
                132 * mm,
            ],
            style=[
                (
                    'VALIGN',
                    (0, 0),
                    (-1, -1),
                    'TOP',
                )
            ],
        )
    )

    story.extend([
        Spacer(1, 3 * mm),
        section(
            'جدول پرفروش‌ترین محصولات'
        ),
    ])

    product_rows = [[
        'رتبه',
        'محصول',
        'تعداد',
        'تعداد سفارش',
        'درآمد',
        'تغییر نسبت به دوره قبل',
    ]]

    for index, row in enumerate(
        top_products[:15],
        1,
    ):
        product_rows.append([
            index,
            row['name'],
            row['quantity'],
            row['orders'],
            (
                f'{money(row["revenue"])} '
                f'تومان'
            ),
            f'{row["change"]:+.1f}٪',
        ])

    story.append(
        report_table(
            product_rows,
            widths=[
                15 * mm,
                90 * mm,
                25 * mm,
                30 * mm,
                50 * mm,
                48 * mm,
            ],
        )
    )

    story.extend([
        Spacer(1, 5 * mm),
        section('عملکرد دسته‌بندی‌ها'),
    ])

    story.append(
        report_table(
            [
                [
                    'دسته‌بندی',
                    'تعداد فروش',
                    'سفارش',
                    'درآمد',
                    'سهم درآمد',
                ]
            ] + [
                [
                    row['name'],
                    row['quantity'],
                    row['orders'],
                    (
                        f'{money(row["revenue"])} '
                        f'تومان'
                    ),
                    f'{row["share"]:.1f}٪',
                ]
                for row
                in data['category_sales']
            ],
            widths=[
                75 * mm,
                35 * mm,
                30 * mm,
                60 * mm,
                40 * mm,
            ],
        )
    )

    story.append(PageBreak())

    # ============================================
    # صفحه مشتریان
    # ============================================

    story.append(
        section('تحلیل مشتریان')
    )

    story.append(
        report_table(
            [
                [
                    'کل مشتریان',
                    'خریداران این دوره',
                    'مشتریان بازگشتی',
                    'بدون خرید',
                    'نرخ کاربران خریدار',
                ],
                [
                    data['total_customers'],
                    data['buying_customers'],
                    data['returning_customers'],
                    data['no_purchase_customers'],
                    (
                        f'{kpis["customer_purchase_rate"]:.1f}٪'
                    ),
                ],
            ],
            widths=[50 * mm] * 5,
        )
    )

    story.extend([
        Spacer(1, 5 * mm),
        section('مشتریان برتر دوره'),
    ])

    customer_rows = [[
        'رتبه',
        'نام کاربری',
        'تلفن',
        'تعداد سفارش',
        'جمع خرید',
        'میانگین سفارش',
    ]]

    for index, row in enumerate(
        data['top_customers'],
        1,
    ):
        customer_rows.append([
            index,
            row['username'],
            row['phone'] or '-',
            row['orders'],
            (
                f'{money(row["spent"])} '
                f'تومان'
            ),
            (
                f'{money(row["average"])} '
                f'تومان'
            ),
        ])

    story.append(
        report_table(
            customer_rows,
            widths=[
                15 * mm,
                55 * mm,
                45 * mm,
                35 * mm,
                55 * mm,
                55 * mm,
            ],
        )
    )

    story.extend([
        Spacer(1, 5 * mm),
        section('کوپن‌ها و تخفیف‌ها'),
    ])

    if data['coupons']:
        story.append(
            report_table(
                [
                    [
                        'کد',
                        'دفعات استفاده',
                        'درآمد سفارش‌ها',
                        'تخفیف کوپن',
                    ]
                ] + [
                    [
                        row['code'],
                        row['uses'],
                        (
                            f'{money(row["revenue"])} '
                            f'تومان'
                        ),
                        (
                            f'{money(row["discount"])} '
                            f'تومان'
                        ),
                    ]
                    for row in data['coupons']
                ],
                widths=[
                    55 * mm,
                    45 * mm,
                    70 * mm,
                    70 * mm,
                ],
            )
        )
    else:
        story.append(
            paragraph(
                'در این دوره سفارشی با '
                'کوپن ثبت نشده است.'
            )
        )

    story.append(PageBreak())

    # ============================================
    # صفحه موجودی و نظرات
    # ============================================

    story.append(
        section(
            'انبار، موجودی و کیفیت تجربه مشتری'
        )
    )

    story.append(
        report_table(
            [
                [
                    'محصول فعال',
                    'واحد موجودی',
                    'ارزش فروش موجودی',
                    'ناموجود',
                    'موجودی کم',
                    'سبد رهاشده',
                ],
                [
                    data['active_products'],
                    data['inventory_units'],
                    (
                        f'{money(data["inventory_value"])} '
                        f'تومان'
                    ),
                    data['out_of_stock'],
                    data['low_stock'],
                    data['abandoned_carts'],
                ],
            ],
            widths=[42 * mm] * 6,
        )
    )

    story.append(Spacer(1, 5 * mm))

    review_table = Table(
        [
            [
                paragraph(
                    'شاخص نظرات',
                    white_style,
                ),
                paragraph(
                    'مقدار',
                    white_style,
                ),
            ],
            [
                paragraph(
                    'نظر ثبت‌شده',
                    small_style,
                ),
                paragraph(
                    data['review_total'],
                    small_style,
                ),
            ],
            [
                paragraph(
                    'نظر تأییدشده',
                    small_style,
                ),
                paragraph(
                    data['verified_review_count'],
                    small_style,
                ),
            ],
            [
                paragraph(
                    'میانگین امتیاز',
                    small_style,
                ),
                paragraph(
                    (
                        f'{data["review_average"]} '
                        f'از ۵'
                    ),
                    small_style,
                ),
            ],
            [
                paragraph(
                    'علاقه‌مندی جدید',
                    small_style,
                ),
                paragraph(
                    data['wishlist_count'],
                    small_style,
                ),
            ],
        ],
        colWidths=[
            60 * mm,
            45 * mm,
        ],
        style=[
            (
                'BACKGROUND',
                (0, 0),
                (-1, 0),
                DARK_PINK,
            ),
            (
                'GRID',
                (0, 0),
                (-1, -1),
                .4,
                GRID,
            ),
            (
                'VALIGN',
                (0, 0),
                (-1, -1),
                'MIDDLE',
            ),
            (
                'TOPPADDING',
                (0, 0),
                (-1, -1),
                7,
            ),
            (
                'BOTTOMPADDING',
                (0, 0),
                (-1, -1),
                7,
            ),
        ],
    )

    story.append(
        Table(
            [[
                bar_chart(
                    [
                        (
                            f'{row["rating"]} '
                            f'ستاره'
                        )
                        for row
                        in data['rating_distribution']
                    ],
                    [
                        row['count']
                        for row
                        in data['rating_distribution']
                    ],
                    AMBER,
                    title='توزیع امتیازها',
                ),

                review_table,
            ]],
            colWidths=[
                145 * mm,
                110 * mm,
            ],
            style=[
                (
                    'VALIGN',
                    (0, 0),
                    (-1, -1),
                    'TOP',
                )
            ],
        )
    )

    story.append(
        section(
            'محصولات نیازمند توجه انبار'
        )
    )

    status_names = {
        'out': 'ناموجود',
        'low': 'موجودی کم',
        'stagnant': 'بدون فروش در دوره',
    }

    story.append(
        report_table(
            [
                [
                    'محصول',
                    'موجودی',
                    'ارزش فروش موجودی',
                    'وضعیت',
                ]
            ] + [
                [
                    row['name'],
                    row['stock'],
                    (
                        f'{money(row["value"])} '
                        f'تومان'
                    ),
                    status_names[row['status']],
                ]
                for row
                in data['inventory_rows']
            ],
            widths=[
                100 * mm,
                30 * mm,
                65 * mm,
                55 * mm,
            ],
        )
    )

    story.append(PageBreak())

    # ============================================
    # صفحه نهایی
    # ============================================

    story.append(
        section(
            'ریز آخرین سفارش‌های دوره'
        )
    )

    recent_order_rows = [[
        'شماره',
        'مشتری',
        'مبلغ',
        'وضعیت',
        'پرداخت',
        'تاریخ',
    ]]

    for row in data['recent_orders']:
        recent_order_rows.append([
            row['number'],
            row['username'],

            (
                f'{money(row["total"])} '
                f'تومان'
            ),

            row['status'],

            (
                'پرداخت‌شده'
                if row['is_paid']
                else 'پرداخت‌نشده'
            ),

            row['date'],
        ])

    story.append(
        report_table(
            recent_order_rows,
            widths=[
                35 * mm,
                50 * mm,
                55 * mm,
                45 * mm,
                40 * mm,
                45 * mm,
            ],
        )
    )

    story.extend([
        Spacer(1, 7 * mm),
        section(
            'هشدارها و جمع‌بندی مدیریتی'
        ),
    ])

    if data['alerts']:
        alert_rows = [[
            'سطح',
            'عنوان',
            'شرح',
        ]]

        alert_labels = {
            'danger': 'بحرانی',
            'warning': 'هشدار',
            'info': 'اطلاع',
        }

        for alert in data['alerts']:
            alert_rows.append([
                alert_labels.get(
                    alert['level'],
                    alert['level'],
                ),
                alert['title'],
                alert['message'],
            ])

        story.append(
            report_table(
                alert_rows,
                widths=[
                    30 * mm,
                    55 * mm,
                    155 * mm,
                ],
            )
        )

    else:
        story.append(
            paragraph(
                'هیچ هشدار مهمی برای این '
                'دوره شناسایی نشد.'
            )
        )

    story.extend([
        Spacer(1, 8 * mm),

        section('توضیح محاسبات'),

        paragraph(
            'درآمد فقط از سفارش‌های دارای وضعیت '
            'پرداخت‌شده محاسبه شده است. فروش ناخالص '
            'از subtotal، تخفیف از مجموع discount و '
            'coupon_discount، و مبلغ نهایی از total '
            'سفارش گرفته می‌شود. سود واقعی در این '
            'گزارش نمایش داده نشده، چون قیمت تمام‌شده '
            'کالا هنگام فروش در OrderItem ذخیره نمی‌شود. '
            'پیش‌بینی ۳۰ روزه بر اساس میانگین روزانه '
            'همین بازه است و تضمین فروش آینده نیست.'
        ),

        Spacer(1, 5 * mm),

        paragraph(
            (
                f'زمان تولید گزارش: '
                f'{data["generated_at"].strftime("%Y/%m/%d %H:%M")}'
            )
        ),
    ])

    document.build(
        story,
        onFirstPage=page_decor,
        onLaterPages=page_decor,
    )

    buffer.seek(0)
    return buffer