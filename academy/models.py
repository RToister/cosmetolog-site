from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Course(models.Model):
    class Format(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"
        HYBRID = "hybrid", "Hybrid"

    title = models.CharField(
        max_length=200,
        unique=True,
    )
    description = models.TextField()
    image = models.ImageField(
        upload_to="courses/",
        blank=True,
    )
    format = models.CharField(
        max_length=20,
        choices=Format.choices,
        default=Format.ONLINE,
    )
    duration_hours = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    start_date = models.DateField(
        null=True,
        blank=True,
    )
    location = models.CharField(
        max_length=255,
        blank=True,
    )
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("start_date", "title")

    def __str__(self):
        return self.title


class CourseEnrollment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class Source(models.TextChoices):
        ONLINE = "online", "Online"
        CLINIC = "clinic", "Clinic"
        TELEGRAM = "telegram", "Telegram"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="course_enrollments",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_course_enrollments",
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
    price_at_enrollment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-enrolled_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("student", "course"),
                condition=~Q(status="cancelled"),
                name="unique_active_course_enrollment",
            ),
        ]

    def clean(self):
        super().clean()

        if not self.student_id:
            return

        if self.student.user_type != "cosmetologist":
            raise ValidationError(
                {
                    "student": (
                        "Only cosmetologists can enroll "
                        "in courses."
                    )
                }
            )

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.price_at_enrollment = self.course.price

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} — {self.course}"
