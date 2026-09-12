# Perfume Shop

فروشگاه عطر مستقل و قابل استقرار؛ `shop_core` موردنیاز پروژه داخل `vendor/shop-core` نگهداری می‌شود.

## وضعیت اولیه

پروفایل `store_profile.json` برای فروشگاه عطر آماده شده و شامل:
- تم لوکس تیره + طلایی/شامپاینی
- دسته‌بندی عطر زنانه، مردانه، یونی‌سکس، سمپل/دکانت و ست هدیه
- Product Typeهای Parfum / EDP / EDT / EDC
- تگ‌های رایحه و کاربرد

## اجرای اولیه

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py apply_store_profile store_profile.json
python manage.py createsuperuser
python manage.py runserver
```

نام برند فعلاً `فروشگاه عطر` است و بعداً بدون دست‌زدن به Core قابل تغییر است.


## بررسی نهایی قبل از Push

```powershell
python manage.py migrate
python manage.py check
python manage.py makemigrations --check
python manage.py test
```

برای پاک‌کردن بکاپ‌ها و اسکریپت‌های توسعه قدیمی یک‌بار `./FINAL_CLEANUP.ps1` را اجرا کنید و سپس `git add -A` بزنید.
