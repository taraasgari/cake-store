#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations
import re, shutil, subprocess, sys, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / ".perfume_frontend_phase06_backup"

BASE = ROOT / "first/templates/perfume_base.html"
CSS = ROOT / "static/css/perfume-phase06.css"
JS = ROOT / "static/js/perfume-phase06.js"

BACKEND_GUARD = [
    "first/views.py",
    "first/models.py",
    "first/urls.py",
    "first/forms.py",
    "first/context_processors.py",
    "customer_care/views.py",
    "customer_care/models.py",
    "customer_care/urls.py",
]

def run(*args):
    print("\n> " + " ".join(map(str, args)))
    p = subprocess.run(list(args), cwd=ROOT, text=True)
    if p.returncode:
        raise RuntimeError("Command failed: " + " ".join(map(str, args)))

def backup(path: Path):
    if not path.exists():
        return
    dst = BACKUP / path.relative_to(ROOT)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)

def write(path: Path, content: str):
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    print("[WRITE]", path.relative_to(ROOT).as_posix())

def patch_base():
    if not BASE.exists():
        raise RuntimeError("first/templates/perfume_base.html was not found.")

    text = BASE.read_text(encoding="utf-8")
    original = text

    css_link = '<link rel="stylesheet" href="{% static \'css/perfume-phase06.css\' %}">'
    js_link = '<script src="{% static \'js/perfume-phase06.js\' %}"></script>'

    if "perfume-phase06.css" not in text:
        if "{% block extra_css %}" in text:
            text = text.replace(
                "{% block extra_css %}",
                css_link + "\n    {% block extra_css %}",
                1,
            )
        else:
            text = text.replace("</head>", "    " + css_link + "\n</head>", 1)

    if "perfume-phase06.js" not in text:
        if "</body>" not in text:
            raise RuntimeError("Could not find </body> in perfume_base.html.")
        text = text.replace("</body>", "    " + js_link + "\n</body>", 1)

    if text != original:
        backup(BASE)
        BASE.write_text(text, encoding="utf-8")
        print("[PATCH] first/templates/perfume_base.html")

def find_tracking_template() -> Path | None:
    roots = [ROOT / "customer_care/templates", ROOT / "first/templates"]
    scored = []

    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.html"):
            if path.name in {"base.html", "perfume_base.html"}:
                continue

            txt = path.read_text(encoding="utf-8", errors="ignore")
            low = txt.lower()
            low_path = path.as_posix().lower()
            score = 0

            if "tracking" in low_path or "order_tracking" in low_path or "track_order" in low_path:
                score += 12
            if "پیگیری سفارش" in txt:
                score += 10
            if re.search(r"<h[12][^>]*>[^<]*پیگیری", txt):
                score += 8
            if "<form" in low:
                score += 5
            if "phone" in low or "تلفن" in txt:
                score += 4
            if "order" in low or "سفارش" in txt:
                score += 4
            if "csrf_token" in txt:
                score += 2

            if score:
                scored.append((score, path))

    if not scored:
        return None

    scored.sort(key=lambda x: (-x[0], len(x[1].as_posix())))
    print("\nTracking candidates:")
    for score, path in scored[:8]:
        print(f"  {score:02d}  {path.relative_to(ROOT)}")

    return scored[0][1]

