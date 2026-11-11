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


class ProfessionalProductModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = ProductCategory.objects.create(
            name="Професійні препарати",
        )

        cls.professional_product = Product.objects.create(
            category=cls.category,
            name="Тестовий професійний препарат",
            sku="MODEL-PRO-001",
            professional_price=Decimal("1800.00"),
            availability=(Product.Availability.PROFESSIONALS_ONLY),
            stock_quantity=10,
            is_active=True,
        )

        cls.public_product = Product.objects.create(
            category=cls.category,
            name="Тестовий засіб для догляду",
            sku="MODEL-PUBLIC-001",
            retail_price=Decimal("1200.00"),
            professional_price=Decimal("900.00"),
            availability=(Product.Availability.PUBLIC),
            stock_quantity=10,
            is_active=True,
        )

        cls.unverified_cosmetologist = User.objects.create_user(
            username="model-unverified",
            phone_number="+380991120001",
            user_type=(User.UserType.COSMETOLOGIST),
            is_cosmetologist_verified=False,
        )

        cls.verified_cosmetologist = User.objects.create_user(
            username="model-verified",
            phone_number="+380991120002",
            user_type=(User.UserType.COSMETOLOGIST),
            is_cosmetologist_verified=True,
        )

    def create_order(self, user):
        return Order.objects.create(
            client=user,
            client_name=user.username,
            client_phone=user.phone_number,
            source=Order.Source.ONLINE,
        )

    def test_unverified_cosmetologist_cannot_create_professional_item(
        self,
    ):
        order = self.create_order(self.unverified_cosmetologist)

        with self.assertRaises(ValidationError):
            OrderItem.objects.create(
                order=order,
                product=(self.professional_product),
                quantity=1,
            )

        self.assertFalse(order.items.exists())

    def test_verified_cosmetologist_can_create_professional_item(
        self,
    ):
        order = self.create_order(self.verified_cosmetologist)

        item = OrderItem.objects.create(
            order=order,
            product=self.professional_product,
            quantity=1,
        )

        self.assertEqual(
            item.price_at_purchase,
            Decimal("1800.00"),
        )

        order.refresh_from_db()

        self.assertEqual(
            order.total_price,
            Decimal("1800.00"),
        )

    def test_unverified_cosmetologist_gets_retail_price_for_public_product(
        self,
    ):
        order = self.create_order(self.unverified_cosmetologist)

        item = OrderItem.objects.create(
            order=order,
            product=self.public_product,
            quantity=1,
        )

        self.assertEqual(
            item.price_at_purchase,
            Decimal("1200.00"),
        )

    def test_verified_cosmetologist_gets_professional_price_for_public_product(
        self,
    ):
        order = self.create_order(self.verified_cosmetologist)

        item = OrderItem.objects.create(
            order=order,
            product=self.public_product,
            quantity=1,
        )

        self.assertEqual(
            item.price_at_purchase,
            Decimal("900.00"),
        )
