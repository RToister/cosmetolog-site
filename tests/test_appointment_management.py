from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from appointments.models import Booking, VisitComment
from schedule.models import WorkingHour
from services.models import Procedure, ProcedureCategory

User = get_user_model()


class AppointmentManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff_user = User.objects.create_user(
            username="appointment-manager",
            password="test-password-123",
            is_staff=True,
        )

        cls.regular_user = User.objects.create_user(
            username="regular-client",
            password="test-password-123",
        )

        cls.category = ProcedureCategory.objects.create(
            name="Тестова категорія",
            description="Категорія для тестів.",
        )

        cls.procedure = Procedure.objects.create(
            category=cls.category,
            name="Тестова процедура",
            description="Процедура для тестів.",
            duration_minutes=60,
            price=1500,
            is_active=True,
        )

    def setUp(self):
        self.booking_date = date.today() + timedelta(days=7)

        WorkingHour.objects.update_or_create(
            day_of_week=self.booking_date.weekday(),
            defaults={
                "start_time": time(8, 0),
                "end_time": time(21, 0),
                "is_active": True,
            },
        )

        self.booking = Booking.objects.create(
            client_name="Марія Тестова",
            client_phone="+380501112233",
            procedure=self.procedure,
            date=self.booking_date,
            start_time=time(10, 0),
            status=Booking.Status.PENDING,
            source=Booking.Source.ONLINE,
        )

    def test_anonymous_user_cannot_open_manage_list(
        self,
    ):
        response = self.client.get(reverse("appointments:manage-list"))

        self.assertEqual(
            response.status_code,
            302,
        )
        self.assertIn(
            "/admin/login/",
            response.url,
        )

    def test_regular_user_cannot_open_manage_list(
        self,
    ):
        self.client.force_login(self.regular_user)

        response = self.client.get(reverse("appointments:manage-list"))

        self.assertEqual(
            response.status_code,
            302,
        )
        self.assertIn(
            "/admin/login/",
            response.url,
        )

    def test_staff_user_can_open_manage_list(
        self,
    ):
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("appointments:manage-list"))

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertTemplateUsed(
            response,
            "appointments/manage_list.html",
        )
        self.assertContains(
            response,
            self.booking.client_name,
        )

    def test_staff_user_can_open_booking_detail(
        self,
    ):
        self.client.force_login(self.staff_user)

        response = self.client.get(
            reverse(
                "appointments:manage-detail",
                kwargs={
                    "pk": self.booking.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertTemplateUsed(
            response,
            "appointments/manage_detail.html",
        )
        self.assertContains(
            response,
            self.booking.client_name,
        )
        self.assertContains(
            response,
            self.procedure.name,
        )

    def test_staff_user_can_create_booking(
        self,
    ):
        self.client.force_login(self.staff_user)

        new_date = self.booking_date + timedelta(days=7)

        WorkingHour.objects.update_or_create(
            day_of_week=new_date.weekday(),
            defaults={
                "start_time": time(8, 0),
                "end_time": time(21, 0),
                "is_active": True,
            },
        )

        response = self.client.post(
            reverse("appointments:manage-create"),
            {
                "client_name": "Олена Нова",
                "client_phone": "+380502223344",
                "procedure": self.procedure.pk,
                "date": new_date.isoformat(),
                "start_time": "12:00",
                "client_note": "Створено адміністратором.",
            },
        )

        created_booking = Booking.objects.get(
            client_phone="+380502223344",
        )

        self.assertRedirects(
            response,
            reverse(
                "appointments:manage-detail",
                kwargs={
                    "pk": created_booking.pk,
                },
            ),
        )
        self.assertEqual(
            created_booking.source,
            Booking.Source.ADMIN,
        )
        self.assertEqual(
            created_booking.created_by,
            self.staff_user,
        )

    def test_staff_user_can_update_booking(
        self,
    ):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse(
                "appointments:manage-update",
                kwargs={
                    "pk": self.booking.pk,
                },
            ),
            {
                "client_name": "Марія Оновлена",
                "client_phone": self.booking.client_phone,
                "procedure": self.procedure.pk,
                "date": self.booking_date.isoformat(),
                "start_time": "13:00",
                "client_note": "Оновлений коментар.",
            },
        )

        self.booking.refresh_from_db()

        self.assertRedirects(
            response,
            reverse(
                "appointments:manage-detail",
                kwargs={
                    "pk": self.booking.pk,
                },
            ),
        )
        self.assertEqual(
            self.booking.client_name,
            "Марія Оновлена",
        )
        self.assertEqual(
            self.booking.start_time,
            time(13, 0),
        )
        self.assertEqual(
            self.booking.end_time,
            time(14, 0),
        )

    def test_staff_user_can_change_status(
        self,
    ):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse(
                "appointments:status-update",
                kwargs={
                    "pk": self.booking.pk,
                },
            ),
            {
                "status": Booking.Status.CONFIRMED,
            },
        )

        self.booking.refresh_from_db()

        self.assertRedirects(
            response,
            reverse(
                "appointments:manage-detail",
                kwargs={
                    "pk": self.booking.pk,
                },
            ),
        )
        self.assertEqual(
            self.booking.status,
            Booking.Status.CONFIRMED,
        )

    def test_invalid_status_is_rejected(self):
        self.client.force_login(self.staff_user)

        self.client.post(
            reverse(
                "appointments:status-update",
                kwargs={
                    "pk": self.booking.pk,
                },
            ),
            {
                "status": "invalid-status",
            },
        )

        self.booking.refresh_from_db()

        self.assertEqual(
            self.booking.status,
            Booking.Status.PENDING,
        )

    def test_status_update_requires_post(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(
            reverse(
                "appointments:status-update",
                kwargs={
                    "pk": self.booking.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_staff_user_can_add_visit_comment(
        self,
    ):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse(
                "appointments:comment-update",
                kwargs={
                    "pk": self.booking.pk,
                },
            ),
            {
                "comment": "Процедуру проведено успішно.",
                "recommendations": ("Використовувати SPF щодня."),
            },
        )

        comment = VisitComment.objects.get(
            booking=self.booking,
        )

        self.assertRedirects(
            response,
            reverse(
                "appointments:manage-detail",
                kwargs={
                    "pk": self.booking.pk,
                },
            ),
        )
        self.assertEqual(
            comment.author,
            self.staff_user,
        )
        self.assertEqual(
            comment.comment,
            "Процедуру проведено успішно.",
        )
        self.assertEqual(
            comment.recommendations,
            "Використовувати SPF щодня.",
        )

    def test_manage_list_filters_by_status(
        self,
    ):
        self.client.force_login(self.staff_user)

        confirmed_booking = Booking.objects.create(
            client_name="Підтверджений клієнт",
            client_phone="+380503334455",
            procedure=self.procedure,
            date=self.booking_date,
            start_time=time(15, 0),
            status=Booking.Status.CONFIRMED,
            source=Booking.Source.ADMIN,
        )

        response = self.client.get(
            reverse("appointments:manage-list"),
            {
                "status": Booking.Status.CONFIRMED,
            },
        )

        self.assertContains(
            response,
            confirmed_booking.client_name,
        )
        self.assertNotContains(
            response,
            self.booking.client_name,
        )

    def test_manage_list_searches_by_phone(
        self,
    ):
        self.client.force_login(self.staff_user)

        response = self.client.get(
            reverse("appointments:manage-list"),
            {
                "q": "501112233",
            },
        )

        self.assertContains(
            response,
            self.booking.client_name,
        )