def patch_tracking_template(path: Path):
    text = path.read_text(encoding="utf-8")

    if "p6-tracking-page" in text:
        print("[SKIP] Tracking page already Phase 06.")
        return

    match = re.search(
        r"(?s)({%\s*block\s+content\s*%})(.*?)({%\s*endblock\s*%})",
        text,
    )
    if not match:
        raise RuntimeError(
            f"Could not find block content in {path.relative_to(ROOT)}"
        )

    original_inner = match.group(2).strip()

    wrapper = r'''
{% block content %}
<section class="p6-tracking-page">
  <div class="p6-tracking-shell">

    <aside class="p6-tracking-intro">
      <div class="p6-tracking-eyebrow">ORDER TRACKING</div>

      <div class="p6-tracking-heading">
        <span>پیگیری سریع و مطمئن</span>
        <h1>سفارشت<br><em>کجاست؟</em></h1>
        <p>
          کد سفارش و شماره تلفنی که هنگام ثبت سفارش وارد کرده‌اید را وارد کنید
          تا وضعیت فعلی سفارش نمایش داده شود.
        </p>
      </div>

      <div class="p6-tracking-steps">
        <article>
          <b>01</b>
          <div><strong>کد سفارش</strong><small>شماره سفارش ثبت‌شده</small></div>
        </article>
        <article>
          <b>02</b>
          <div><strong>شماره تلفن</strong><small>همان شماره هنگام خرید</small></div>
        </article>
        <article>
          <b>03</b>
          <div><strong>مشاهده وضعیت</strong><small>پردازش، آماده‌سازی یا ارسال</small></div>
        </article>
      </div>

      <div class="p6-tracking-art">
        <div class="p6-orbit orbit-a"></div>
        <div class="p6-orbit orbit-b"></div>
        <div class="p6-track-mark"><i class="fa-solid fa-box"></i></div>
      </div>
    </aside>

    <div class="p6-tracking-card">
      <div class="p6-tracking-card-head">
        <span>TRACK YOUR ORDER</span>
        <h2>اطلاعات سفارش</h2>
        <p>اطلاعات زیر را دقیقاً مطابق زمان ثبت سفارش وارد کنید.</p>
      </div>

      <div class="p6-track-original">
__ORIGINAL__
      </div>
    </div>

  </div>
</section>
{% endblock %}
'''.replace("__ORIGINAL__", original_inner)

    new_text = text[:match.start()] + wrapper + text[match.end():]
    backup(path)
    path.write_text(new_text, encoding="utf-8")
    print("[PATCH]", path.relative_to(ROOT), "-> professional tracking layout")

