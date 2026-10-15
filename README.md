# MESC Copilot demo

این مخزن یک نمونه مصنوعی برای توسعه جست‌وجوی کدهای کالا است. هیچ کدی در این مجموعه به‌عنوان کد معتبر سازمانی یا کاتالوگ رسمی MESC تأیید نشده است.

## ساخت داده و ایندکس

```powershell
python scripts/generate_demo.py
```

این دستور فایل CSV و پایگاه داده SQLite با جدول اصلی و FTS5 می‌سازد. داده شامل ۳۱۰۰ رکورد مصنوعی دوزبانه، ویژگی‌های فنی، کدهای ساختاری شبیه MESC، وضعیت فعال/غیرفعال و provenance است.

## ساخت Excel

```powershell
$env:NODE_PATH = 'C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'
& 'C:\Users\ASUS\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' scripts/build_catalog.mjs
```

خروجی در `outputs/mesc_synthetic_catalog.xlsx` ذخیره می‌شود.

## جست‌وجوی نمونه

```powershell
python scripts/search_mesc.py "لوله دو اینچی پلاستیکی برند داچ" --limit 10
```

جست‌وجو در این نسخه با جدول SQLite و ایندکس‌های نوع کالا، سایز، خانواده جنس و برند انجام می‌شود و سپس با امتیازدهی ساختاری رتبه‌بندی می‌شود. برای نسخه اولیه به embedding خارجی نیاز نیست. پس از رسیدن داده واقعی می‌توان همین قرارداد را به embedding محلی و رتبه‌بندی ترکیبی گسترش داد.

## بررسی سریع

```powershell
python scripts/check_demo.py
```

## اجرای FastAPI

ابتدا وابستگی‌ها را نصب کنید:

```powershell
python -m pip install -r requirements.txt
```

برای تست با OpenRouter:

```powershell
$env:LLM_PROVIDER = "openrouter"
$env:OPENROUTER_API_KEY = "YOUR_KEY"
$env:LLM_MODEL = "google/gemini-2.5-flash"
uvicorn app:app --reload
```

فایل `.env` در ریشه پروژه به‌صورت خودکار خوانده می‌شود؛ بعد از هر تغییر در آن باید سرویس را restart کنید. متغیرهای محیطی واقعی، در صورت وجود، بر `.env` اولویت دارند.

برای دسترسی از سیستم‌های دیگر در شبکه محلی:

```powershell
.\run_network.ps1
```

آدرس چاپ‌شده شبیه `http://192.168.1.25:8000` خواهد بود. سیستم‌های دیگر باید به همان شبکه وصل باشند و Windows Firewall باید اجازه ورودی به پورت ۸۰۰۰ را بدهد.

برای استفاده مستقیم از Gemini:

```powershell
$env:LLM_PROVIDER = "gemini"
$env:GEMINI_API_KEY = "YOUR_KEY"
$env:LLM_MODEL = "gemini-2.5-flash"
uvicorn app:app --reload
```

سپس به `POST /search` یک JSON مثل زیر بفرستید:

```json
{
  "query": "لوله دو اینچی پلاستیکی برند داچ",
  "limit": 10,
  "use_ai": true
}
```

در PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/search -ContentType "application/json" -Body '{"query":"لوله دو اینچی پلاستیکی برند داچ","limit":10,"use_ai":true}'
```

در PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/search -ContentType "application/json" -Body '{"query":"لوله دو اینچی پلاستیکی برند داچ","limit":10,"use_ai":true}'
```

اگر کلید API تنظیم نشده باشد یا سرویس خطا بدهد، API به parser قطعی فعلی fallback می‌کند و در `ai_error` علت را برمی‌گرداند. مدل فقط مشخصات جست‌وجو را استخراج می‌کند؛ کد MESC را تولید نمی‌کند.

سناریوهای عجیب و پاسخ‌های فعلی در [TEST_QUERIES.md](<E:/projs/MESC/TEST_QUERIES.md>) قرار دارند. برای بازتولید آن‌ها:

```powershell
python scripts/write_test_queries.py
```

## قرارداد داده

ستون‌های اصلی شامل `mesc_code`, `description_en`, `description_fa`, `manufacturer`, `material`, `material_family`, `size_inch`, `pressure_class`, `connection`, `standard`, `status`, `catalogue_revision`, `source` و `is_synthetic` هستند.
