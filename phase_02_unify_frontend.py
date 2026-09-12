#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations
import re, shutil, subprocess, sys, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / '.perfume_frontend_phase02_backup'
BASE = ROOT / 'first/templates/perfume_base.html'
INDEX = ROOT / 'first/templates/index.html'
CSS = ROOT / 'static/css/perfume-global-compat.css'

BACKEND = [
    'first/views.py','first/models.py','first/urls.py','first/forms.py',
    'first/context_processors.py','customer_care/views.py',
    'customer_care/models.py','customer_care/urls.py',
]
EXCLUDE = {'admin','dashboard','emails','email','includes','partials','components'}

def run(*args):
    print('\n> ' + ' '.join(map(str,args)))
    p = subprocess.run(list(args), cwd=ROOT, text=True)
    if p.returncode:
        raise RuntimeError('Command failed: ' + ' '.join(map(str,args)))

def backup(path: Path):
    if not path.exists():
        return
    dst = BACKUP / path.relative_to(ROOT)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)

def patch_templates():
    changed = []
    pattern = r'{%\s*extends\s+([\'\"])base\.html\1\s*%}'
    for root in (ROOT/'first/templates', ROOT/'customer_care/templates'):
        if not root.exists():
            continue
        for path in root.rglob('*.html'):
            parts = {x.lower() for x in path.parts}
            if parts & EXCLUDE:
                continue
            if path.name in {'base.html','perfume_base.html','index.html'}:
                continue
            txt = path.read_text(encoding='utf-8')
            new = re.sub(pattern, "{% extends 'perfume_base.html' %}", txt, count=1)
            if new != txt:
                backup(path)
                path.write_text(new, encoding='utf-8')
                changed.append(path.relative_to(ROOT).as_posix())
    return changed