CSS_TEXT = r'''
:root,
html[data-perfume-theme="night"]{
  --lux-canvas:#090706;
  --lux-canvas-2:#0f0b08;
  --lux-panel:#17110d;
  --lux-panel-2:#21160f;
  --lux-panel-3:#2b1d13;
  --lux-text:#f7f0e7;
  --lux-muted:#aa9d8f;
  --lux-gold:#c9954d;
  --lux-gold-light:#e3c286;
  --lux-brown:#74451f;
  --lux-line:rgba(218,178,112,.18);
  --lux-line-strong:rgba(218,178,112,.42);
  --lux-shadow:0 28px 80px rgba(0,0,0,.34);

  --p-bg:var(--lux-canvas)!important;
  --p-bg-2:var(--lux-canvas-2)!important;
  --p-surface:var(--lux-panel)!important;
  --p-surface-2:var(--lux-panel-2)!important;
  --p-text:var(--lux-text)!important;
  --p-muted:var(--lux-muted)!important;
  --p-gold:var(--lux-gold)!important;
  --p-gold-deep:var(--lux-brown)!important;
  --p-gold-pale:var(--lux-gold-light)!important;
  --p-line:var(--lux-line)!important;
  --p-line-strong:var(--lux-line-strong)!important;
  --p-shadow:var(--lux-shadow)!important;
}

html[data-perfume-theme="day"]{
  --lux-canvas:#eee2d4;
  --lux-canvas-2:#e1cfbb;
  --lux-panel:#fffaf4;
  --lux-panel-2:#f1e3d2;
  --lux-panel-3:#d8bfa2;
  --lux-text:#18120e;
  --lux-muted:#75675a;
  --lux-gold:#a67332;
  --lux-gold-light:#c5934c;
  --lux-brown:#75471f;
  --lux-line:rgba(103,64,29,.15);
  --lux-line-strong:rgba(135,84,35,.34);
  --lux-shadow:0 26px 65px rgba(77,48,23,.13);

  --p-bg:var(--lux-canvas)!important;
  --p-bg-2:var(--lux-canvas-2)!important;
  --p-surface:var(--lux-panel)!important;
  --p-surface-2:var(--lux-panel-2)!important;
  --p-text:var(--lux-text)!important;
  --p-muted:var(--lux-muted)!important;
  --p-gold:var(--lux-gold)!important;
  --p-gold-deep:var(--lux-brown)!important;
  --p-gold-pale:var(--lux-gold-light)!important;
  --p-line:var(--lux-line)!important;
  --p-line-strong:var(--lux-line-strong)!important;
  --p-shadow:var(--lux-shadow)!important;
}

html,body{
  background:var(--lux-canvas)!important;
  color:var(--lux-text)!important;
}

.phase-main{
  min-height:62vh;
  background:
    radial-gradient(circle at 82% 4%,rgba(176,113,52,.08),transparent 21%),
    linear-gradient(180deg,var(--lux-canvas),var(--lux-canvas-2))!important;
}

/* Header */
.p4-top-strip,.phase04-topbar{
  background:#090706!important;
  color:#f0dfc6!important;
}

.p4-header,.phase04-header,.luxury-shop-header{
  border-color:var(--lux-line)!important;
  box-shadow:0 18px 48px rgba(0,0,0,.07)!important;
}

html[data-perfume-theme="night"] .p4-header,
html[data-perfume-theme="night"] .phase04-header,
html[data-perfume-theme="night"] .luxury-shop-header{
  background:linear-gradient(180deg,#0d0a08,#090706)!important;
}

html[data-perfume-theme="day"] .p4-header,
html[data-perfume-theme="day"] .phase04-header,
html[data-perfume-theme="day"] .luxury-shop-header{
  background:linear-gradient(180deg,#fffaf4,#f0e4d5)!important;
}

.p4-search,.phase04-search{
  background:var(--lux-panel)!important;
  border-color:var(--lux-line)!important;
}

html[data-perfume-theme="day"] .p4-search,
html[data-perfume-theme="day"] .phase04-search{
  background:#fffdf9!important;
}

.p4-nav a,.phase04-nav a{color:var(--lux-muted)!important}
.p4-nav a:hover,.phase04-nav a:hover{color:var(--lux-gold)!important}

/* Make the storefront layered instead of one flat color */
.p5-category-section{background:var(--lux-canvas)!important}
.p5-products-light{background:var(--lux-panel)!important}
.p5-promo-section{background:var(--lux-canvas-2)!important}
.p5-products-dark{
  background:linear-gradient(180deg,var(--lux-panel-2),var(--lux-canvas-2))!important;
}
.p5-shop-guide{background:var(--lux-panel)!important}
.p5-brands{background:var(--lux-canvas-2)!important}

html[data-perfume-theme="day"] .p5-category-section{background:#eee2d3!important}
html[data-perfume-theme="day"] .p5-products-light{background:#fffaf4!important}
html[data-perfume-theme="day"] .p5-promo-section{background:#e2d0bc!important}
html[data-perfume-theme="day"] .p5-products-dark{
  background:linear-gradient(180deg,#d6bda0,#eadfd1)!important;
}
html[data-perfume-theme="day"] .p5-shop-guide{background:#fffaf4!important}
html[data-perfume-theme="day"] .p5-brands{background:#dfccb6!important}

.p5-category-grid a,
.p5-shop-card,
.p5-shop-guide-copy,
.p5-guide-cards article,
.p5-promo-card,
.p5-quick-grid a,
.p4-product-card,
.p4-filter,
.p4-toolbar,
.p4-service-menu,
.p4-service-content,
.auth-lux-card,
.auth-lux-form-side{
  border-color:var(--lux-line)!important;
}

html[data-perfume-theme="night"] .p5-category-grid a,
html[data-perfume-theme="night"] .p5-shop-card,
html[data-perfume-theme="night"] .p5-shop-guide-copy,
html[data-perfume-theme="night"] .p5-guide-cards article,
html[data-perfume-theme="night"] .p5-promo-card,
html[data-perfume-theme="night"] .p5-quick-grid a,
html[data-perfume-theme="night"] .p4-product-card,
html[data-perfume-theme="night"] .p4-filter,
html[data-perfume-theme="night"] .p4-toolbar,
html[data-perfume-theme="night"] .p4-service-menu,
html[data-perfume-theme="night"] .p4-service-content{
  background:linear-gradient(145deg,#18110d,#21160f)!important;
}

html[data-perfume-theme="day"] .p5-category-grid a,
html[data-perfume-theme="day"] .p5-shop-card,
html[data-perfume-theme="day"] .p5-shop-guide-copy,
html[data-perfume-theme="day"] .p5-guide-cards article,
html[data-perfume-theme="day"] .p5-quick-grid a,
html[data-perfume-theme="day"] .p4-product-card,
html[data-perfume-theme="day"] .p4-filter,
html[data-perfume-theme="day"] .p4-toolbar,
html[data-perfume-theme="day"] .p4-service-menu,
html[data-perfume-theme="day"] .p4-service-content{
  background:linear-gradient(145deg,#fffdf9,#f3e7d8)!important;
}

html[data-perfume-theme="day"] .p5-promo-card{
  background:
    radial-gradient(circle at 82% 25%,rgba(170,109,45,.09),transparent 24%),
    linear-gradient(130deg,#fffaf4,#dfc6aa)!important;
}

html[data-perfume-theme="night"] .p5-shop-card-media,
html[data-perfume-theme="night"] .p4-product-media{
  background:
    radial-gradient(circle at 50% 72%,rgba(149,88,35,.14),transparent 42%),
    #100c09!important;
}

html[data-perfume-theme="day"] .p5-shop-card-media,
html[data-perfume-theme="day"] .p4-product-media{
  background:
    radial-gradient(circle at 50% 72%,rgba(164,104,47,.11),transparent 42%),
    #f1e4d5!important;
}

.p4-page-hero,.p4-feature-hero,.p4-service-hero{
  border-bottom:1px solid var(--lux-line)!important;
}

html[data-perfume-theme="night"] .p4-page-hero,
html[data-perfume-theme="night"] .p4-feature-hero,
html[data-perfume-theme="night"] .p4-service-hero{
  background:
    radial-gradient(circle at 78% 25%,rgba(178,110,48,.13),transparent 22%),
    linear-gradient(120deg,#17100c,#090706)!important;
}

html[data-perfume-theme="day"] .p4-page-hero,
html[data-perfume-theme="day"] .p4-feature-hero,
html[data-perfume-theme="day"] .p4-service-hero{
  background:
    radial-gradient(circle at 78% 25%,rgba(171,109,48,.10),transparent 22%),
    linear-gradient(120deg,#ead7c1,#fffaf4)!important;
}

html[data-perfume-theme="night"] .auth-lux-form-side{background:#17110d!important}
html[data-perfume-theme="day"] .auth-lux-form-side{background:#fffaf4!important}

.auth-lux-visual-side{
  background:
    radial-gradient(circle at 42% 54%,rgba(167,95,37,.22),transparent 27%),
    linear-gradient(135deg,#21150f,#080605 72%)!important;
}

/* Inputs */
html[data-perfume-theme="night"] .phase-main input:not([type="checkbox"]):not([type="radio"]),
html[data-perfume-theme="night"] .phase-main textarea,
html[data-perfume-theme="night"] .phase-main select{
  background:#0f0b09!important;
  color:#f7f0e7!important;
}

html[data-perfume-theme="day"] .phase-main input:not([type="checkbox"]):not([type="radio"]),
html[data-perfume-theme="day"] .phase-main textarea,
html[data-perfume-theme="day"] .phase-main select{
  background:#fffdf9!important;
  color:#18120e!important;
}

/* REAL TRACKING PAGE */
.p6-tracking-page{
  padding:52px 0 90px;
  background:
    radial-gradient(circle at 82% 7%,rgba(168,100,42,.10),transparent 23%),
    var(--lux-canvas);
}

.p6-tracking-shell{
  width:min(1280px,calc(100% - 56px));
  margin:auto;
  display:grid;
  grid-template-columns:.92fr 1.08fr;
  gap:18px;
}

.p6-tracking-intro,
.p6-tracking-card{
  min-height:620px;
  border:1px solid var(--lux-line);
}

.p6-tracking-intro{
  position:relative;
  overflow:hidden;
  padding:48px;
  background:
    radial-gradient(circle at 35% 62%,rgba(157,91,35,.18),transparent 28%),
    linear-gradient(145deg,var(--lux-panel-2),var(--lux-canvas));
}

html[data-perfume-theme="day"] .p6-tracking-intro{
  background:
    radial-gradient(circle at 30% 65%,rgba(152,91,39,.12),transparent 27%),
    linear-gradient(145deg,#d9b995,#f1e4d5)!important;
}

.p6-tracking-eyebrow{
  color:var(--lux-gold);
  letter-spacing:.22em;
  font-size:10px;
}

.p6-tracking-heading{
  position:relative;
  z-index:3;
  max-width:520px;
  margin-top:42px;
}

.p6-tracking-heading>span{
  display:block;
  margin-bottom:8px;
  color:var(--lux-muted);
  font-size:13px;
}

.p6-tracking-heading h1{
  margin:0 0 20px!important;
  color:var(--lux-text)!important;
  font-size:clamp(54px,5vw,82px)!important;
  line-height:.98!important;
  font-weight:800!important;
}

.p6-tracking-heading h1 em{
  color:var(--lux-gold-light);
  font-style:normal;
}

.p6-tracking-heading p{
  color:var(--lux-muted)!important;
  font-size:15px;
  line-height:2;
}

.p6-tracking-steps{
  position:relative;
  z-index:3;
  margin-top:36px;
  display:grid;
  gap:9px;
}

.p6-tracking-steps article{
  padding:13px 14px;
  display:grid;
  grid-template-columns:42px 1fr;
  gap:10px;
  align-items:center;
  border:1px solid var(--lux-line);
  background:color-mix(in srgb,var(--lux-panel) 72%,transparent);
}

html[data-perfume-theme="day"] .p6-tracking-steps article{
  background:rgba(255,250,244,.5);
}

.p6-tracking-steps b{
  color:var(--lux-gold);
  font-size:11px;
}

.p6-tracking-steps strong{
  display:block;
  color:var(--lux-text);
  font-size:13px;
}

.p6-tracking-steps small{
  color:var(--lux-muted)!important;
  font-size:10px;
}

.p6-tracking-art{
  position:absolute;
  left:-40px;
  bottom:-75px;
  width:330px;
  height:330px;
}

.p6-orbit{
  position:absolute;
  border:1px solid var(--lux-line-strong);
  border-radius:50%;
}

.orbit-a{
  inset:40px 0 90px;
  transform:rotate(-18deg);
}

.orbit-b{
  inset:10px 100px 30px 65px;
  transform:rotate(34deg);
}

.p6-track-mark{
  position:absolute;
  left:115px;
  top:105px;
  width:80px;
  height:80px;
  border:1px solid var(--lux-line-strong);
  border-radius:50%;
  background:var(--lux-panel);
  display:grid;
  place-items:center;
  color:var(--lux-gold);
  font-size:26px;
}

.p6-tracking-card{
  padding:50px 48px;
  background:var(--lux-panel);
  box-shadow:var(--lux-shadow);
}

html[data-perfume-theme="day"] .p6-tracking-card{
  background:linear-gradient(145deg,#fffdf9,#f1e4d5)!important;
}

.p6-tracking-card-head{
  padding-bottom:24px;
  margin-bottom:25px;
  border-bottom:1px solid var(--lux-line);
}

.p6-tracking-card-head>span{
  color:var(--lux-gold);
  letter-spacing:.2em;
  font-size:9px;
}

.p6-tracking-card-head h2{
  margin:8px 0 5px!important;
  color:var(--lux-text)!important;
  font-size:32px!important;
}

.p6-tracking-card-head p{
  margin:0;
  color:var(--lux-muted)!important;
  font-size:12px;
}

.p6-track-original{
  width:100%!important;
  max-width:none!important;
  min-height:0!important;
  margin:0!important;
  padding:0!important;
  position:static!important;
  float:none!important;
  color:var(--lux-text)!important;
}

.p6-track-original > *{
  max-width:none!important;
  margin-right:0!important;
  margin-left:0!important;
  position:static!important;
  float:none!important;
}

.p6-track-original h1,
.p6-track-original h2{
  margin:0 0 12px!important;
  color:var(--lux-text)!important;
  font-size:24px!important;
}

.p6-track-original p{
  color:var(--lux-muted)!important;
  line-height:1.9!important;
}

.p6-track-original form{
  width:100%!important;
  max-width:none!important;
  margin:22px 0 0!important;
  padding:0!important;
  display:grid!important;
  grid-template-columns:1fr!important;
  gap:15px!important;
  position:static!important;
  float:none!important;
}

.p6-track-original form > *{
  width:100%!important;
  max-width:none!important;
  margin:0!important;
  position:static!important;
  float:none!important;
}

.p6-track-original label{
  display:grid!important;
  gap:7px!important;
  color:var(--lux-muted)!important;
  font-size:12px!important;
}

.p6-track-original input:not([type="checkbox"]):not([type="radio"]),
.p6-track-original select,
.p6-track-original textarea{
  width:100%!important;
  min-width:0!important;
  min-height:54px!important;
  padding:0 14px!important;
  border:1px solid var(--lux-line)!important;
  background:var(--lux-canvas)!important;
  color:var(--lux-text)!important;
  outline:none!important;
  box-shadow:none!important;
}

html[data-perfume-theme="day"] .p6-track-original input:not([type="checkbox"]):not([type="radio"]),
html[data-perfume-theme="day"] .p6-track-original select,
html[data-perfume-theme="day"] .p6-track-original textarea{
  background:#fffdf9!important;
  color:#18120e!important;
}

.p6-track-original input:focus,
.p6-track-original select:focus,
.p6-track-original textarea:focus{
  border-color:var(--lux-line-strong)!important;
  box-shadow:0 0 0 4px rgba(190,137,70,.07)!important;
}

.p6-track-original button,
.p6-track-original input[type="submit"]{
  width:100%!important;
  min-height:54px!important;
  padding:0 18px!important;
  border:0!important;
  background:linear-gradient(120deg,var(--lux-gold-light),var(--lux-brown))!important;
  color:#171008!important;
  font-weight:700!important;
  cursor:pointer!important;
}

.p6-track-original table{
  width:100%!important;
  margin-top:24px!important;
  border-collapse:collapse!important;
}

.p6-track-original th,
.p6-track-original td{
  padding:12px!important;
  border:1px solid var(--lux-line)!important;
  color:var(--lux-text)!important;
}

.p6-track-original th{
  background:var(--lux-panel-2)!important;
  color:var(--lux-gold)!important;
}

/* Footer intentionally dark in both modes */
.p4-footer,.phase04-footer,.phase-footer{
  background:#090706!important;
  color:#f7efe5!important;
  border-top:1px solid rgba(218,178,112,.18)!important;
}

.p4-footer h2,.phase04-footer h2,.phase-footer h2{
  color:#f7efe5!important;
}

.p4-footer p,.p4-footer a,
.phase04-footer p,.phase04-footer a,
.phase-footer p,.phase-footer a{
  color:#aa9d8e!important;
}

@media(max-width:1000px){
  .p6-tracking-shell{grid-template-columns:1fr}
  .p6-tracking-intro,.p6-tracking-card{min-height:auto}
  .p6-tracking-art{opacity:.45}
}

@media(max-width:680px){
  .p6-tracking-page{padding:24px 0 55px}
  .p6-tracking-shell{width:calc(100% - 24px);gap:12px}
  .p6-tracking-intro,.p6-tracking-card{padding:28px 20px}
  .p6-tracking-heading{margin-top:25px}
  .p6-tracking-heading h1{font-size:48px!important}
  .p6-tracking-art{display:none}
}
'''

