from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from schedule.models import BlockedDate, WorkingHour
from services.models import Procedure


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class Source(models.TextChoices):
        ONLINE = "online", "Online"
        CLINIC = "clinic", "Clinic"
        TELEGRAM = "telegram", "Telegram"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="bookings",
        null=True,
        blank=True,
    )
    client_name = models.CharField(
        max_length=150,
        blank=True,
    )
    client_phone = models.CharField(
        max_length=20,
        blank=True,
    )
    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_bookings",
        null=True,
        blank=True,
    )

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(editable=False)

    price_at_booking = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
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

    client_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-date", "-start_time")
        constraints = [
            models.UniqueConstraint(
                fields=("date", "start_time"),
                condition=~Q(status="cancelled"),
                name="unique_active_booking_start",
            ),
        ]

    def calculate_end_time(self):
        start_datetime = datetime.combine(
            self.date,
            self.start_time,
        )
        end_datetime = start_datetime + timedelta(
            minutes=self.procedure.duration_minutes
        )

        return end_datetime.time()

    def clean(self):
        super().clean()

        errors = {}

        if not self.client_id and not self.client_name:
            errors["client_name"] = "Enter the client name."

        if not self.client_id and not self.client_phone:
            errors["client_phone"] = "Enter the phone number."

        if errors:
            raise ValidationError(errors)

        if not self.procedure_id or not self.date or not self.start_time:
            return

        calculated_end_time = self.calculate_end_time()
        self.end_time = calculated_end_time

        if BlockedDate.objects.filter(date=self.date).exists():
            raise ValidationError(
                {
                    "date": (
                        "The clinic is unavailable on this date."
                    )
                }
            )

        working_hour = WorkingHour.objects.filter(
            day_of_week=self.date.weekday(),
            is_active=True,
        ).first()

        if working_hour is None:
            raise ValidationError(
                {
                    "date": (
                        "The clinic does not work on this day."
                    )
                }
            )

        if (
                self.start_time < working_hour.start_time
                or calculated_end_time > working_hour.end_time
        ):
            raise ValidationError(
                {
                    "start_time": (
                        "The appointment must fit within "
                        "clinic working hours."
                    )
                }
            )

        if self.status != self.Status.CANCELLED:
            overlapping_bookings = Booking.objects.filter(
                date=self.date,
                start_time__lt=calculated_end_time,
                end_time__gt=self.start_time,
            ).exclude(
                status=self.Status.CANCELLED,
            ).exclude(
                pk=self.pk,
            )

            if overlapping_bookings.exists():
                raise ValidationError(
                    {
                        "start_time": (
                            "This time overlaps another "
                            "appointment."
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
                self.client_phone = self.client.phone_number

        if self._state.adding:
            self.price_at_booking = self.procedure.price

        self.end_time = self.calculate_end_time()
        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.client_name} — {self.procedure} — "
            f"{self.date} {self.start_time:%H:%M}"
        )


class VisitComment(models.Model):
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="visit_comment",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="visit_comments",
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Comment for booking #{self.booking_id}"