GLOBAL_CSS = r'''
html, body, .phase-main, .phase-main *, .luxury-shop-header, .phase-footer,
button, input, select, textarea {
  font-family: Vazir, Tahoma, Arial, sans-serif !important;
}
.phase-main {
  min-height: 60vh;
  color: var(--p-text);
  background: radial-gradient(circle at 85% 0%, rgba(176,116,48,.06), transparent 24%), var(--p-bg);
}
.phase-main h1,.phase-main h2,.phase-main h3,.phase-main h4,.phase-main h5,.phase-main h6 {
  color: var(--p-text) !important;
  font-family: Vazir, Tahoma, Arial, sans-serif !important;
}
.phase-main p,.phase-main small,.phase-main [class*="text-gray-"],.phase-main [class*="text-slate-"] {
  color: var(--p-muted) !important;
}
.phase-main [class*="text-pink-"],.phase-main [class*="text-purple-"],.phase-main [class*="text-fuchsia-"],.phase-main [class*="text-rose-"] {
  color: var(--p-gold) !important;
}
.phase-main [class*="bg-pink-"],.phase-main [class*="bg-purple-"],.phase-main [class*="bg-fuchsia-"],.phase-main [class*="bg-rose-"] {
  background: var(--p-gold) !important;
  color: #171008 !important;
}
.phase-main [class*="border-pink-"],.phase-main [class*="border-purple-"],.phase-main [class*="border-fuchsia-"],.phase-main [class*="border-rose-"],.phase-main [class*="border-gray-"],.phase-main [class*="border-slate-"] {
  border-color: var(--p-line) !important;
}
.phase-main [class~="bg-white"],.phase-main [class*="bg-gray-50"],.phase-main [class*="bg-gray-100"],.phase-main [class*="bg-slate-50"] {
  background: var(--p-surface) !important;
  color: var(--p-text) !important;
}
.phase-main :is(.card,.panel,.box,.product-card,.order-card,.profile-card,.summary-card,.checkout-card,.wishlist-card) {
  background: linear-gradient(145deg,var(--p-surface),var(--p-surface-2)) !important;
  border-color: var(--p-line) !important;
  color: var(--p-text) !important;
  box-shadow: 0 18px 55px rgba(0,0,0,.09);
}
.phase-main input:not([type="checkbox"]):not([type="radio"]),.phase-main textarea,.phase-main select {
  background: color-mix(in srgb,var(--p-surface) 88%,transparent) !important;
  border-color: var(--p-line) !important;
  color: var(--p-text) !important;
  outline: none !important;
}
.phase-main input:focus,.phase-main textarea:focus,.phase-main select:focus {
  border-color: var(--p-line-strong) !important;
  box-shadow: 0 0 0 4px rgba(216,179,109,.055) !important;
}
.phase-main :is(.btn-primary,.button-primary,.primary-btn,input[type="submit"]) {
  background: linear-gradient(120deg,var(--p-gold-pale),var(--p-gold-deep)) !important;
  color: #171008 !important;
  border-color: transparent !important;
}
.phase-main a:hover { color: var(--p-gold); }
.phase-main table,.phase-main th,.phase-main td { border-color: var(--p-line) !important; }
.phase-main th { background: var(--p-surface-2) !important; color: var(--p-gold) !important; }
.phase-main .min-h-screen { min-height: auto !important; }

.home-shop-section {
  max-width: var(--p-max);
  margin: auto;
  padding: 90px 4.5vw;
  border-top: 1px solid var(--p-line);
}
.home-shop-head {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 30px;
  align-items: end;
  margin-bottom: 34px;
}
.home-shop-head h2 {
  margin: 10px 0 0 !important;
  font-size: clamp(38px,4.3vw,62px) !important;
  font-weight: 500 !important;
}
.home-shop-head p { max-width: 600px; color: var(--p-muted); font-size: 10px; }
.home-shop-head>a,.home-shop-more a {
  min-height: 46px;
  padding: 0 20px;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  border: 1px solid var(--p-line-strong);
  font-size: 9px;
}
.home-shop-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; }
.home-shop-card {
  overflow: hidden;
  border: 1px solid var(--p-line);
  background: linear-gradient(145deg,var(--p-surface),var(--p-surface-2));
  transition: .3s;
}
.home-shop-card:hover { transform: translateY(-6px); border-color: var(--p-line-strong); box-shadow: var(--p-shadow); }
.home-shop-media {
  height: 355px;
  position: relative;
  display: grid;
  place-items: center;
  overflow: hidden;
  background: radial-gradient(circle at 50% 72%,rgba(166,104,43,.18),transparent 43%);
}
.home-shop-media img { width:100%; height:100%; object-fit:contain; padding:25px; transition:.4s; }
.home-shop-card:hover img { transform: scale(1.045) translateY(-4px); }
.home-shop-badges { position:absolute; z-index:3; top:11px; right:11px; display:flex; gap:4px; }
.home-shop-badges span { padding:3px 7px; background:var(--p-gold-pale); color:#171008; font-size:6px; }
.home-shop-body { padding:15px; }
.home-shop-body>small { display:block; color:var(--p-gold) !important; font-size:7px; }
.home-shop-body h3 { margin:3px 0 15px !important; font-size:16px !important; font-weight:500 !important; }
.home-shop-bottom { display:flex; align-items:end; justify-content:space-between; gap:12px; }
.home-shop-price strong { display:block; font-size:11px; }
.home-shop-price span,.home-shop-price del { color:var(--p-muted); font-size:7px; }
.home-shop-price del { display:block; }
.home-shop-action {
  width:38px; height:38px; border:1px solid var(--p-line); border-radius:50%; background:none;
  color:var(--p-text); display:grid; place-items:center; cursor:pointer;
}
.home-shop-more { margin-top:22px; display:flex; justify-content:center; }
.home-shop-empty { grid-column:1/-1; padding:55px; border:1px solid var(--p-line); text-align:center; color:var(--p-muted); }
@media(max-width:1050px){.home-shop-grid{grid-template-columns:repeat(3,1fr)}}
@media(max-width:780px){.home-shop-section{padding:60px 20px}.home-shop-head{grid-template-columns:1fr}.home-shop-head>a{width:max-content}.home-shop-grid{grid-template-columns:1fr 1fr}}
@media(max-width:520px){.home-shop-grid{grid-template-columns:1fr}.home-shop-media{height:390px}}
'''