JS_TEXT = r'''
(() => {
  "use strict";

  function setTheme(theme){
    document.documentElement.dataset.perfumeTheme = theme;
    try { localStorage.setItem("velora-theme", theme); } catch (_) {}
  }

  document.addEventListener("click", event => {
    const btn = event.target.closest("[data-theme-toggle]");
    if(!btn) return;

    const current = document.documentElement.dataset.perfumeTheme || "night";
    setTheme(current === "night" ? "day" : "night");
  });

  document.addEventListener("DOMContentLoaded", () => {
    try {
      const saved = localStorage.getItem("velora-theme");
      if(saved === "day" || saved === "night"){
        document.documentElement.dataset.perfumeTheme = saved;
      }
    } catch (_) {}
  });
})();
'''

def main():
    print("=" * 82)
    print(" PHASE 06 — LUXURY THEME + ORDER TRACKING FIX")
    print("=" * 82)

    if not (ROOT / "manage.py").exists():
        raise SystemExit("Put this file beside manage.py.")

    if BACKUP.exists():
        raise SystemExit(
            f"Backup already exists: {BACKUP}\n"
            "Rename/delete it only if you intentionally want to rerun Phase 06."
        )

    BACKUP.mkdir(parents=True)

    snapshot = {
        rel: (ROOT / rel).read_bytes()
        for rel in BACKEND_GUARD
        if (ROOT / rel).exists()
    }

    tracking = find_tracking_template()
    if not tracking:
        raise RuntimeError("Could not automatically locate the order-tracking template.")

    print("\nSelected tracking template:")
    print(" ", tracking.relative_to(ROOT))

    write(CSS, CSS_TEXT)
    write(JS, JS_TEXT)
    patch_base()
    patch_tracking_template(tracking)

    for rel, before in snapshot.items():
        if (ROOT / rel).read_bytes() != before:
            raise RuntimeError("Backend changed unexpectedly: " + rel)

    run(sys.executable, "manage.py", "check")
    run(sys.executable, "manage.py", "makemigrations", "--check", "--dry-run")

    print("\n" + "=" * 82)
    print(" PHASE 06 READY")
    print("=" * 82)
    print("✓ Day mode: warm white + light brown + gold sections")
    print("✓ Night mode: black + layered brown + gold sections")
    print("✓ Cards and sections no longer blend together")
    print("✓ Real tracking template patched directly")
    print("✓ Existing tracking form/action/field names preserved")
    print("✓ Backend unchanged")
    print("\nRun:")
    print("  python manage.py runserver")

if __name__ == "__main__":
    main()
