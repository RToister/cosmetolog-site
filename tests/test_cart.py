from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from shop.models import (
    Order,
    Product,
    ProductCategory,
)


class ShoppingCartTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = ProductCategory.objects.create(
            name="Тестова категорія",
        )

        cls.first_product = Product.objects.create(
            category=cls.category,
            name="Крем для обличчя",
            sku="CART-001",
            description="Тестовий крем",
            retail_price=Decimal("1000.00"),
            professional_price=Decimal("800.00"),
            availability=Product.Availability.PUBLIC,
            stock_quantity=10,
            is_active=True,
        )

        cls.second_product = Product.objects.create(
            category=cls.category,
            name="Сироватка",
            sku="CART-002",
            description="Тестова сироватка",
            retail_price=Decimal("1500.00"),
            professional_price=Decimal("1200.00"),
            availability=Product.Availability.PUBLIC,
            stock_quantity=5,
            is_active=True,
        )

        cls.professional_product = Product.objects.create(
            category=cls.category,
            name="Професійний препарат",
            sku="CART-PRO-001",
            professional_price=Decimal("2000.00"),
            availability=(
                Product.Availability.PROFESSIONALS_ONLY
            ),
            stock_quantity=5,
            is_active=True,
        )

    def test_guest_can_add_product_to_cart(self):
        response = self.client.post(
            reverse(
                "shop:cart-add",
                args=[self.first_product.pk],
            ),
            {
                "quantity": 2,
            },
        )

        self.assertRedirects(
            response,
            reverse("shop:cart-detail"),
        )

        session_cart = self.client.session["cart"]

        self.assertEqual(
            session_cart[str(self.first_product.pk)][
                "quantity"
            ],
            2,
        )

    def test_guest_can_update_product_quantity(self):
        self.client.post(
            reverse(
                "shop:cart-add",
                args=[self.first_product.pk],
            ),
            {
                "quantity": 1,
            },
        )

        response = self.client.post(
            reverse(
                "shop:cart-update",
                args=[self.first_product.pk],
            ),
            {
                "quantity": 4,
            },
        )

        self.assertRedirects(
            response,
            reverse("shop:cart-detail"),
        )

        session_cart = self.client.session["cart"]

        self.assertEqual(
            session_cart[str(self.first_product.pk)][
                "quantity"
            ],
            4,
        )

    def test_guest_can_remove_product_from_cart(self):
        self.client.post(
            reverse(
                "shop:cart-add",
                args=[self.first_product.pk],
            ),
            {
                "quantity": 1,
            },
        )

        response = self.client.post(
            reverse(
                "shop:cart-remove",
                args=[self.first_product.pk],
            ),
        )

        self.assertRedirects(
            response,
            reverse("shop:cart-detail"),
        )

        session_cart = self.client.session["cart"]

        self.assertNotIn(
            str(self.first_product.pk),
            session_cart,
        )

    def test_guest_cannot_add_professional_product(self):
        response = self.client.post(
            reverse(
                "shop:cart-add",
                args=[self.professional_product.pk],
            ),
            {
                "quantity": 1,
            },
        )

        self.assertEqual(response.status_code, 404)

        session_cart = self.client.session.get(
            "cart",
            {},
        )

        self.assertNotIn(
            str(self.professional_product.pk),
            session_cart,
        )

    def test_quantity_cannot_exceed_stock(self):
        response = self.client.post(
            reverse(
                "shop:cart-add",
                args=[self.first_product.pk],
            ),
            {
                "quantity": 11,
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "shop:product-detail",
                args=[self.first_product.pk],
            ),
        )

        session_cart = self.client.session.get(
            "cart",
            {},
        )

        self.assertNotIn(
            str(self.first_product.pk),
            session_cart,
        )

    def test_cart_page_displays_added_product(self):
        self.client.post(
            reverse(
                "shop:cart-add",
                args=[self.first_product.pk],
            ),
            {
                "quantity": 2,
            },
        )

        response = self.client.get(
            reverse("shop:cart-detail")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "shop/cart_detail.html",
        )
        self.assertContains(
            response,
            self.first_product.name,
        )
        self.assertContains(
            response,
            "2000,00",
        )

    def test_guest_can_checkout_multiple_products(self):
        self.client.post(
            reverse(
                "shop:cart-add",
                args=[self.first_product.pk],
            ),
            {
                "quantity": 2,
            },
        )

        self.client.post(
            reverse(
                "shop:cart-add",
                args=[self.second_product.pk],
            ),
            {
                "quantity": 1,
            },
        )

        response = self.client.post(
            reverse("shop:checkout"),
            {
                "client_name": "Марія",
                "client_phone": "+380991112233",
            },
        )

        order = Order.objects.get()

        self.assertRedirects(
            response,
            reverse(
                "shop:order-success",
                args=[order.pk],
            ),
        )

        self.assertEqual(order.client_name, "Марія")
        self.assertEqual(
            order.client_phone,
            "+380991112233",
        )
        self.assertEqual(
            order.source,
            Order.Source.ONLINE,
        )
        self.assertEqual(
            order.items.count(),
            2,
        )

        order.refresh_from_db()

        self.assertEqual(
            order.total_price,
            Decimal("3500.00"),
        )

        self.assertEqual(
            self.client.session["cart"],
            {},
        )

    def test_empty_cart_redirects_from_checkout(self):
        response = self.client.get(
            reverse("shop:checkout")
        )

        self.assertRedirects(
            response,
            reverse("shop:product-list"),
        )

        self.assertFalse(Order.objects.exists())

    def test_order_success_is_available_after_checkout(self):
        self.client.post(
            reverse(
                "shop:cart-add",
                args=[self.first_product.pk],
            ),
            {
                "quantity": 1,
            },
        )

        self.client.post(
            reverse("shop:checkout"),
            {
                "client_name": "Олена",
                "client_phone": "+380991112244",
            },
        )

        order = Order.objects.get()

        response = self.client.get(
            reverse(
                "shop:order-success",
                args=[order.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "shop/order_success.html",
        )
        self.assertContains(
            response,
            f"№{order.pk}",
        )

    def test_other_order_success_page_is_hidden(self):
        order = Order.objects.create(
            client_name="Інший клієнт",
            client_phone="+380991112255",
            source=Order.Source.ONLINE,
        )

        response = self.client.get(
            reverse(
                "shop:order-success",
                args=[order.pk],
            )
        )

        self.assertEqual(response.status_code, 404)
