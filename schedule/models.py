from datetime import time

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class WorkingHour(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Понеділок"
        TUESDAY = 1, "Вівторок"
        WEDNESDAY = 2, "Середа"
        THURSDAY = 3, "Четвер"
        FRIDAY = 4, "П’ятниця"
        SATURDAY = 5, "Субота"
        SUNDAY = 6, "Неділя"

    day_of_week = models.PositiveSmallIntegerField(
        "День тижня",
        choices=Weekday.choices,
        unique=True,
    )
    start_time = models.TimeField(
        "Початок роботи",
        default=time(8, 0),
    )
    end_time = models.TimeField(
        "Кінець роботи",
        default=time(20, 0),
    )
    is_active = models.BooleanField(
        "Робочий день",
        default=True,
    )

    class Meta:
        ordering = ("day_of_week",)
        verbose_name = "Робочі години"
        verbose_name_plural = "Робочий графік"
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=F("start_time")),
                name="working_hour_end_after_start",
            ),
        ]

    def clean(self):
        if (
            self.start_time
            and self.end_time
            and self.start_time >= self.end_time
        ):
            raise ValidationError(
                {
                    "end_time": (
                        "Кінець роботи має бути пізніше " "за початок."
                    )
                }
            )

    def __str__(self):
        return (
            f"{self.get_day_of_week_display()}: "
            f"{self.start_time:%H:%M}–{self.end_time:%H:%M}"
        )


class BlockedDate(models.Model):
    date = models.DateField(
        "Дата",
        unique=True,
    )
    reason = models.CharField(
        "Причина",
        max_length=255,
        blank=True,
    )

    class Meta:
        ordering = ("date",)
        verbose_name = "Неробочий день"
        verbose_name_plural = "Неробочі дні"

    def __str__(self):
        return str(self.date)
