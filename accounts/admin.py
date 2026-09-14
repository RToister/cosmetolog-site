from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "phone_number",
        "user_type",
        "professional_status",
        "is_staff",
    )
    list_filter = (
        "user_type",
        "professional_status",
        "is_staff",
        "is_active",
    )
    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "phone_number",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "Clinic profile",
            {
                "fields": (
                    "phone_number",
                    "birth_date",
                    "user_type",
                    "professional_status",
                    "license_number",
                    "specialization",
                )
            },
        ),
    )
