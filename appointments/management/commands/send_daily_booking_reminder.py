from datetime import datetime

from django.conf import settings
from django.core.management.base import (
    BaseCommand,
    CommandError,
)
from django.utils import timezone

from appointments.models import Booking
from dr_toister_site.telegram_notifications import (
    format_daily_bookings_message,
    send_telegram_message,
)


class Command(BaseCommand):
    help = (
        "Надсилає в Telegram список записів " "на поточний або вказаний день."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            dest="reminder_date",
            help=(
                "Дата записів у форматі YYYY-MM-DD. "
                "Якщо не вказана, використовується "
                "поточна дата."
            ),
        )

    def get_reminder_date(self, value):
        if not value:
            return timezone.localdate()

        try:
            return datetime.strptime(
                value,
                "%Y-%m-%d",
            ).date()
        except ValueError as error:
            raise CommandError(
                "Дата повинна мати формат YYYY-MM-DD."
            ) from error

    def handle(self, *args, **options):
        reminder_date = self.get_reminder_date(options.get("reminder_date"))

        bookings = list(
            Booking.objects.filter(
                date=reminder_date,
                status__in=(
                    Booking.Status.PENDING,
                    Booking.Status.CONFIRMED,
                ),
            )
            .select_related(
                "procedure",
                "client",
                "customer",
            )
            .order_by(
                "start_time",
                "client_name",
            )
        )

        message = format_daily_bookings_message(
            bookings,
            reminder_date,
        )

        chat_id = getattr(
            settings,
            "TELEGRAM_BOOKINGS_CHAT_ID",
            "",
        )

        if not chat_id:
            self.stdout.write(
                self.style.WARNING(
                    "TELEGRAM_BOOKINGS_CHAT_ID не вказано. "
                    "Нагадування не надіслано."
                )
            )
            return

        sent = send_telegram_message(
            chat_id=chat_id,
            text=message,
        )

        formatted_date = reminder_date.strftime("%d.%m.%Y")

        if sent:
            self.stdout.write(
                self.style.SUCCESS(
                    "Telegram-нагадування на "
                    f"{formatted_date} надіслано. "
                    f"Записів: {len(bookings)}."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Не вдалося надіслати "
                    "Telegram-нагадування на "
                    f"{formatted_date}."
                )
            )
