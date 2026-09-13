Perfume Shop mobile responsive fix — V2

This replaces the previous perfume-mobile-final.css.

What V2 fixes:
- Mobile slider no longer crops/zooms the desktop artwork.
  The active slide takes its height from the image's natural aspect ratio.
- Built-in slider and uploaded slider images use object-fit: contain on mobile.
- Home hero no longer overlaps or cuts the Persian heading.
- The "Special discounts / Best sellers / New arrivals / All products" cards
  are SIDE-BY-SIDE on mobile in a horizontal swipe row instead of stacking down the page.
- Desktop is still untouched: the stylesheet is loaded only under max-width: 900px
  and every rule in this file is mobile-scoped.

Install:
1) Replace:
   static/css/perfume-mobile-final.css
   with the V2 file in this ZIP.

2) Keep this line in first/templates/perfume_base.html after perfume-account-menu.css:
   <link rel="stylesheet" href="{% static 'css/perfume-mobile-final.css' %}?v=2" media="(max-width: 900px)">

   If you already have ?v=1, change it to ?v=2 to bypass browser/static cache.

3) Commit/push:
   git add static/css/perfume-mobile-final.css first/templates/perfume_base.html
   git commit -m "Fix mobile slider and horizontal home cards"
   git push origin main

4) Render:
   If Auto-Deploy is enabled, it deploys automatically.
   Otherwise use Manual Deploy -> Deploy latest commit.
   If old CSS remains, use Clear build cache & deploy.

Checks:
   python manage.py check

After deploy, hard-refresh/mobile incognito is recommended.
