from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from crm.models import Customer

User = get_user_model()


class CrmAccessTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            full_name="Тестовий клієнт",
            phone_number="+380501111111",
        )

        self.regular_user = User.objects.create_user(
            username="regular-user",
            password="test-password-123",
        )

        self.staff_user = User.objects.create_user(
            username="staff-user",
            password="test-password-123",
            is_staff=True,
        )

    def test_anonymous_user_cannot_open_customer_list(
            self,
    ):
        response = self.client.get(
            reverse("crm:customer-list")
        )

        self.assertEqual(
            response.status_code,
            302,
        )
        self.assertIn(
            "/admin/login/",
            response.url,
        )

    def test_regular_user_cannot_open_customer_list(
            self,
    ):
        self.client.force_login(
            self.regular_user
        )

        response = self.client.get(
            reverse("crm:customer-list")
        )

        self.assertEqual(
            response.status_code,
            302,
        )
        self.assertIn(
            "/admin/login/",
            response.url,
        )

    def test_staff_user_can_open_customer_list(
            self,
    ):
        self.client.force_login(
            self.staff_user
        )

        response = self.client.get(
            reverse("crm:customer-list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            self.customer.full_name,
        )

    def test_staff_user_can_open_customer_detail(
            self,
    ):
        self.client.force_login(
            self.staff_user
        )

        response = self.client.get(
            reverse(
                "crm:customer-detail",
                kwargs={
                    "pk": self.customer.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            self.customer.full_name,
        )
        self.assertContains(
            response,
            self.customer.phone_number,
        )


class CustomerListTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="crm-manager",
            password="test-password-123",
            is_staff=True,
        )

        self.client_customer = Customer.objects.create(
            full_name="Марія Клієнт",
            phone_number="+380502222222",
            customer_type=(
                Customer.CustomerType.CLIENT
            ),
        )

        self.cosmetologist = Customer.objects.create(
            full_name="Олена Косметолог",
            phone_number="+380503333333",
            customer_type=(
                Customer.CustomerType.COSMETOLOGIST
            ),
        )

        self.client.force_login(
            self.staff_user
        )

    def test_customer_list_contains_all_customers(
            self,
    ):
        response = self.client.get(
            reverse("crm:customer-list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            self.client_customer.full_name,
        )
        self.assertContains(
            response,
            self.cosmetologist.full_name,
        )

    def test_search_by_customer_name(self):
        response = self.client.get(
            reverse("crm:customer-list"),
            {
                "q": "Марія",
            },
        )

        self.assertContains(
            response,
            self.client_customer.full_name,
        )
        self.assertNotContains(
            response,
            self.cosmetologist.full_name,
        )

    def test_search_by_phone_number(self):
        response = self.client.get(
            reverse("crm:customer-list"),
            {
                "q": "503333333",
            },
        )

        self.assertContains(
            response,
            self.cosmetologist.full_name,
        )
        self.assertNotContains(
            response,
            self.client_customer.full_name,
        )

    def test_filter_regular_clients(self):
        response = self.client.get(
            reverse("crm:customer-list"),
            {
                "type": "clients",
            },
        )

        self.assertContains(
            response,
            self.client_customer.full_name,
        )
        self.assertNotContains(
            response,
            self.cosmetologist.full_name,
        )

    def test_filter_cosmetologists(self):
        response = self.client.get(
            reverse("crm:customer-list"),
            {
                "type": "cosmetologists",
            },
        )

        self.assertContains(
            response,
            self.cosmetologist.full_name,
        )
        self.assertNotContains(
            response,
            self.client_customer.full_name,
        )


class CustomerManagementTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="crm-admin",
            password="test-password-123",
            is_staff=True,
        )

        self.customer = Customer.objects.create(
            full_name="Ірина Тестова",
            phone_number="+380504444444",
            customer_type=(
                Customer.CustomerType.CLIENT
            ),
            notes="Перша нотатка",
        )

        self.client.force_login(
            self.staff_user
        )

    def test_customer_create_page_opens(self):
        response = self.client.get(
            reverse("crm:customer-create")
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            "Новий клієнт",
        )

    def test_staff_user_can_create_customer(self):
        response = self.client.post(
            reverse("crm:customer-create"),
            {
                "full_name": "Новий Клієнт",
                "phone_number": "095 836 01 85",
                "customer_type": (
                    Customer.CustomerType.CLIENT
                ),
                "notes": "Новий клієнт із CRM.",
                "is_active": "on",
            },
        )

        created_customer = Customer.objects.get(
            phone_number="+380958360185",
        )

        self.assertRedirects(
            response,
            reverse(
                "crm:customer-detail",
                kwargs={
                    "pk": created_customer.pk,
                },
            ),
        )
        self.assertEqual(
            created_customer.full_name,
            "Новий Клієнт",
        )
        self.assertEqual(
            created_customer.notes,
            "Новий клієнт із CRM.",
        )
        self.assertTrue(
            created_customer.is_active
        )

    def test_duplicate_phone_number_is_rejected(
            self,
    ):
        response = self.client.post(
            reverse("crm:customer-create"),
            {
                "full_name": "Інший клієнт",
                "phone_number": (
                    self.customer.phone_number
                ),
                "customer_type": (
                    Customer.CustomerType.CLIENT
                ),
                "notes": "",
                "is_active": "on",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            Customer.objects.filter(
                phone_number=(
                    self.customer.phone_number
                ),
            ).count(),
            1,
        )
        self.assertTrue(
            response.context["form"].errors
        )

    def test_staff_user_can_update_customer(self):
        response = self.client.post(
            reverse(
                "crm:customer-update",
                kwargs={
                    "pk": self.customer.pk,
                },
            ),
            {
                "full_name": "Ірина Оновлена",
                "phone_number": (
                    self.customer.phone_number
                ),
                "customer_type": (
                    Customer.CustomerType.COSMETOLOGIST
                ),
                "notes": "Оновлена нотатка",
                "is_active": "on",
            },
        )

        self.customer.refresh_from_db()

        self.assertRedirects(
            response,
            reverse(
                "crm:customer-detail",
                kwargs={
                    "pk": self.customer.pk,
                },
            ),
        )
        self.assertEqual(
            self.customer.full_name,
            "Ірина Оновлена",
        )
        self.assertEqual(
            self.customer.customer_type,
            Customer.CustomerType.COSMETOLOGIST,
        )
        self.assertEqual(
            self.customer.notes,
            "Оновлена нотатка",
        )

    def test_staff_user_can_deactivate_customer(
            self,
    ):
        response = self.client.post(
            reverse(
                "crm:customer-toggle-active",
                kwargs={
                    "pk": self.customer.pk,
                },
            )
        )

        self.customer.refresh_from_db()

        self.assertRedirects(
            response,
            reverse(
                "crm:customer-detail",
                kwargs={
                    "pk": self.customer.pk,
                },
            ),
        )
        self.assertFalse(
            self.customer.is_active
        )

    def test_staff_user_can_activate_customer(
            self,
    ):
        self.customer.is_active = False
        self.customer.save(
            update_fields=(
                "is_active",
                "updated_at",
            )
        )

        response = self.client.post(
            reverse(
                "crm:customer-toggle-active",
                kwargs={
                    "pk": self.customer.pk,
                },
            )
        )

        self.customer.refresh_from_db()

        self.assertRedirects(
            response,
            reverse(
                "crm:customer-detail",
                kwargs={
                    "pk": self.customer.pk,
                },
            ),
        )
        self.assertTrue(
            self.customer.is_active
        )

    def test_toggle_active_requires_post(self):
        response = self.client.get(
            reverse(
                "crm:customer-toggle-active",
                kwargs={
                    "pk": self.customer.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            405,
        )
