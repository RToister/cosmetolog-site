from datetime import datetime, time
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from academy.models import Course, CourseEnrollment
from appointments.models import Booking
from dr_toister_site.phone_numbers import (
    normalize_phone_number,
)
from schedule.models import WorkingHour
from services.models import (
    Procedure,
    ProcedureCategory,
)
from shop.cart import Cart
from shop.models import (
    Order,
    OrderItem,
    Product,
    ProductCategory,
)

User = get_user_model()


class PhoneNumberValidationTests(TestCase):
    def test_ukrainian_local_phone_is_normalized(self):
        self.assertEqual(
            normalize_phone_number("099 111 22 33"),
            "+380991112233",
        )

    def test_ukrainian_international_phone_is_normalized(
        self,
    ):
        self.assertEqual(
            normalize_phone_number("+38 (099) 111-22-33"),
            "+380991112233",
        )

    def test_international_prefix_is_normalized(self):
        self.assertEqual(
            normalize_phone_number("004915112345678"),
            "+4915112345678",
        )

    def test_invalid_phone_is_rejected(self):
        with self.assertRaises(ValidationError):
            normalize_phone_number("0000000000")


class BookingTimeValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = ProcedureCategory.objects.create(
            name="Тестова категорія часу",
        )

        cls.procedure = Procedure.objects.create(
            category=cls.category,
            name="Тестова процедура часу",
            description=("Перевірка минулого часу"),
            duration_minutes=60,
            price=Decimal("1000.00"),
            is_active=True,
        )

    def create_working_hours(
        self,
        fixed_datetime,
    ):
        return WorkingHour.objects.create(
            day_of_week=(fixed_datetime.date().weekday()),
            start_time=time(8, 0),
            end_time=time(21, 0),
            is_active=True,
        )

    def test_past_time_today_is_rejected(self):
        fixed_datetime = timezone.make_aware(
            datetime(
                2026,
                9,
                17,
                15,
                0,
            )
        )

        self.create_working_hours(fixed_datetime)

        booking = Booking(
            client_name="Марія",
            client_phone="+380991112233",
            procedure=self.procedure,
            date=fixed_datetime.date(),
            start_time=time(10, 0),
        )

        with patch(
            "appointments.models.timezone.localtime",
            return_value=fixed_datetime,
        ):
            with self.assertRaises(ValidationError) as error:
                booking.full_clean()

        self.assertIn(
            "start_time",
            error.exception.message_dict,
        )

    def test_future_time_today_is_allowed(self):
        fixed_datetime = timezone.make_aware(
            datetime(
                2026,
                9,
                17,
                10,
                0,
            )
        )

        self.create_working_hours(fixed_datetime)

        booking = Booking(
            client_name="Марія",
            client_phone="+380991112233",
            procedure=self.procedure,
            date=fixed_datetime.date(),
            start_time=time(12, 0),
        )

        with patch(
            "appointments.models.timezone.localtime",
            return_value=fixed_datetime,
        ):
            booking.full_clean()


class CartAccessRegressionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = ProductCategory.objects.create(
            name=("Категорія перевірки кошика"),
        )

        cls.public_product = Product.objects.create(
            category=cls.category,
            name=("Звичайний тестовий крем"),
            sku="VALIDATION-PUBLIC-001",
            retail_price=Decimal("1000.00"),
            professional_price=Decimal("800.00"),
            availability=(Product.Availability.PUBLIC),
            stock_quantity=10,
            is_active=True,
        )

        cls.professional_product = Product.objects.create(
            category=cls.category,
            name=("Закритий тестовий препарат"),
            sku="VALIDATION-PRO-001",
            professional_price=Decimal("1500.00"),
            availability=(Product.Availability.PROFESSIONALS_ONLY),
            stock_quantity=10,
            is_active=True,
        )

        cls.unverified_cosmetologist = User.objects.create_user(
            username=("cart-validation-user"),
            password="test-password-123",
            phone_number=("+380991112244"),
            user_type=(User.UserType.COSMETOLOGIST),
            is_cosmetologist_verified=False,
        )

    def create_request_with_cart(
        self,
        product,
    ):
        request = RequestFactory().get("/")

        request.user = self.unverified_cosmetologist

        session = self.client.session
        session["cart"] = {
            str(product.pk): {
                "quantity": 1,
            },
        }
        session.save()

        request.session = session

        return request

    def test_unverified_cosmetologist_gets_retail_price(
        self,
    ):
        request = self.create_request_with_cart(self.public_product)

        cart_items = list(Cart(request))

        self.assertEqual(
            len(cart_items),
            1,
        )
        self.assertEqual(
            cart_items[0]["price"],
            Decimal("1000.00"),
        )

    def test_professional_product_is_removed_without_access(
        self,
    ):
        request = self.create_request_with_cart(self.professional_product)

        cart_items = list(Cart(request))

        self.assertEqual(
            cart_items,
            [],
        )
        self.assertNotIn(
            str(self.professional_product.pk),
            request.session["cart"],
        )


class GuestCourseDuplicateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.course = Course.objects.create(
            title=("Тестова програма дублікатів"),
            description=("Перевірка повторних заявок"),
            audience=(Course.Audience.EVERYONE),
            training_type=(Course.TrainingType.GROUP),
            format=Course.Format.ONLINE,
            duration_hours=2,
            price=Decimal("1200.00"),
            is_published=True,
        )

    def test_guest_cannot_create_duplicate_by_phone(
        self,
    ):
        course_url = reverse(
            "academy:course-detail",
            args=[self.course.pk],
        )

        self.client.post(
            course_url,
            {
                "applicant_name": "Марія",
                "applicant_phone": ("099 111 22 33"),
                "applicant_comment": "",
            },
        )

        second_response = self.client.post(
            course_url,
            {
                "applicant_name": "Марія",
                "applicant_phone": ("+380991112233"),
                "applicant_comment": "",
            },
        )

        self.assertEqual(
            CourseEnrollment.objects.filter(
                course=self.course,
            ).count(),
            1,
        )

        application = CourseEnrollment.objects.get(
            course=self.course,
        )

        self.assertRedirects(
            second_response,
            reverse(
                "academy:application-success",
                args=[application.pk],
            ),
        )


class OrderStockRegressionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = ProductCategory.objects.create(
            name=("Категорія перевірки складу"),
        )

        cls.product = Product.objects.create(
            category=cls.category,
            name="Товар перевірки складу",
            sku="STOCK-REGRESSION-001",
            retail_price=Decimal("1000.00"),
            professional_price=Decimal("800.00"),
            availability=(Product.Availability.PUBLIC),
            stock_quantity=5,
            is_active=True,
        )

    def create_order(self):
        order = Order.objects.create(
            client_name="Олена",
            client_phone="+380991112255",
            payment_method=(Order.PaymentMethod.CARD),
            source=Order.Source.ONLINE,
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
        )

        return order

    def test_repeated_payment_does_not_decrease_stock_twice(
        self,
    ):
        order = self.create_order()

        order.mark_as_paid()
        order.mark_as_paid()

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock_quantity,
            3,
        )

    def test_repeated_cancellation_does_not_restore_stock_twice(
        self,
    ):
        order = self.create_order()

        order.mark_as_paid()
        order.cancel()
        order.cancel()

        self.product.refresh_from_db()

        self.assertEqual(
            self.product.stock_quantity,
            5,
        )
