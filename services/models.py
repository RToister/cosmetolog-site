from django.core.validators import MinValueValidator
from django.db import models

from dr_toister_site.illustrations import procedure_illustration


class ProcedureCategory(models.Model):
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
        verbose_name = "Категорія процедур"
        verbose_name_plural = "Категорії процедур"

    def __str__(self):
        return self.name


class Procedure(models.Model):
    category = models.ForeignKey(
        ProcedureCategory,
        on_delete=models.PROTECT,
        related_name="procedures",
        verbose_name="Категорія",
    )
    name = models.CharField(
        "Назва",
        max_length=150,
        unique=True,
    )
    description = models.TextField(
        "Опис",
        blank=True,
    )
    duration_minutes = models.PositiveIntegerField(
        "Тривалість, хв",
        validators=[MinValueValidator(1)],
    )
    price = models.DecimalField(
        "Ціна",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    is_active = models.BooleanField(
        "Активна",
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
        verbose_name = "Процедура"
        verbose_name_plural = "Процедури"

    @property
    def illustration(self):
        return procedure_illustration(self)

    def __str__(self):
        return self.name
