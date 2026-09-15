from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "first_name",
        "phone_number",
        "user_type",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "user_type",
        "is_staff",
        "is_active",
    )
    search_fields = (
        "username",
        "first_name",
        "last_name",
        "phone_number",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "Профіль",
            {
                "fields": (
                    "phone_number",
                    "birth_date",
                    "user_type",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Профіль",
            {
                "fields": (
                    "first_name",
                    "phone_number",
                    "birth_date",
                    "user_type",
                )
            },
        ),
    )
