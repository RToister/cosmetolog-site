from datetime import time

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class WorkingHour(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    day_of_week = models.PositiveSmallIntegerField(
        choices=Weekday.choices,
        unique=True,
    )
    start_time = models.TimeField(default=time(8, 0))
    end_time = models.TimeField(default=time(20, 0))
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("day_of_week",)
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=F("start_time")),
                name="working_hour_end_after_start",
            ),
        ]

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError(
                {"end_time": "End time must be later than start time."}
            )

    def __str__(self):
        return (
            f"{self.get_day_of_week_display()}: "
            f"{self.start_time:%H:%M}–{self.end_time:%H:%M}"
        )


class BlockedDate(models.Model):
    date = models.DateField(unique=True)
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("date",)

    def __str__(self):
        return str(self.date)
