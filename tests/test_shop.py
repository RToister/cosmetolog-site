from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from shop.models import (
    Order,
    OrderItem,
    Product,
    ProductCategory,
)

User = get_user_model()


class ShopModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = ProductCategory.objects.create(
            name="Домашній догляд",
            description=("Засоби для домашнього догляду"),
        )

        cls.public_product = Product.objects.create(
            category=cls.category,
            name="Зволожувальний крем",
            sku="CREAM-001",
            description=("Крем для щоденного догляду"),
            retail_price=Decimal("1000.00"),
            professional_price=Decimal("800.00"),
            availability=(Product.Availability.PUBLIC),
            stock_quantity=10,
            is_active=True,
        )

        cls.professional_product = Product.objects.create(
            category=cls.category,
            name="Професійний препарат",
            sku="PRO-001",
            description=("Препарат лише для косметологів"),
            retail_price=None,
            professional_price=Decimal("1500.00"),
            availability=(Product.Availability.PROFESSIONALS_ONLY),
            stock_quantity=5,
            is_active=True,
        )

    def create_guest_order(
        self,
        **extra_fields,
    ):
        order_data = {
            "client_name": "Марія",
            "client_phone": "+380991112233",
            "source": Order.Source.ONLINE,
        }

        order_data.update(extra_fields)

        return Order.objects.create(**order_data)

    def test_guest_receives_retail_price(self):
        order = self.create_guest_order()

        item = OrderItem.objects.create(
            order=order,
            product=self.public_product,
            quantity=2,
        )

        self.assertEqual(
            item.price_at_purchase,
            Decimal("1000.00"),
        )

        self.assertEqual(
            item.subtotal,
            Decimal("2000.00"),
        )

        order.refresh_from_db()

        self.assertEqual(
            order.total_price,
            Decimal("2000.00"),
        )

    def test_cosmetologist_receives_professional_price(
        self,
    ):
        cosmetologist = User.objects.create_user(
            username="cosmetologist",
            password="test-password-123",
            first_name="Анна",
            phone_number="+380991112244",
            user_type=(User.UserType.COSMETOLOGIST),
            is_cosmetologist_verified=True,
        )

        order = self.create_guest_order(
            client=cosmetologist,
            client_name="Анна",
            client_phone="+380991112244",
        )

        item = OrderItem.objects.create(
            order=order,
            product=self.public_product,
            quantity=1,
        )

        self.assertEqual(
            item.price_at_purchase,
            Decimal("800.00"),
        )

        order.refresh_from_db()

        self.assertEqual(
            order.total_price,
            Decimal("800.00"),
        )

    def test_unverified_cosmetologist_receives_retail_price(
        self,
    ):
        cosmetologist = User.objects.create_user(
            username="unverified-shop-user",
            password="test-password-123",
            first_name="Ірина",
            phone_number="+380991112245",
            user_type=(User.UserType.COSMETOLOGIST),
            is_cosmetologist_verified=False,
        )

        order = self.create_guest_order(
            client=cosmetologist,
            client_name="Ірина",
            client_phone="+380991112245",
        )

        item = OrderItem.objects.create(
            order=order,
            product=self.public_product,
            quantity=1,
        )

        self.assertEqual(
            item.price_at_purchase,
            Decimal("1000.00"),
        )

    def test_guest_cannot_buy_professional_product(
        self,
    ):
        order = self.create_guest_order()

        with self.assertRaises(ValidationError):
            OrderItem.objects.create(
                order=order,
                product=(self.professional_product),
                quantity=1,
            )

        self.assertFalse(
            OrderItem.objects.filter(
                order=order,
                product=(self.professional_product),
            ).exists()
        )

    def test_unverified_cosmetologist_cannot_buy_professional_product(
        self,
    ):
        cosmetologist = User.objects.create_user(
            username="unverified-professional",
            password="test-password-123",
            first_name="Марина",
            phone_number="+380991112254",
            user_type=(User.UserType.COSMETOLOGIST),
            is_cosmetologist_verified=False,
        )

        order = self.create_guest_order(
            client=cosmetologist,
            client_name="Марина",
            client_phone="+380991112254",
        )

        with self.assertRaises(ValidationError):
            OrderItem.objects.create(
                order=order,
                product=(self.professional_product),
                quantity=1,
            )

        self.assertFalse(order.items.exists())

    def test_cosmetologist_can_buy_professional_product(
        self,
    ):
        cosmetologist = User.objects.create_user(
            username="professional",
            password="test-password-123",
            first_name="Олена",
            phone_number="+380991112255",
            user_type=(User.UserType.COSMETOLOGIST),
            is_cosmetologist_verified=True,
        )

        order = self.create_guest_order(
            client=cosmetologist,
            client_name="Олена",
            client_phone="+380991112255",
        )

        item = OrderItem.objects.create(
            order=order,
            product=self.professional_product,
            quantity=1,
        )

        self.assertEqual(
            item.price_at_purchase,
            Decimal("1500.00"),
        )

    def test_payment_decreases_stock_quantity(self):
        order = self.create_guest_order(
            payment_method=(Order.PaymentMethod.CARD),
        )

        OrderItem.objects.create(
            order=order,
            product=self.public_product,
            quantity=3,
        )

        order.mark_as_paid()

        order.refresh_from_db()
        self.public_product.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.PAID,
        )

        self.assertIsNotNone(order.paid_at)

        self.assertEqual(
            self.public_product.stock_quantity,
            7,
        )

    def test_cancelling_paid_order_restores_stock(
        self,
    ):
        order = self.create_guest_order(
            payment_method=(Order.PaymentMethod.CASH),
        )

        OrderItem.objects.create(
            order=order,
            product=self.public_product,
            quantity=3,
        )

        order.mark_as_paid()
        order.cancel()

        order.refresh_from_db()
        self.public_product.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.CANCELLED,
        )

        self.assertEqual(
            self.public_product.stock_quantity,
            10,
        )

    def test_empty_order_cannot_be_paid(self):
        order = self.create_guest_order(
            payment_method=(Order.PaymentMethod.CARD),
        )

        with self.assertRaises(ValidationError):
            order.mark_as_paid()

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.PENDING,
        )

    def test_order_without_payment_method_cannot_be_paid(
        self,
    ):
        order = self.create_guest_order()

        OrderItem.objects.create(
            order=order,
            product=self.public_product,
            quantity=1,
        )

        with self.assertRaises(ValidationError):
            order.mark_as_paid()

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            Order.Status.PENDING,
        )

    def test_order_cannot_exceed_available_stock(
        self,
    ):
        order = self.create_guest_order()

        with self.assertRaises(ValidationError):
            OrderItem.objects.create(
                order=order,
                product=self.public_product,
                quantity=11,
            )

    def test_cancelled_order_cannot_be_paid(self):
        order = self.create_guest_order(
            payment_method=(Order.PaymentMethod.CARD),
        )

        OrderItem.objects.create(
            order=order,
            product=self.public_product,
            quantity=1,
        )

        order.cancel()

        with self.assertRaises(ValidationError):
            order.mark_as_paid()
