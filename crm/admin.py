from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "phone_number",
        "customer_type",
        "has_account",
        "is_active",
        "first_contact_at",
        "last_activity_at",
    )
    list_filter = (
        "customer_type",
        "is_active",
        "first_contact_at",
        "last_activity_at",
    )
    search_fields = (
        "full_name",
        "phone_number",
        "user__username",
        "user__first_name",
        "user__last_name",
    )
    autocomplete_fields = ("user",)
    readonly_fields = (
        "first_contact_at",
        "last_activity_at",
        "created_at",
        "updated_at",
    )
    list_editable = (
        "customer_type",
        "is_active",
    )
    date_hierarchy = "first_contact_at"
    ordering = ("-last_activity_at",)

    fieldsets = (
        (
            "Клієнт",
            {
                "fields": (
                    "user",
                    "full_name",
                    "phone_number",
                    "customer_type",
                    "is_active",
                )
            },
        ),
        (
            "Нотатки лікаря",
            {"fields": ("notes",)},
        ),
        (
            "Системна інформація",
            {
                "classes": ("collapse",),
                "fields": (
                    "first_contact_at",
                    "last_activity_at",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    @admin.display(
        description="Є акаунт",
        boolean=True,
    )
    def has_account(self, obj):
        return obj.user_id is not None
