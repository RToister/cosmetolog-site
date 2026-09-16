from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F
from django.utils import timezone


class ProductCategory(models.Model):
    name = models.CharField(
        "Назва",
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        "Опис",
        blank=True,
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Категорія товарів"
        verbose_name_plural = (
            "Категорії товарів"
        )

    def __str__(self):
        return self.name


class Product(models.Model):
    class Availability(models.TextChoices):
        PUBLIC = (
            "public",
            "Для всіх",
        )
        PROFESSIONALS_ONLY = (
            "professionals_only",
            "Лише для косметологів",
        )

    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="Категорія",
    )

    name = models.CharField(
        "Назва",
        max_length=150,
        unique=True,
    )

    sku = models.CharField(
        "Артикул SKU",
        max_length=50,
        unique=True,
    )

    description = models.TextField(
        "Опис",
        blank=True,
    )

    usage_recommendations = models.TextField(
        "Рекомендації щодо застосування",
        blank=True,
    )

    image = models.ImageField(
        "Зображення",
        upload_to="products/",
        blank=True,
    )

    retail_price = models.DecimalField(
        "Роздрібна ціна",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(
                Decimal("0.01")
            ),
        ],
    )

    professional_price = models.DecimalField(
        "Професійна ціна",
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(
                Decimal("0.01")
            ),
        ],
    )

    availability = models.CharField(
        "Доступність",
        max_length=30,
        choices=Availability.choices,
        default=Availability.PUBLIC,
    )

    stock_quantity = models.PositiveIntegerField(
        "Кількість на складі",
        default=0,
    )

    is_active = models.BooleanField(
        "Активний",
        default=True,
    )

    created_at = models.DateTimeField(
        "Створено",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        "Оновлено",
        auto_now=True,
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Товар"
        verbose_name_plural = "Товари"

    def clean(self):
        super().clean()

        if (
                self.availability
                == self.Availability.PUBLIC
                and self.retail_price is None
        ):
            raise ValidationError(
                {
                    "retail_price": (
                        "Для загальнодоступного "
                        "товару потрібно вказати "
                        "роздрібну ціну."
                    )
                }
            )

        if (
                self.availability
                == self.Availability.PUBLIC
                and self.retail_price is not None
                and self.professional_price is not None
                and self.professional_price
                >= self.retail_price
        ):
            raise ValidationError(
                {
                    "professional_price": (
                        "Професійна ціна повинна "
                        "бути нижчою за роздрібну."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()

        return super().save(
            *args,
            **kwargs,
        )

    def __str__(self):
        return self.name


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = (
            "pending",
            "Очікує обробки",
        )
        PAID = (
            "paid",
            "Оплачено",
        )
        CANCELLED = (
            "cancelled",
            "Скасовано",
        )

    class Source(models.TextChoices):
        ONLINE = (
            "online",
            "Сайт",
        )
        CLINIC = (
            "clinic",
            "Клініка",
        )
        TELEGRAM = (
            "telegram",
            "Telegram",
        )

    class PaymentMethod(models.TextChoices):
        CASH = (
            "cash",
            "Готівка",
        )
        CARD = (
            "card",
            "Картка",
        )
        BANK_TRANSFER = (
            "bank_transfer",
            "Банківський переказ",
        )

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="orders",
        verbose_name="Зареєстрований клієнт",
        null=True,
        blank=True,
    )

    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.SET_NULL,
        related_name="orders",
        verbose_name="Клієнт CRM",
        null=True,
        blank=True,
    )

    client_name = models.CharField(
        "Ім’я покупця",
        max_length=150,
    )

    client_phone = models.CharField(
        "Номер телефону",
        max_length=20,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_orders",
        verbose_name="Хто створив",
        null=True,
        blank=True,
    )

    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    source = models.CharField(
        "Джерело",
        max_length=20,
        choices=Source.choices,
        default=Source.ONLINE,
    )

    payment_method = models.CharField(
        "Спосіб оплати",
        max_length=20,
        choices=PaymentMethod.choices,
        blank=True,
    )

    total_price = models.DecimalField(
        "Загальна сума",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,
    )

    paid_at = models.DateTimeField(
        "Дата оплати",
        null=True,
        blank=True,
        editable=False,
    )

    created_at = models.DateTimeField(
        "Створено",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        "Оновлено",
        auto_now=True,
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"

    @property
    def client_is_cosmetologist(self):
        return bool(
            self.client_id
            and self.client.is_cosmetologist
        )

    @property
    def client_has_professional_access(self):
        return bool(
            self.client_id
            and self.client
            .can_buy_professional_products
        )

    def clean(self):
        super().clean()

        if not self.client_name.strip():
            raise ValidationError(
                {
                    "client_name": (
                        "Вкажіть ім’я покупця."
                    )
                }
            )

        digits = "".join(
            character
            for character in self.client_phone
            if character.isdigit()
        )

        if (
                len(digits) < 10
                or len(digits) > 15
        ):
            raise ValidationError(
                {
                    "client_phone": (
                        "Введіть коректний "
                        "номер телефону."
                    )
                }
            )

    def save(self, *args, **kwargs):
        if self.client_id:
            if not self.client_name:
                self.client_name = (
                        self.client.get_full_name()
                        or self.client.username
                )

            if not self.client_phone:
                self.client_phone = (
                    self.client.phone_number
                )

        self.full_clean()

        return super().save(
            *args,
            **kwargs,
        )

    def recalculate_total(self):
        if not self.pk:
            return

        total = sum(
            (
                item.subtotal
                for item in self.items.all()
            ),
            Decimal("0.00"),
        )

        type(self).objects.filter(
            pk=self.pk,
        ).update(
            total_price=total,
        )

        self.total_price = total

    @transaction.atomic
    def mark_as_paid(self):
        if self.status == self.Status.PAID:
            return

        if self.status == self.Status.CANCELLED:
            raise ValidationError(
                (
                    "Скасоване замовлення "
                    "не можна оплатити."
                )
            )

        if not self.payment_method:
            raise ValidationError(
                (
                    "Перед оплатою оберіть "
                    "спосіб оплати."
                )
            )

        items = list(
            self.items.select_related(
                "product"
            ).select_for_update()
        )

        if not items:
            raise ValidationError(
                (
                    "Порожнє замовлення "
                    "не можна оплатити."
                )
            )

        for item in items:
            if (
                    item.quantity
                    > item.product.stock_quantity
            ):
                raise ValidationError(
                    (
                        "Недостатньо товару "
                        f"«{item.product.name}» "
                        "на складі."
                    )
                )

        for item in items:
            Product.objects.filter(
                pk=item.product_id,
            ).update(
                stock_quantity=(
                        F("stock_quantity")
                        - item.quantity
                )
            )

        self.status = self.Status.PAID
        self.paid_at = timezone.now()

        self.save(
            update_fields=(
                "status",
                "paid_at",
                "updated_at",
            )
        )

    @transaction.atomic
    def cancel(self):
        if self.status == self.Status.CANCELLED:
            return

        if self.status == self.Status.PAID:
            for item in self.items.all():
                Product.objects.filter(
                    pk=item.product_id,
                ).update(
                    stock_quantity=(
                            F("stock_quantity")
                            + item.quantity
                    )
                )

        self.status = self.Status.CANCELLED

        self.save(
            update_fields=(
                "status",
                "updated_at",
            )
        )

    def __str__(self):
        order_number = self.pk or "нове"

        return (
            f"Замовлення №{order_number} — "
            f"{self.client_name}"
        )


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Замовлення",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="Товар",
    )

    quantity = models.PositiveIntegerField(
        "Кількість",
        default=1,
        validators=[
            MinValueValidator(1),
        ],
    )

    price_at_purchase = models.DecimalField(
        "Ціна під час покупки",
        max_digits=10,
        decimal_places=2,
        editable=False,
    )

    class Meta:
        verbose_name = "Товар у замовленні"
        verbose_name_plural = (
            "Товари в замовленні"
        )
        constraints = [
            models.UniqueConstraint(
                fields=("order", "product"),
                name="unique_product_in_order",
            ),
        ]

    @property
    def subtotal(self):
        return (
                self.price_at_purchase
                * self.quantity
        )

    def client_has_professional_access(self):
        return (
            self.order
            .client_has_professional_access
        )

    def clean(self):
        super().clean()

        if (
                not self.order_id
                or not self.product_id
        ):
            return

        has_professional_access = (
            self.client_has_professional_access()
        )

        if not self.product.is_active:
            raise ValidationError(
                {
                    "product": (
                        "Цей товар зараз "
                        "недоступний."
                    )
                }
            )

        if (
                self.product.availability
                == Product.Availability
                .PROFESSIONALS_ONLY
                and not has_professional_access
        ):
            raise ValidationError(
                {
                    "product": (
                        "Цей товар доступний лише "
                        "підтвердженим косметологам."
                    )
                }
            )

        if (
                not has_professional_access
                and self.product.retail_price is None
        ):
            raise ValidationError(
                {
                    "product": (
                        "Для цього товару не "
                        "вказана роздрібна ціна."
                    )
                }
            )

        if (
                self.quantity
                > self.product.stock_quantity
        ):
            raise ValidationError(
                {
                    "quantity": (
                        "Запитана кількість "
                        "перевищує залишок товару "
                        "на складі."
                    )
                }
            )

    def save(self, *args, **kwargs):
        if self._state.adding:
            if (
                    self.client_has_professional_access()
            ):
                self.price_at_purchase = (
                    self.product
                    .professional_price
                )
            else:
                self.price_at_purchase = (
                    self.product.retail_price
                )

        self.full_clean()

        result = super().save(
            *args,
            **kwargs,
        )

        self.order.recalculate_total()

        return result

    def delete(self, *args, **kwargs):
        order = self.order

        result = super().delete(
            *args,
            **kwargs,
        )

        order.recalculate_total()

        return result

    def __str__(self):
        return (
            f"{self.product} × "
            f"{self.quantity} "
            f"у замовленні №{self.order_id}"
        )
