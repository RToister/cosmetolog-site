from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings

from academy.models import Course, CourseEnrollment
from appointments.models import Booking
from crm.models import Customer
from schedule.models import WorkingHour
from services.models import Procedure
from shop.models import Order, Product

User = get_user_model()


@override_settings(DEBUG=True)
class CreateDemoDataCommandTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="demo-admin",
            email="admin@example.com",
            password="test-password-123",
        )

        self.old_user = User.objects.create_user(
            username="old-client",
            password="test-password-123",
        )

        Customer.objects.create(
            user=self.old_user,
            full_name="Старий клієнт",
            phone_number="+380999999999",
        )

    def test_command_requires_clear_flag(self):
        with self.assertRaisesMessage(
            Exception,
            "--clear",
        ):
            call_command(
                "create_demo_data",
            )

    def test_command_creates_demo_data(self):
        call_command(
            "create_demo_data",
            "--clear",
            verbosity=0,
        )

        self.assertTrue(
            User.objects.filter(
                pk=self.admin_user.pk,
                is_superuser=True,
            ).exists()
        )

        self.assertFalse(
            User.objects.filter(
                username="old-client",
            ).exists()
        )

        self.assertEqual(
            WorkingHour.objects.count(),
            7,
        )

        for working_hour in WorkingHour.objects.all():
            self.assertEqual(
                working_hour.start_time.hour,
                8,
            )
            self.assertEqual(
                working_hour.end_time.hour,
                21,
            )
            self.assertTrue(working_hour.is_active)

        self.assertEqual(
            Customer.objects.count(),
            5,
        )
        self.assertEqual(
            Procedure.objects.count(),
            5,
        )
        self.assertEqual(
            Product.objects.count(),
            5,
        )
        self.assertEqual(
            Booking.objects.count(),
            5,
        )
        self.assertEqual(
            Order.objects.count(),
            4,
        )
        self.assertEqual(
            Course.objects.count(),
            2,
        )
        self.assertEqual(
            CourseEnrollment.objects.count(),
            3,
        )

    def test_command_can_be_run_repeatedly(self):
        call_command(
            "create_demo_data",
            "--clear",
            verbosity=0,
        )

        call_command(
            "create_demo_data",
            "--clear",
            verbosity=0,
        )

        self.assertEqual(
            Customer.objects.count(),
            5,
        )
        self.assertEqual(
            Booking.objects.count(),
            5,
        )
        self.assertEqual(
            Order.objects.count(),
            4,
        )
        self.assertEqual(
            WorkingHour.objects.count(),
            7,
        )
