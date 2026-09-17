from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from dr_toister_site.phone_numbers import (
    normalize_phone_number,
)


class CustomerManager(models.Manager):
    def get_or_create_by_phone(
            self,
            *,
            full_name,
            phone_number,
            user=None,
            customer_type=None,
    ):
        normalized_phone = normalize_phone_number(
            phone_number
        )

        if customer_type is None:
            customer_type = (
                self.model.CustomerType.CLIENT
            )

        if (
                user
                and user.is_authenticated
                and user.user_type == "cosmetologist"
        ):
            customer_type = (
                self.model.CustomerType.COSMETOLOGIST
            )

        customer = self.filter(
            phone_number=normalized_phone,
        ).first()

        if (
                customer is None
                and user
                and user.is_authenticated
        ):
            customer = self.filter(
                user=user,
            ).first()

        if customer is None:
            customer = self.create(
                full_name=full_name,
                phone_number=normalized_phone,
                user=(
                    user
                    if (
                            user
                            and user.is_authenticated
                    )
                    else None
                ),
                customer_type=customer_type,
                last_activity_at=timezone.now(),
            )

            return customer, True

        fields_to_update = []

        if full_name and not customer.full_name:
            customer.full_name = (
                full_name.strip()
            )
            fields_to_update.append(
                "full_name"
            )

        if (
                user
                and user.is_authenticated
                and customer.user_id is None
        ):
            customer.user = user
            fields_to_update.append("user")

        if (
                customer_type
                == self.model.CustomerType.COSMETOLOGIST
                and customer.customer_type
                != self.model.CustomerType.COSMETOLOGIST
        ):
            customer.customer_type = (
                customer_type
            )
            fields_to_update.append(
                "customer_type"
            )

        customer.last_activity_at = (
            timezone.now()
        )
        fields_to_update.append(
            "last_activity_at"
        )

        customer.save(
            update_fields=fields_to_update,
        )

        return customer, False


class Customer(models.Model):
    class CustomerType(models.TextChoices):
        CLIENT = (
            "client",
            "Звичайний клієнт",
        )
        COSMETOLOGIST = (
            "cosmetologist",
            "Косметолог",
        )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="customer_profile",
        verbose_name="Обліковий запис",
        null=True,
        blank=True,
    )

    full_name = models.CharField(
        "Ім’я",
        max_length=150,
    )

    phone_number = models.CharField(
        "Номер телефону",
        max_length=20,
        unique=True,
    )

    customer_type = models.CharField(
        "Тип клієнта",
        max_length=20,
        choices=CustomerType.choices,
        default=CustomerType.CLIENT,
    )

    notes = models.TextField(
        "Внутрішні нотатки",
        blank=True,
    )

    is_active = models.BooleanField(
        "Активний",
        default=True,
    )

    first_contact_at = models.DateTimeField(
        "Перше звернення",
        auto_now_add=True,
    )

    last_activity_at = models.DateTimeField(
        "Остання активність",
        default=timezone.now,
    )

    created_at = models.DateTimeField(
        "Створено",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        "Оновлено",
        auto_now=True,
    )

    objects = CustomerManager()

    class Meta:
        ordering = (
            "-last_activity_at",
            "full_name",
        )
        verbose_name = "Клієнт CRM"
        verbose_name_plural = "Клієнти CRM"

    def clean(self):
        super().clean()

        self.full_name = (
            self.full_name.strip()
        )

        if len(self.full_name) < 2:
            raise ValidationError(
                {
                    "full_name": (
                        "Ім’я повинно містити "
                        "щонайменше 2 символи."
                    )
                }
            )

        self.phone_number = (
            normalize_phone_number(
                self.phone_number
            )
        )

        if (
                self.user_id
                and self.user.user_type
                == "cosmetologist"
        ):
            self.customer_type = (
                self.CustomerType.COSMETOLOGIST
            )

    def save(self, *args, **kwargs):
        if self.user_id:
            if not self.full_name:
                self.full_name = (
                        self.user.get_full_name()
                        or self.user.username
                )

            if (
                    not self.phone_number
                    and self.user.phone_number
            ):
                self.phone_number = (
                    self.user.phone_number
                )

        self.full_name = (
            self.full_name.strip()
        )

        self.phone_number = (
            normalize_phone_number(
                self.phone_number
            )
        )

        self.full_clean()

        return super().save(
            *args,
            **kwargs,
        )

    def touch(self):
        self.last_activity_at = (
            timezone.now()
        )

        self.save(
            update_fields=(
                "last_activity_at",
                "updated_at",
            )
        )

    def __str__(self):
        return (
            f"{self.full_name} — "
            f"{self.phone_number}"
        )
