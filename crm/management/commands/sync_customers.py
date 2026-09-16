from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import transaction

from academy.models import Course, CourseEnrollment
from appointments.models import Booking
from crm.models import Customer
from shop.models import Order

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Створює CRM-клієнтів із користувачів, "
        "записів, замовлень і заявок на курси."
    )

    def __init__(self):
        super().__init__()

        self.created_count = 0
        self.linked_count = 0
        self.skipped_count = 0

    def get_customer_type(
            self,
            user=None,
            professional=False,
    ):
        if professional:
            return Customer.CustomerType.COSMETOLOGIST

        if (
                user
                and getattr(user, "user_type", None)
                == "cosmetologist"
        ):
            return Customer.CustomerType.COSMETOLOGIST

        return Customer.CustomerType.CLIENT

    def get_full_name(self, user):
        full_name = user.get_full_name().strip()

        if full_name:
            return full_name

        return user.username

    def get_or_create_customer(
            self,
            *,
            full_name,
            phone_number,
            user=None,
            customer_type,
    ):
        if not phone_number:
            self.skipped_count += 1
            return None

        try:
            customer, created = (
                Customer.objects.get_or_create_by_phone(
                    full_name=full_name,
                    phone_number=phone_number,
                    user=user,
                    customer_type=customer_type,
                )
            )
        except ValidationError as error:
            self.skipped_count += 1

            self.stdout.write(
                self.style.WARNING(
                    f"Пропущено номер {phone_number}: "
                    f"{error}"
                )
            )

            return None

        if created:
            self.created_count += 1

        return customer

    def sync_users(self):
        users = User.objects.exclude(
            phone_number="",
        ).exclude(
            phone_number__isnull=True,
        )

        for user in users.iterator():
            self.get_or_create_customer(
                full_name=self.get_full_name(user),
                phone_number=user.phone_number,
                user=user,
                customer_type=self.get_customer_type(
                    user=user,
                ),
            )

    def sync_bookings(self):
        bookings = Booking.objects.select_related(
            "client",
        )

        for booking in bookings.iterator():
            user = (
                booking.client
                if booking.client_id
                else None
            )

            customer = self.get_or_create_customer(
                full_name=booking.client_name,
                phone_number=booking.client_phone,
                user=user,
                customer_type=self.get_customer_type(
                    user=user,
                ),
            )

            if (
                    customer
                    and booking.customer_id != customer.pk
            ):
                Booking.objects.filter(
                    pk=booking.pk,
                ).update(
                    customer=customer,
                )

                self.linked_count += 1

    def sync_orders(self):
        orders = Order.objects.select_related(
            "client",
            "customer",
        )

        for order in orders.iterator():
            user = (
                order.client
                if order.client_id
                else None
            )

            professional = (
                    user is not None
                    and getattr(
                user,
                "user_type",
                None,
            )
                    == "cosmetologist"
            )

            if (
                    order.customer_id
                    and order.customer.customer_type
                    == Customer.CustomerType.COSMETOLOGIST
            ):
                professional = True

            customer = self.get_or_create_customer(
                full_name=order.client_name,
                phone_number=order.client_phone,
                user=user,
                customer_type=self.get_customer_type(
                    user=user,
                    professional=professional,
                ),
            )

            if (
                    customer
                    and order.customer_id != customer.pk
            ):
                Order.objects.filter(
                    pk=order.pk,
                ).update(
                    customer=customer,
                )

                self.linked_count += 1

    def sync_course_applications(self):
        applications = (
            CourseEnrollment.objects.select_related(
                "student",
                "course",
            )
        )

        for application in applications.iterator():
            user = (
                application.student
                if application.student_id
                else None
            )

            professional_course = (
                    application.course.audience
                    == Course.Audience.COSMETOLOGISTS
            )

            customer = self.get_or_create_customer(
                full_name=application.applicant_name,
                phone_number=application.applicant_phone,
                user=user,
                customer_type=self.get_customer_type(
                    user=user,
                    professional=professional_course,
                ),
            )

            if (
                    customer
                    and application.customer_id
                    != customer.pk
            ):
                CourseEnrollment.objects.filter(
                    pk=application.pk,
                ).update(
                    customer=customer,
                )

                self.linked_count += 1

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(
            "Синхронізація клієнтів CRM..."
        )

        self.sync_users()
        self.sync_bookings()
        self.sync_orders()
        self.sync_course_applications()

        total_customers = Customer.objects.count()

        regular_clients = Customer.objects.filter(
            customer_type=Customer.CustomerType.CLIENT,
        ).count()

        cosmetologists = Customer.objects.filter(
            customer_type=(
                Customer.CustomerType.COSMETOLOGIST
            ),
        ).count()

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Синхронізацію завершено."
            )
        )

        self.stdout.write(
            f"Створено нових клієнтів: "
            f"{self.created_count}"
        )

        self.stdout.write(
            f"Прив’язано операцій: "
            f"{self.linked_count}"
        )

        self.stdout.write(
            f"Пропущено записів: "
            f"{self.skipped_count}"
        )

        self.stdout.write(
            f"Усього клієнтів CRM: "
            f"{total_customers}"
        )

        self.stdout.write(
            f"Звичайних клієнтів: "
            f"{regular_clients}"
        )

        self.stdout.write(
            f"Косметологів: "
            f"{cosmetologists}"
        )
