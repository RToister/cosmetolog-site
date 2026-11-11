# DR TOISTER — сайт косметолога

Django-сайт клініки косметології: публічні сторінки, онлайн-запис на процедури,
магазин (з професійним асортиментом для підтверджених косметологів),
навчальні курси, CRM, аналітика та Telegram-сповіщення.

## Локальний запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py create_demo_data --clear   # необов'язково: демо-дані
python manage.py runserver
```

## Перевірки

```bash
python manage.py test
flake8
```

## Продакшн

У `.env` обов'язково задайте:

- `DJANGO_DEBUG=False`
- `DJANGO_SECRET_KEY` — довгий випадковий ключ (без нього сайт не запуститься);
- `DJANGO_ALLOWED_HOSTS` і `DJANGO_CSRF_TRUSTED_ORIGINS` (наприклад `https://example.com`);
- `DJANGO_BEHIND_PROXY=True`, якщо HTTPS завершується на nginx/балансувальнику;
- `DJANGO_SECURE_HSTS_SECONDS` — вмикайте лише після перевірки, що весь сайт працює через HTTPS.

Контакти у футері сайту задаються змінними `SITE_PHONE`, `SITE_EMAIL`,
`SITE_ADDRESS`, `SITE_INSTAGRAM_URL`, `SITE_TELEGRAM_URL`.

Щоденне нагадування про записи в Telegram:

```bash
python manage.py send_daily_booking_reminder
```
