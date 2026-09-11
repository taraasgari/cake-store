# Perfume Shop

اولین فروشگاه مشتق‌شده از `shop-starter`.

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
pip install -e ..\shop-core
python manage.py migrate
python manage.py apply_store_profile store_profile.json
python manage.py createsuperuser
python manage.py runserver
```

نام برند فعلاً `فروشگاه عطر` است و بعداً بدون دست‌زدن به Core قابل تغییر است.
