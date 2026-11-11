from datetime import date
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

COMMAND_MODULE = (
    "appointments.management.commands." "send_daily_booking_reminder"
)


@override_settings(
    TELEGRAM_NOTIFICATIONS_ENABLED=True,
    TELEGRAM_BOOKINGS_CHAT_ID="-1001234567890",
)
class DailyBookingReminderCommandTests(SimpleTestCase):
    def create_queryset_mock(self, bookings):
        queryset = MagicMock()

        queryset.select_related.return_value = queryset
        queryset.order_by.return_value = bookings

        return queryset

    @patch(f"{COMMAND_MODULE}.send_telegram_message")
    @patch(f"{COMMAND_MODULE}." "format_daily_bookings_message")
    @patch(f"{COMMAND_MODULE}.Booking.objects.filter")
    def test_command_sends_daily_reminder(
        self,
        filter_mock,
        format_message_mock,
        send_message_mock,
    ):
        first_booking = MagicMock()
        second_booking = MagicMock()

        filter_mock.return_value = self.create_queryset_mock(
            [
                first_booking,
                second_booking,
            ]
        )

        format_message_mock.return_value = "Записи на день"
        send_message_mock.return_value = True

        output = StringIO()

        call_command(
            "send_daily_booking_reminder",
            "--date",
            "2026-09-17",
            stdout=output,
        )

        filter_mock.assert_called_once()

        filter_arguments = filter_mock.call_args.kwargs

        self.assertEqual(
            filter_arguments["date"],
            date(2026, 9, 17),
        )

        format_message_mock.assert_called_once_with(
            [
                first_booking,
                second_booking,
            ],
            date(2026, 9, 17),
        )

        send_message_mock.assert_called_once_with(
            chat_id="-1001234567890",
            text="Записи на день",
        )

        self.assertIn(
            "Записів: 2",
            output.getvalue(),
        )

    @patch(f"{COMMAND_MODULE}.send_telegram_message")
    @patch(f"{COMMAND_MODULE}." "format_daily_bookings_message")
    @patch(f"{COMMAND_MODULE}.Booking.objects.filter")
    def test_command_sends_message_without_bookings(
        self,
        filter_mock,
        format_message_mock,
        send_message_mock,
    ):
        filter_mock.return_value = self.create_queryset_mock([])

        format_message_mock.return_value = "На сьогодні записів немає."
        send_message_mock.return_value = True

        output = StringIO()

        call_command(
            "send_daily_booking_reminder",
            "--date",
            "2026-09-18",
            stdout=output,
        )

        send_message_mock.assert_called_once_with(
            chat_id="-1001234567890",
            text="На сьогодні записів немає.",
        )

        self.assertIn(
            "Записів: 0",
            output.getvalue(),
        )

    @patch(f"{COMMAND_MODULE}.send_telegram_message")
    @patch(f"{COMMAND_MODULE}." "format_daily_bookings_message")
    @patch(f"{COMMAND_MODULE}.Booking.objects.filter")
    def test_command_does_not_crash_when_sending_fails(
        self,
        filter_mock,
        format_message_mock,
        send_message_mock,
    ):
        filter_mock.return_value = self.create_queryset_mock([])

        format_message_mock.return_value = "Записи на день"
        send_message_mock.return_value = False

        output = StringIO()

        call_command(
            "send_daily_booking_reminder",
            "--date",
            "2026-09-19",
            stdout=output,
        )

        send_message_mock.assert_called_once_with(
            chat_id="-1001234567890",
            text="Записи на день",
        )

        self.assertIn(
            "Не вдалося надіслати",
            output.getvalue(),
        )

    def test_command_rejects_invalid_date(self):
        with self.assertRaisesMessage(
            CommandError,
            "Дата повинна мати формат YYYY-MM-DD.",
        ):
            call_command(
                "send_daily_booking_reminder",
                "--date",
                "19.09.2026",
            )


@override_settings(
    TELEGRAM_NOTIFICATIONS_ENABLED=True,
    TELEGRAM_BOOKINGS_CHAT_ID="",
)
class DailyBookingReminderWithoutChatTests(SimpleTestCase):
    @patch(f"{COMMAND_MODULE}.send_telegram_message")
    @patch(f"{COMMAND_MODULE}." "format_daily_bookings_message")
    @patch(f"{COMMAND_MODULE}.Booking.objects.filter")
    def test_command_skips_sending_without_chat_id(
        self,
        filter_mock,
        format_message_mock,
        send_message_mock,
    ):
        queryset = MagicMock()

        queryset.select_related.return_value = queryset
        queryset.order_by.return_value = []

        filter_mock.return_value = queryset

        format_message_mock.return_value = "Записи на день"

        output = StringIO()

        call_command(
            "send_daily_booking_reminder",
            "--date",
            "2026-09-20",
            stdout=output,
        )

        send_message_mock.assert_not_called()

        self.assertIn(
            "TELEGRAM_BOOKINGS_CHAT_ID не вказано",
            output.getvalue(),
        )
