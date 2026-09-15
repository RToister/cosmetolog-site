from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class UserType(models.TextChoices):
        CLIENT = "client", "Client"
        COSMETOLOGIST = "cosmetologist", "Cosmetologist"

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
    )
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.CLIENT,
    )

    def __str__(self):
        return self.get_full_name() or self.username