HOME_SECTION = r'''
<!-- PHASE02_HOME_PRODUCTS -->
<section class="home-shop-section">
  <div class="home-shop-head reveal">
    <div>
      <span class="phase-kicker">SHOP THE COLLECTION</span>
      <h2>محصولات فروشگاه</h2>
      <p>محصولات واقعی فروشگاه حالا مستقیم در صفحه اصلی دیده می‌شوند.</p>
    </div>
    <a href="{% url 'first:product_list' %}">مشاهده همه محصولات <i class="fa-solid fa-arrow-left"></i></a>
  </div>

  <div class="home-shop-grid">
    {% for product in new_products|slice:":8" %}
    <article class="home-shop-card reveal">
      <a class="home-shop-media" href="{% url 'first:product_detail' product.slug %}">
        <div class="home-shop-badges">
          {% if product.is_new %}<span>NEW</span>{% endif %}
          {% if product.is_best_seller %}<span>ICON</span>{% endif %}
        </div>
        {% if product.main_image %}<img src="{{ product.main_image.url }}" alt="{{ product.name }}" loading="lazy">{% else %}<div class="mini-css-bottle">V</div>{% endif %}
      </a>
      <div class="home-shop-body">
        <small>{{ product.brand.name|default:'VÉLORA' }}</small>
        <h3><a href="{% url 'first:product_detail' product.slug %}">{{ product.name }}</a></h3>
        <div class="home-shop-bottom">
          <div class="home-shop-price"><strong>{{ product.final_price|price_format }}</strong><span> تومان</span>{% if product.discount_percent %}<del>{{ product.price|price_format }}</del>{% endif %}</div>
          {% if product.has_variants %}
          <a class="home-shop-action" href="{% url 'first:product_detail' product.slug %}"><i class="fa-solid fa-arrow-left"></i></a>
          {% else %}
          <form method="post" action="{% url 'first:add_to_cart' product.id %}">{% csrf_token %}<button class="home-shop-action" type="submit"><i class="fa-solid fa-bag-shopping"></i></button></form>
          {% endif %}
        </div>
      </div>
    </article>
    {% empty %}
      {% for product in featured_products|slice:":8" %}
      <article class="home-shop-card reveal">
        <a class="home-shop-media" href="{% url 'first:product_detail' product.slug %}">{% if product.main_image %}<img src="{{ product.main_image.url }}" alt="{{ product.name }}" loading="lazy">{% else %}<div class="mini-css-bottle">V</div>{% endif %}</a>
        <div class="home-shop-body"><small>{{ product.brand.name|default:'VÉLORA' }}</small><h3><a href="{% url 'first:product_detail' product.slug %}">{{ product.name }}</a></h3><div class="home-shop-bottom"><div class="home-shop-price"><strong>{{ product.final_price|price_format }}</strong><span> تومان</span></div><a class="home-shop-action" href="{% url 'first:product_detail' product.slug %}"><i class="fa-solid fa-arrow-left"></i></a></div></div>
      </article>
      {% empty %}<div class="home-shop-empty">هنوز محصولی برای نمایش وجود ندارد.</div>{% endfor %}
    {% endfor %}
  </div>

  <div class="home-shop-more"><a href="{% url 'first:product_list' %}">ورود به فروشگاه <i class="fa-solid fa-arrow-left"></i></a></div>
</section>
'''

def main():
    print('='*76)
    print(' PHASE 02 — UNIFY FRONTEND + HOME PRODUCTS')
    print('='*76)

    if not (ROOT/'manage.py').exists():
        raise SystemExit('Put this file beside manage.py.')
    if not BASE.exists() or not INDEX.exists():
        raise SystemExit('Phase 01 must exist first.')
    if BACKUP.exists():
        raise SystemExit(f'Backup already exists: {BACKUP}')

    BACKUP.mkdir()
    snap = {p:(ROOT/p).read_bytes() for p in BACKEND if (ROOT/p).exists()}

    changed = patch_templates()

    backup(CSS)
    CSS.parent.mkdir(parents=True, exist_ok=True)
    CSS.write_text(textwrap.dedent(GLOBAL_CSS).lstrip(), encoding='utf-8')
    print('[WRITE] static/css/perfume-global-compat.css')

    base = BASE.read_text(encoding='utf-8')
    if 'perfume-global-compat.css' not in base:
        backup(BASE)
        needle = '<link rel="stylesheet" href="{% static \'css/perfume-phase01.css\' %}">'
        link = '<link rel="stylesheet" href="{% static \'css/perfume-global-compat.css\' %}">'
        if needle in base:
            base = base.replace(needle, needle+'\n    '+link, 1)
        else:
            base = base.replace('{% block extra_css %}', link+'\n    {% block extra_css %}', 1)
        BASE.write_text(base, encoding='utf-8')
        print('[PATCH] perfume_base.html')

    index = INDEX.read_text(encoding='utf-8')
    if 'PHASE02_HOME_PRODUCTS' not in index:
        backup(INDEX)
        marker = '<section class="home-final-quote">'
        if marker in index:
            index = index.replace(marker, HOME_SECTION+'\n\n'+marker, 1)
        else:
            pos = index.rfind('{% endblock %}')
            if pos < 0:
                raise RuntimeError('Could not locate index endblock.')
            index = index[:pos] + HOME_SECTION + '\n\n' + index[pos:]
        INDEX.write_text(index, encoding='utf-8')
        print('[PATCH] index.html -> products section')

    for rel,data in snap.items():
        if (ROOT/rel).read_bytes() != data:
            raise RuntimeError('Backend changed unexpectedly: '+rel)

    run(sys.executable, 'manage.py', 'check')
    run(sys.executable, 'manage.py', 'makemigrations', '--check', '--dry-run')

    print('\n'+'='*76)
    print(' PHASE 02 READY')
    print('='*76)
    print('Customer templates moved to shared perfume shell:', len(changed))
    for rel in changed:
        print('  -', rel)
    print('\n✓ same header/search everywhere')
    print('✓ same footer everywhere')
    print('✓ same Vazir typography')
    print('✓ brown/gold theme on original Core page structures')
    print('✓ products added to Home')
    print('✓ admin/dashboard/email templates untouched')
    print('✓ backend untouched')

if __name__ == '__main__':
    main()
