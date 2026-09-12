# Final Audit Fix — Perfume Shop

1. Extract this ZIP directly inside `C:\Users\Tara\Desktop\perfume-shop`.
2. Choose **Replace All** when Windows asks.
3. Activate the existing venv.
4. Run:

```powershell
python manage.py migrate
python manage.py check
python manage.py makemigrations --check
python manage.py test
```

5. Test login, home slider, cart/checkout, order detail, admin orders/PDF, category, brand, password reset, tracking, customizer, and image uploads.
6. Run `./FINAL_CLEANUP.ps1` once to delete legacy backup/phase files.
7. Then commit with `git add -A`, commit, and push.

The project now carries its required `shop_core` inside `vendor/shop-core`, so a separate sibling `../shop-core` installation is no longer required.
