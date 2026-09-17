from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from dr_toister_site.phone_numbers import (
    normalize_phone_number,
)


class User(AbstractUser):
    class UserType(models.TextChoices):
        CLIENT = "client", "Клієнт"
        COSMETOLOGIST = (
            "cosmetologist",
            "Косметолог",
        )

    phone_number = models.CharField(
        "Номер телефону",
        max_length=20,
        blank=True,
    )

    user_type = models.CharField(
        "Тип користувача",
        max_length=20,
        choices=UserType.choices,
        default=UserType.CLIENT,
    )

    is_cosmetologist_verified = models.BooleanField(
        "Косметолога підтверджено",
        default=False,
        help_text=(
            "Надає доступ до професійних цін "
            "і препаратів для спеціалістів."
        ),
    )

    cosmetologist_verified_at = models.DateTimeField(
        "Дата підтвердження косметолога",
        blank=True,
        null=True,
        editable=False,
    )

    cosmetologist_verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Хто підтвердив косметолога",
        related_name="verified_cosmetologists",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        editable=False,
    )

    class Meta:
        verbose_name = "Користувач"
        verbose_name_plural = "Користувачі"

    @property
    def is_cosmetologist(self):
        return (
                self.user_type
                == self.UserType.COSMETOLOGIST
        )

    @property
    def can_buy_professional_products(self):
        return (
                self.is_authenticated
                and self.is_cosmetologist
                and self.is_cosmetologist_verified
                and self.is_active
        )

    @property
    def cosmetologist_verification_status(self):
        if not self.is_cosmetologist:
            return "Не застосовується"

        if self.is_cosmetologist_verified:
            return "Підтверджено"

        return "Очікує підтвердження"

    def verify_cosmetologist(self, verified_by):
        if not self.is_cosmetologist:
            raise ValueError(
                "Підтвердити можна лише користувача "
                "з типом «Косметолог»."
            )

        self.is_cosmetologist_verified = True
        self.cosmetologist_verified_at = (
            timezone.now()
        )
        self.cosmetologist_verified_by = (
            verified_by
        )

        self.save(
            update_fields=[
                "is_cosmetologist_verified",
                "cosmetologist_verified_at",
                "cosmetologist_verified_by",
            ]
        )

    def revoke_cosmetologist_verification(self):
        self.is_cosmetologist_verified = False
        self.cosmetologist_verified_at = None
        self.cosmetologist_verified_by = None

        self.save(
            update_fields=[
                "is_cosmetologist_verified",
                "cosmetologist_verified_at",
                "cosmetologist_verified_by",
            ]
        )

    def clean(self):
        super().clean()

        if self.phone_number:
            self.phone_number = (
                normalize_phone_number(
                    self.phone_number
                )
            )

    def save(self, *args, **kwargs):
        if self.phone_number:
            self.phone_number = (
                normalize_phone_number(
                    self.phone_number
                )
            )

        if (
                self.user_type
                != self.UserType.COSMETOLOGIST
        ):
            self.is_cosmetologist_verified = False
            self.cosmetologist_verified_at = None
            self.cosmetologist_verified_by = None

        return super().save(*args, **kwargs)

    def __str__(self):
        return (
                self.get_full_name()
                or self.username
        )
