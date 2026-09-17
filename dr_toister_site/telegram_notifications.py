import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def telegram_is_configured():
    return bool(
        settings.TELEGRAM_NOTIFICATIONS_ENABLED
        and settings.TELEGRAM_BOT_TOKEN
    )


def send_telegram_message(
        *,
        chat_id,
        text,
):
    if not settings.TELEGRAM_NOTIFICATIONS_ENABLED:
        return False

    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning(
            "Telegram-сповіщення увімкнені, "
            "але TELEGRAM_BOT_TOKEN не задано."
        )
        return False

    if not chat_id:
        logger.warning(
            "Telegram-сповіщення не надіслано: "
            "не задано ID групи."
        )
        return False

    url = (
        "https://api.telegram.org/bot"
        f"{settings.TELEGRAM_BOT_TOKEN}"
        "/sendMessage"
    )

    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }
    ).encode("utf-8")

    request = Request(
        url=url,
        data=payload,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(
                request,
                timeout=settings.TELEGRAM_REQUEST_TIMEOUT,
        ) as response:
            response_data = json.loads(
                response.read().decode("utf-8")
            )

        if not response_data.get("ok"):
            logger.warning(
                "Telegram API повернув "
                "невдалу відповідь."
            )
            return False

        return True

    except (
            HTTPError,
            URLError,
            TimeoutError,
            ValueError,
    ) as error:
        logger.warning(
            (
                "Не вдалося надіслати "
                "Telegram-повідомлення: %s"
            ),
            error,
        )
        return False


def get_customer_type_label(user):
    if user is None:
        return "Гість"

    if not user.is_authenticated:
        return "Гість"

    if not user.is_cosmetologist:
        return "Звичайний клієнт"

    if user.is_cosmetologist_verified:
        return "Підтверджений косметолог"

    return "Непідтверджений косметолог"


def format_booking_message(booking):
    lines = [
        "НОВИЙ ЗАПИС НА ПРОЦЕДУРУ",
        "",
        f"Запис №{booking.pk}",
        f"Клієнт: {booking.client_name}",
        f"Телефон: {booking.client_phone}",
        (
            "Процедура: "
            f"{booking.procedure.name}"
        ),
        (
            "Дата: "
            f"{booking.date:%d.%m.%Y}"
        ),
        (
            "Час: "
            f"{booking.start_time:%H:%M}"
            "–"
            f"{booking.end_time:%H:%M}"
        ),
        (
            "Вартість: "
            f"{booking.price_at_booking:.2f} грн"
        ),
        (
            "Тип клієнта: "
            f"{get_customer_type_label(booking.client)}"
        ),
        (
                "CRM: "
                + (
                    "так"
                    if booking.customer_id
                    else "ні"
                )
        ),
    ]

    if booking.client_note:
        lines.extend(
            [
                "",
                (
                    "Коментар: "
                    f"{booking.client_note}"
                ),
            ]
        )

    return "\n".join(lines)


def format_order_message(order):
    order_items = (
        order.items.select_related(
            "product"
        ).all()
    )

    lines = [
        "НОВЕ ЗАМОВЛЕННЯ",
        "",
        f"Замовлення №{order.pk}",
        f"Покупець: {order.client_name}",
        f"Телефон: {order.client_phone}",
        (
            "Тип покупця: "
            f"{get_customer_type_label(order.client)}"
        ),
        "",
        "Товари:",
    ]

    has_professional_products = False

    for item in order_items:
        if (
                item.product.availability
                == item.product.Availability.PROFESSIONALS_ONLY
        ):
            has_professional_products = True

        lines.append(
            (
                f"• {item.product.name} "
                f"× {item.quantity} — "
                f"{item.subtotal:.2f} грн"
            )
        )

    lines.extend(
        [
            "",
            (
                "Загальна сума: "
                f"{order.total_price:.2f} грн"
            ),
            (
                    "Професійні препарати: "
                    + (
                        "так"
                        if has_professional_products
                        else "ні"
                    )
            ),
            (
                "Джерело: "
                f"{order.get_source_display()}"
            ),
        ]
    )

    return "\n".join(lines)


def format_course_application_message(
        application,
):
    course = application.course

    if (
            course.audience
            == course.Audience.COSMETOLOGISTS
    ):
        course_group = (
            "Підвищення кваліфікації"
        )
    else:
        course_group = "Школа догляду"

    application_datetime = timezone.localtime(
        application.enrolled_at
    )

    lines = [
        "НОВА ЗАЯВКА НА НАВЧАННЯ",
        "",
        f"Заявка №{application.pk}",
        (
            "Програма: "
            f"{course.title}"
        ),
        f"Розділ: {course_group}",
        (
            "Формат: "
            f"{course.get_format_display()}"
        ),
        (
            "Заявник: "
            f"{application.applicant_name}"
        ),
        (
            "Телефон: "
            f"{application.applicant_phone}"
        ),
        (
            "Тип користувача: "
            f"{get_customer_type_label(application.student)}"
        ),
        (
            "Вартість: "
            f"{application.price_at_enrollment:.2f} грн"
        ),
        (
            "Дата заявки: "
            f"{application_datetime:%d.%m.%Y %H:%M}"
        ),
    ]

    if application.applicant_comment:
        lines.extend(
            [
                "",
                (
                    "Коментар: "
                    f"{application.applicant_comment}"
                ),
            ]
        )

    return "\n".join(lines)


def send_booking_notification(booking):
    return send_telegram_message(
        chat_id=settings.TELEGRAM_BOOKINGS_CHAT_ID,
        text=format_booking_message(
            booking
        ),
    )


def send_order_notification(order):
    return send_telegram_message(
        chat_id=settings.TELEGRAM_ORDERS_CHAT_ID,
        text=format_order_message(
            order
        ),
    )


def send_course_application_notification(
        application,
):
    return send_telegram_message(
        chat_id=settings.TELEGRAM_COURSES_CHAT_ID,
        text=format_course_application_message(
            application
        ),
    )


def format_daily_bookings_message(
        bookings,
        reminder_date,
):
    lines = [
        (
            "ЗАПИСИ НА "
            f"{reminder_date:%d.%m.%Y}"
        ),
        "",
    ]

    if not bookings:
        lines.append(
            "На сьогодні записів немає."
        )
        return "\n".join(lines)

    for booking in bookings:
        lines.extend(
            [
                (
                    f"{booking.start_time:%H:%M} — "
                    f"{booking.procedure.name}"
                ),
                (
                    f"{booking.client_name} · "
                    f"{booking.client_phone}"
                ),
                (
                    "Статус: "
                    f"{booking.get_status_display()}"
                ),
                "",
            ]
        )

    lines.append(
        f"Усього записів: {len(bookings)}"
    )

    return "\n".join(lines)


def notify_booking_created(booking_id):
    from appointments.models import Booking

    try:
        booking = (
            Booking.objects.select_related(
                "procedure",
                "client",
                "customer",
            )
            .get(pk=booking_id)
        )
    except Booking.DoesNotExist:
        logger.warning(
            "Telegram: запис №%s "
            "не знайдено.",
            booking_id,
        )
        return False

    return send_booking_notification(
        booking
    )


def notify_order_created(order_id):
    from shop.models import Order

    try:
        order = (
            Order.objects.select_related(
                "client",
                "customer",
            )
            .prefetch_related(
                "items__product"
            )
            .get(pk=order_id)
        )
    except Order.DoesNotExist:
        logger.warning(
            "Telegram: замовлення №%s "
            "не знайдено.",
            order_id,
        )
        return False

    return send_order_notification(
        order
    )


def notify_course_application_created(
        application_id,
):
    from academy.models import CourseEnrollment

    try:
        application = (
            CourseEnrollment.objects.select_related(
                "course",
                "student",
                "customer",
            )
            .get(pk=application_id)
        )
    except CourseEnrollment.DoesNotExist:
        logger.warning(
            "Telegram: заявку на навчання "
            "№%s не знайдено.",
            application_id,
        )
        return False

    return send_course_application_notification(
        application
    )
