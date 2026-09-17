from datetime import date, time, timedelta

from django.test import TestCase
from django.urls import reverse

from appointments.models import Booking
from schedule.models import BlockedDate, WorkingHour
from services.models import Procedure, ProcedureCategory


class AppointmentViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = ProcedureCategory.objects.create(
            name="Ін’єкційна косметологія",
            description="Тестова категорія",
        )

        cls.procedure = Procedure.objects.create(
            category=cls.category,
            name="Ботулінотерапія",
            description="Тестова процедура",
            duration_minutes=60,
            price=2500,
            is_active=True,
        )

    def get_future_date(self, weekday=0):
        booking_date = date.today() + timedelta(days=1)

        while booking_date.weekday() != weekday:
            booking_date += timedelta(days=1)

        return booking_date

    def create_working_hours(self, booking_date):
        return WorkingHour.objects.create(
            day_of_week=booking_date.weekday(),
            start_time=time(8, 0),
            end_time=time(20, 0),
            is_active=True,
        )

    def test_booking_page_is_available(self):
        response = self.client.get(reverse("appointments:booking-create"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "appointments/booking_form.html",
        )

    def test_booking_success_page_is_available(self):
        response = self.client.get(reverse("appointments:booking-success"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "appointments/booking_success.html",
        )

    def test_guest_can_create_booking(self):
        booking_date = self.get_future_date()
        self.create_working_hours(booking_date)

        response = self.client.post(
            reverse("appointments:booking-create"),
            {
                "client_name": "Марія",
                "client_phone": "+380991112233",
                "procedure": self.procedure.pk,
                "date": booking_date.isoformat(),
                "start_time": "10:00",
                "client_note": "Перший візит",
            },
        )

        self.assertRedirects(
            response,
            reverse("appointments:booking-success"),
        )

        self.assertEqual(Booking.objects.count(), 1)

        booking = Booking.objects.get()

        self.assertEqual(booking.client_name, "Марія")
        self.assertEqual(
            booking.client_phone,
            "+380991112233",
        )
        self.assertEqual(
            booking.procedure,
            self.procedure,
        )
        self.assertEqual(
            booking.source,
            Booking.Source.ONLINE,
        )
        self.assertIsNone(booking.client)

    def test_available_times_returns_slots(self):
        booking_date = self.get_future_date()
        self.create_working_hours(booking_date)

        response = self.client.get(
            reverse("appointments:available-times"),
            {
                "procedure": self.procedure.pk,
                "date": booking_date.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        available_values = [
            slot["value"] for slot in response_data["available_times"]
        ]

        self.assertIn("08:00", available_values)
        self.assertIn("10:00", available_values)
        self.assertEqual(response_data["error"], "")

    def test_occupied_time_is_not_available(self):
        booking_date = self.get_future_date()
        self.create_working_hours(booking_date)

        Booking.objects.create(
            client_name="Ірина",
            client_phone="+380991234567",
            procedure=self.procedure,
            date=booking_date,
            start_time=time(10, 0),
        )

        response = self.client.get(
            reverse("appointments:available-times"),
            {
                "procedure": self.procedure.pk,
                "date": booking_date.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        available_values = [
            slot["value"] for slot in response_data["available_times"]
        ]

        self.assertNotIn("09:30", available_values)
        self.assertNotIn("10:00", available_values)
        self.assertNotIn("10:30", available_values)
        self.assertIn("11:00", available_values)

    def test_blocked_date_has_no_available_times(self):
        booking_date = self.get_future_date()
        self.create_working_hours(booking_date)

        BlockedDate.objects.create(
            date=booking_date,
            reason="Вихідний",
        )

        response = self.client.get(
            reverse("appointments:available-times"),
            {
                "procedure": self.procedure.pk,
                "date": booking_date.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        self.assertEqual(
            response_data["available_times"],
            [],
        )
        self.assertEqual(
            response_data["error"],
            "Обраний день недоступний для запису.",
        )

    def test_non_working_day_has_no_available_times(self):
        booking_date = self.get_future_date()

        response = self.client.get(
            reverse("appointments:available-times"),
            {
                "procedure": self.procedure.pk,
                "date": booking_date.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        self.assertEqual(
            response_data["available_times"],
            [],
        )
        self.assertEqual(
            response_data["error"],
            "У цей день лікар не працює.",
        )

    def test_past_date_is_rejected(self):
        past_date = date.today() - timedelta(days=1)

        response = self.client.get(
            reverse("appointments:available-times"),
            {
                "procedure": self.procedure.pk,
                "date": past_date.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)

        response_data = response.json()

        self.assertEqual(
            response_data["available_times"],
            [],
        )
        self.assertEqual(
            response_data["error"],
            "Неможливо записатися на минулу дату.",
        )

    def test_invalid_phone_does_not_create_booking(self):
        booking_date = self.get_future_date()
        self.create_working_hours(booking_date)

        response = self.client.post(
            reverse("appointments:booking-create"),
            {
                "client_name": "Марія",
                "client_phone": "invalid-phone",
                "procedure": self.procedure.pk,
                "date": booking_date.isoformat(),
                "start_time": "10:00",
                "client_note": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Booking.objects.exists())

        phone_errors = response.context["form"].errors["client_phone"]

        self.assertIn(
            (
                "Введіть коректний номер телефону "
                "з кодом країни, наприклад "
                "+380991112233 або +4915112345678."
            ),
            phone_errors,
        )
