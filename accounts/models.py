from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class UserType(models.TextChoices):
        CLIENT = "client", "Клієнт"
        COSMETOLOGIST = "cosmetologist", "Косметолог"

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

    class Meta:
        verbose_name = "Користувач"
        verbose_name_plural = "Користувачі"

    def __str__(self):
        return self.get_full_name() or self.username
