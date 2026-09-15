from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F
from django.utils import timezone


class ProductCategory(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "product categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    class Availability(models.TextChoices):
        PUBLIC = "public", "Available to everyone"
        PROFESSIONALS_ONLY = (
            "professionals_only",
            "Cosmetologists only",
        )

    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField(
        max_length=150,
        unique=True,
    )
    sku = models.CharField(
        max_length=50,
        unique=True,
    )
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="products/",
        blank=True,
    )
    retail_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    professional_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    availability = models.CharField(
        max_length=30,
        choices=Availability.choices,
        default=Availability.PUBLIC,
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def clean(self):
        super().clean()

        if (
                self.availability == self.Availability.PUBLIC
                and self.retail_price is None
        ):
            raise ValidationError(
                {
                    "retail_price": (
                        "A public product must have "
                        "a retail price."
                    )
                }
            )

        if (
                self.availability == self.Availability.PUBLIC
                and self.retail_price is not None
                and self.professional_price is not None
                and self.professional_price >= self.retail_price
        ):
            raise ValidationError(
                {
                    "professional_price": (
                        "Professional price must be lower "
                        "than retail price."
                    )
                }
            )

    def __str__(self):
        return self.name


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    class Source(models.TextChoices):
        ONLINE = "online", "Online"
        CLINIC = "clinic", "Clinic"
        TELEGRAM = "telegram", "Telegram"

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Cash"
        CARD = "card", "Card"
        BANK_TRANSFER = "bank_transfer", "Bank transfer"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_orders",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.ONLINE,
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        blank=True,
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def recalculate_total(self):
        total = sum(
            (item.subtotal for item in self.items.all()),
            Decimal("0.00"),
        )

        type(self).objects.filter(pk=self.pk).update(
            total_price=total,
        )
        self.total_price = total

    @transaction.atomic
    def mark_as_paid(self):
        if self.status == self.Status.PAID:
            return

        if self.status == self.Status.CANCELLED:
            raise ValidationError(
                "A cancelled order cannot be paid."
            )

        if not self.payment_method:
            raise ValidationError(
                "Select a payment method before payment."
            )

        items = list(
            self.items.select_related("product")
            .select_for_update()
        )

        if not items:
            raise ValidationError(
                "An empty order cannot be paid."
            )

        for item in items:
            if item.quantity > item.product.stock_quantity:
                raise ValidationError(
                    (
                        f"Not enough stock for "
                        f"{item.product.name}."
                    )
                )

        for item in items:
            Product.objects.filter(
                pk=item.product_id
            ).update(
                stock_quantity=(
                        F("stock_quantity") - item.quantity
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
                    pk=item.product_id
                ).update(
                    stock_quantity=(
                            F("stock_quantity") + item.quantity
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
        return f"Order #{self.pk} — {self.client}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )
    price_at_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("order", "product"),
                name="unique_product_in_order",
            ),
        ]

    @property
    def subtotal(self):
        return self.price_at_purchase * self.quantity

    def client_is_cosmetologist(self):
        return (
                self.order.client.user_type == "cosmetologist"
        )

    def clean(self):
        super().clean()

        if not self.order_id or not self.product_id:
            return

        is_cosmetologist = self.client_is_cosmetologist()

        if (
                self.product.availability
                == Product.Availability.PROFESSIONALS_ONLY
                and not is_cosmetologist
        ):
            raise ValidationError(
                "This product is available only "
                "to cosmetologists."
            )

        if (
                not is_cosmetologist
                and self.product.retail_price is None
        ):
            raise ValidationError(
                "This product does not have a retail price."
            )

        if self.quantity > self.product.stock_quantity:
            raise ValidationError(
                {
                    "quantity": (
                        "The requested quantity exceeds "
                        "available stock."
                    )
                }
            )

    def save(self, *args, **kwargs):
        if self._state.adding:
            if self.client_is_cosmetologist():
                self.price_at_purchase = (
                    self.product.professional_price
                )
            else:
                self.price_at_purchase = (
                    self.product.retail_price
                )

        self.full_clean()
        super().save(*args, **kwargs)
        self.order.recalculate_total()

    def delete(self, *args, **kwargs):
        order = self.order
        result = super().delete(*args, **kwargs)
        order.recalculate_total()

        return result

    def __str__(self):
        return (
            f"{self.product} × {self.quantity} "
            f"in order #{self.order_id}"
        )
