from django.core.validators import MinValueValidator
from django.db import models


class ProcedureCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "procedure categories"

    def __str__(self):
        return self.name


class Procedure(models.Model):
    category = models.ForeignKey(
        ProcedureCategory,
        on_delete=models.PROTECT,
        related_name="procedures",
    )
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name
