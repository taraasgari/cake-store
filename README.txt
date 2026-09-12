Perfume Shop — Final audited build

Local run (Windows PowerShell):
cd C:\Users\Tara\Desktop\perfume-shop
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py test
python manage.py runserver

The shared shop_core package is bundled inside vendor/shop-core and is loaded automatically.
Before the final Git commit, run .\FINAL_CLEANUP.ps1 once to remove old backup/phase files, then run git add -A.
