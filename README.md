# DR TOISTER — сайт косметолога

Django-сайт клініки косметології: публічні сторінки, онлайн-запис на процедури,
магазин (з професійним асортиментом для підтверджених косметологів),
навчальні курси, CRM, аналітика та Telegram-сповіщення.

## Локальний запуск

Потрібен Python 3.12 або новіший (перевірка: `python3 --version`).
На macOS команда `python` може вказувати на старий Python 2.7, тому
використовуйте `python3`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

За бажанням перед `runserver` можна заповнити базу демо-даними:

```bash
python manage.py create_demo_data --clear
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

## Зображення

Ілюстрації сайту лежать у `static/img/` і виконані в одному стилі
(кремовий, пудровий і какао-кольори фірмової палітри):

- `hero.svg` — головний банер;
- `doctor.svg` — тимчасовий портрет лікаря на головній і на сторінці
  «Про лікаря». Щоб поставити справжнє фото, покладіть його в `static/img/`
  (наприклад, `doctor.jpg`) і замініть `img/doctor.svg` на `img/doctor.jpg`
  у `templates/home.html` та `templates/about.html`;
- `product-*.svg`, `course-*.svg`, `procedure-*.svg` — ілюстрації товарів,
  курсів і процедур.

Якщо в адмінці для товару або курсу завантажено фото, показується воно.
Якщо фото немає, ілюстрація підбирається автоматично за назвою
(правила — у `dr_toister_site/illustrations.py`).
