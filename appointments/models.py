from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from dr_toister_site.phone_numbers import (
    normalize_phone_number,
)
from schedule.models import (
    BlockedDate,
    WorkingHour,
)
from services.models import Procedure


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = (
            "pending",
            "Очікує підтвердження",
        )
        CONFIRMED = (
            "confirmed",
            "Підтверджено",
        )
        COMPLETED = (
            "completed",
            "Завершено",
        )
        CANCELLED = (
            "cancelled",
            "Скасовано",
        )

    class Source(models.TextChoices):
        ONLINE = "online", "Сайт"
        ADMIN = (
            "admin",
            "Адміністратор",
        )
        TELEGRAM = (
            "telegram",
            "Telegram",
        )

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="bookings",
        null=True,
        blank=True,
        verbose_name=(
            "Обліковий запис клієнта"
        ),
    )

    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.SET_NULL,
        related_name="bookings",
        null=True,
        blank=True,
        verbose_name="Клієнт CRM",
    )

    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.PROTECT,
        related_name="bookings",
        verbose_name="Процедура",
    )

    client_name = models.CharField(
        max_length=150,
        verbose_name="Ім’я клієнта",
    )

    client_phone = models.CharField(
        max_length=30,
        verbose_name="Номер телефону",
    )

    date = models.DateField(
        verbose_name="Дата",
    )

    start_time = models.TimeField(
        verbose_name="Час початку",
    )

    end_time = models.TimeField(
        editable=False,
        verbose_name="Час завершення",
    )

    price_at_booking = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,
        verbose_name="Ціна під час запису",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Статус",
    )

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.ONLINE,
        verbose_name="Джерело",
    )

    client_note = models.TextField(
        blank=True,
        verbose_name="Коментар клієнта",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_bookings",
        null=True,
        blank=True,
        verbose_name="Хто створив запис",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Створено",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Оновлено",
    )

    class Meta:
        ordering = (
            "-date",
            "-start_time",
        )
        verbose_name = "Запис"
        verbose_name_plural = "Записи"
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "date",
                    "start_time",
                ),
                condition=~models.Q(
                    status="cancelled"
                ),
                name=(
                    "unique_active_booking_start"
                ),
            ),
        ]

    def calculate_end_time(self):
        if (
                not self.date
                or not self.start_time
                or not self.procedure_id
        ):
            return None

        start_datetime = datetime.combine(
            self.date,
            self.start_time,
        )

        end_datetime = (
                start_datetime
                + timedelta(
            minutes=(
                self.procedure
                .duration_minutes
            ),
        )
        )

        return end_datetime.time()

    def clean(self):
        super().clean()

        self.client_name = (
            self.client_name.strip()
        )

        if len(self.client_name) < 2:
            raise ValidationError(
                {
                    "client_name": (
                        "Ім’я повинно містити "
                        "щонайменше 2 символи."
                    )
                }
            )

        self.client_phone = (
            normalize_phone_number(
                self.client_phone
            )
        )

        if (
                not self.date
                or not self.start_time
                or not self.procedure_id
        ):
            return

        calculated_end_time = (
            self.calculate_end_time()
        )

        if calculated_end_time is None:
            return

        self.end_time = calculated_end_time

        current_datetime = (
            timezone.localtime()
        )
        current_date = (
            current_datetime.date()
        )
        current_time = (
            current_datetime.time()
            .replace(
                tzinfo=None,
            )
        )

        if self.date < current_date:
            raise ValidationError(
                {
                    "date": (
                        "Неможливо створити запис "
                        "на минулу дату."
                    )
                }
            )

        if (
                self.date == current_date
                and self.start_time <= current_time
        ):
            raise ValidationError(
                {
                    "start_time": (
                        "Неможливо створити запис "
                        "на час, який уже минув."
                    )
                }
            )

        if BlockedDate.objects.filter(
                date=self.date,
        ).exists():
            raise ValidationError(
                {
                    "date": (
                        "Обраний день недоступний "
                        "для запису."
                    )
                }
            )

        try:
            working_hours = (
                WorkingHour.objects.get(
                    day_of_week=(
                        self.date.weekday()
                    ),
                    is_active=True,
                )
            )
        except WorkingHour.DoesNotExist:
            raise ValidationError(
                {
                    "date": (
                        "У цей день лікар "
                        "не працює."
                    )
                }
            )

        if (
                self.start_time
                < working_hours.start_time
                or calculated_end_time
                > working_hours.end_time
        ):
            raise ValidationError(
                {
                    "start_time": (
                        "Час запису виходить "
                        "за межі робочого графіка."
                    )
                }
            )

        overlapping_bookings = (
            Booking.objects.filter(
                date=self.date,
                start_time__lt=(
                    calculated_end_time
                ),
                end_time__gt=(
                    self.start_time
                ),
            )
            .exclude(
                status=self.Status.CANCELLED,
            )
        )

        if self.pk:
            overlapping_bookings = (
                overlapping_bookings.exclude(
                    pk=self.pk
                )
            )

        if overlapping_bookings.exists():
            raise ValidationError(
                {
                    "start_time": (
                        "Обраний час перетинається "
                        "з іншим записом."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.client_name = (
            self.client_name.strip()
        )

        self.client_phone = (
            normalize_phone_number(
                self.client_phone
            )
        )

        calculated_end_time = (
            self.calculate_end_time()
        )

        if calculated_end_time is not None:
            self.end_time = (
                calculated_end_time
            )

        if (
                self._state.adding
                and self.procedure_id
                and self.price_at_booking
                == Decimal("0.00")
        ):
            self.price_at_booking = (
                self.procedure.price
            )

        self.full_clean()

        return super().save(
            *args,
            **kwargs,
        )

    def __str__(self):
        return (
            f"{self.client_name} — "
            f"{self.procedure} — "
            f"{self.date:%d.%m.%Y} "
            f"{self.start_time:%H:%M}"
        )


class VisitComment(models.Model):
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="visit_comment",
        verbose_name="Запис",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name=(
            "authored_visit_comments"
        ),
        null=True,
        blank=True,
        verbose_name="Автор",
    )

    comment = models.TextField(
        verbose_name="Коментар лікаря",
    )

    recommendations = models.TextField(
        blank=True,
        verbose_name="Рекомендації",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Створено",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Оновлено",
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = (
            "Коментар до візиту"
        )
        verbose_name_plural = (
            "Коментарі до візитів"
        )

    def __str__(self):
        return (
            f"Коментар до запису "
            f"#{self.booking_id} — "
            f"{self.booking.client_name}"
        )
