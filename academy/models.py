from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Course(models.Model):
    class Format(models.TextChoices):
        ONLINE = "online", "Онлайн"
        OFFLINE = "offline", "Офлайн"
        HYBRID = "hybrid", "Онлайн та офлайн"

    class Audience(models.TextChoices):
        EVERYONE = "everyone", "Для всіх"
        COSMETOLOGISTS = (
            "cosmetologists",
            "Для косметологів",
        )

    class TrainingType(models.TextChoices):
        INDIVIDUAL = (
            "individual",
            "Індивідуальне",
        )
        GROUP = "group", "Групове"
        BOTH = (
            "both",
            "Індивідуальне або групове",
        )

    title = models.CharField(
        "Назва",
        max_length=200,
        unique=True,
    )
    description = models.TextField(
        "Опис",
    )
    image = models.ImageField(
        "Зображення",
        upload_to="courses/",
        blank=True,
    )
    audience = models.CharField(
        "Для кого курс",
        max_length=30,
        choices=Audience.choices,
        default=Audience.EVERYONE,
    )
    training_type = models.CharField(
        "Тип навчання",
        max_length=30,
        choices=TrainingType.choices,
        default=TrainingType.BOTH,
    )
    format = models.CharField(
        "Формат",
        max_length=20,
        choices=Format.choices,
        default=Format.ONLINE,
    )
    duration_hours = models.PositiveIntegerField(
        "Тривалість у годинах",
        validators=[
            MinValueValidator(1),
        ],
    )
    price = models.DecimalField(
        "Орієнтовна вартість",
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
        ],
    )
    start_date = models.DateField(
        "Орієнтовна дата початку",
        null=True,
        blank=True,
    )
    location = models.CharField(
        "Місце проведення",
        max_length=255,
        blank=True,
    )
    organization_details = models.TextField(
        "Деталі організації навчання",
        blank=True,
        default=(
            "Дата, час, формат, програма та остаточна "
            "вартість узгоджуються індивідуально "
            "після подання заявки."
        ),
    )
    is_published = models.BooleanField(
        "Опублікований",
        default=False,
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
        ordering = (
            "audience",
            "start_date",
            "title",
        )
        verbose_name = "Курс"
        verbose_name_plural = "Курси"

    def __str__(self):
        return self.title


class CourseEnrollment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Нова заявка"
        CONTACTED = "contacted", "Зв’язалися"
        CONFIRMED = "confirmed", "Підтверджено"
        COMPLETED = "completed", "Завершено"
        CANCELLED = "cancelled", "Скасовано"

    class Source(models.TextChoices):
        ONLINE = "online", "Сайт"
        CLINIC = "clinic", "Клініка"
        TELEGRAM = "telegram", "Telegram"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="course_enrollments",
        verbose_name="Зареєстрований користувач",
        null=True,
        blank=True,
    )
    customer = models.ForeignKey(
        "crm.Customer",
        on_delete=models.SET_NULL,
        related_name="course_applications",
        verbose_name="Клієнт CRM",
        null=True,
        blank=True,
    )
    applicant_name = models.CharField(
        "Ім’я заявника",
        max_length=150,
        blank=True,
    )
    applicant_phone = models.CharField(
        "Номер телефону",
        max_length=20,
        blank=True,
    )
    applicant_comment = models.TextField(
        "Коментар або побажання",
        blank=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="enrollments",
        verbose_name="Курс",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_course_enrollments",
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
    price_at_enrollment = models.DecimalField(
        "Вартість на момент заявки",
        max_digits=10,
        decimal_places=2,
        editable=False,
    )
    enrolled_at = models.DateTimeField(
        "Дата подання заявки",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        "Оновлено",
        auto_now=True,
    )

    class Meta:
        ordering = ("-enrolled_at",)
        verbose_name = "Заявка на курс"
        verbose_name_plural = "Заявки на курси"
        constraints = [
            models.UniqueConstraint(
                fields=("student", "course"),
                condition=(
                        Q(student__isnull=False)
                        & ~Q(status="cancelled")
                ),
                name="unique_active_course_enrollment",
            ),
        ]

    def clean(self):
        super().clean()

        if not self.applicant_name.strip():
            raise ValidationError(
                {
                    "applicant_name": (
                        "Вкажіть ім’я заявника."
                    )
                }
            )

        digits = "".join(
            character
            for character in self.applicant_phone
            if character.isdigit()
        )

        if len(digits) < 10 or len(digits) > 15:
            raise ValidationError(
                {
                    "applicant_phone": (
                        "Введіть коректний номер телефону."
                    )
                }
            )

    def save(self, *args, **kwargs):
        if self.student_id:
            if not self.applicant_name:
                self.applicant_name = (
                        self.student.get_full_name()
                        or self.student.username
                )

            if not self.applicant_phone:
                self.applicant_phone = (
                    self.student.phone_number
                )

        if self._state.adding:
            self.price_at_enrollment = (
                self.course.price
            )

        self.full_clean()

        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.applicant_name} — "
            f"{self.course.title}"
        )
