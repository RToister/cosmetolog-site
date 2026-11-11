from django.conf import settings


def site(request):
    return {
        "site_contacts": {
            "phone": settings.SITE_PHONE,
            "email": settings.SITE_EMAIL,
            "address": settings.SITE_ADDRESS,
            "instagram_url": settings.SITE_INSTAGRAM_URL,
            "telegram_url": settings.SITE_TELEGRAM_URL,
        },
    }
