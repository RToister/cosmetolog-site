from datetime import time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from appointments.models import Booking
from crm.models import Customer
from schedule.models import WorkingHour
from services.models import Procedure, ProcedureCategory

User = get_user_model()


class PublicPagesTests(TestCase):
    def test_public_pages_render_with_footer(self):
        for url_name in (
            "home",
            "about",
            "service-list",
            "results",
            "appointments:booking-create",
            "shop:product-list",
            "academy:course-list",
            "accounts:login",
            "accounts:register",
        ):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "site-footer")

    def test_active_navigation_item_is_marked(self):
        response = self.client.get(reverse("about"))

        self.assertContains(response, 'aria-current="page"', count=1)

    def test_anonymous_visit_does_not_create_session(self):
        self.client.get(reverse("home"))
        self.client.get(reverse("shop:product-list"))

        self.assertEqual(Session.objects.count(), 0)

    def test_invalid_shop_category_does_not_crash(self):
        response = self.client.get(
            reverse("shop:product-list"),
            {"category": "abc"},
        )

        self.assertEqual(response.status_code, 200)

    def test_custom_404_page(self):
        response = self.client.get("/missing-page/")

        self.assertEqual(response.status_code, 404)
        self.assertContains(
            response,
            "Сторінку не знайдено",
            status_code=404,
        )

    def test_login_form_uses_bootstrap_classes(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertContains(response, 'class="form-control"')


class AvailableTimesTests(TestCase):
    def setUp(self):
        category = ProcedureCategory.objects.create(name="Догляд")
        self.procedure = Procedure.objects.create(
            category=category,
            name="Чистка",
            duration_minutes=60,
            price=Decimal("1000.00"),
        )
        self.booking_date = timezone.localdate() + timedelta(days=2)

        WorkingHour.objects.create(
            day_of_week=self.booking_date.weekday(),
            start_time=time(10, 0),
            end_time=time(13, 0),
        )

        Booking.objects.create(
            procedure=self.procedure,
            client_name="Клієнт",
            client_phone="+380501111111",
            date=self.booking_date,
            start_time=time(11, 0),
        )

    def get_times(self, **extra):
        response = self.client.get(
            reverse("appointments:available-times"),
            {
                "date": self.booking_date.isoformat(),
                "procedure": self.procedure.pk,
                **extra,
            },
        )

        self.assertEqual(response.status_code, 200)

        return [
            slot["value"] for slot in response.json()["available_times"]
        ]

    def test_busy_slots_are_excluded(self):
        self.assertEqual(self.get_times(), ["10:00", "12:00"])

    def test_invalid_exclude_booking_is_ignored(self):
        self.assertEqual(
            self.get_times(exclude_booking="abc"),
            ["10:00", "12:00"],
        )


class CrmImprovementsTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="staff",
            password="test-password-123",
            is_staff=True,
        )
        self.client.force_login(self.staff_user)

        self.customer = Customer.objects.create(
            full_name="Клієнт",
            phone_number="+380501111111",
        )

    def test_toggle_active_rejects_external_next_url(self):
        response = self.client.post(
            reverse(
                "crm:customer-toggle-active",
                kwargs={"pk": self.customer.pk},
            ),
            {"next": "https://evil.example.com/"},
        )

        self.assertEqual(
            response.url,
            reverse(
                "crm:customer-detail",
                kwargs={"pk": self.customer.pk},
            ),
        )

    def test_customer_spending_counts_equal_amounts(self):
        category = ProcedureCategory.objects.create(name="Догляд")
        procedure = Procedure.objects.create(
            category=category,
            name="Чистка",
            duration_minutes=60,
            price=Decimal("500.00"),
        )
        booking_date = timezone.localdate() + timedelta(days=1)

        WorkingHour.objects.create(
            day_of_week=booking_date.weekday(),
            start_time=time(9, 0),
            end_time=time(18, 0),
        )

        for start_hour in (10, 12):
            booking = Booking.objects.create(
                procedure=procedure,
                client_name="Клієнт",
                client_phone="+380501111111",
                date=booking_date,
                start_time=time(start_hour, 0),
            )
            Booking.objects.filter(pk=booking.pk).update(
                status=Booking.Status.COMPLETED,
            )

        response = self.client.get(reverse("crm:customer-list"))

        customer = response.context["page_obj"].object_list[0]

        self.assertEqual(
            customer.appointment_spending,
            Decimal("1000.00"),
        )


class ProfileUpdateTests(TestCase):
    def test_user_can_clear_phone_number(self):
        user = User.objects.create_user(
            username="client",
            password="test-password-123",
            phone_number="+380501111111",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("accounts:profile-update"),
            {
                "first_name": "Олена",
                "last_name": "",
                "phone_number": "",
            },
        )

        self.assertRedirects(response, reverse("accounts:dashboard"))

        user.refresh_from_db()

        self.assertEqual(user.phone_number, "")
