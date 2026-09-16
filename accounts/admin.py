from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    actions = (
        "verify_cosmetologists",
        "revoke_cosmetologist_verification",
    )

    list_display = (
        "username",
        "first_name",
        "last_name",
        "phone_number",
        "user_type",
        "verification_status",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "user_type",
        "is_cosmetologist_verified",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "phone_number",
    )

    readonly_fields = (
        "is_cosmetologist_verified",
        "cosmetologist_verified_at",
        "cosmetologist_verified_by",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "Профіль",
            {
                "fields": (
                    "phone_number",
                    "user_type",
                )
            },
        ),
        (
            "Підтвердження косметолога",
            {
                "fields": (
                    "is_cosmetologist_verified",
                    "cosmetologist_verified_at",
                    "cosmetologist_verified_by",
                ),
                "description": (
                    "Підтвердження та його скасування "
                    "виконується через дії у списку "
                    "користувачів."
                ),
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Профіль",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone_number",
                    "user_type",
                )
            },
        ),
    )

    @admin.display(
        description="Статус косметолога",
        ordering="is_cosmetologist_verified",
    )
    def verification_status(self, user):
        if not user.is_cosmetologist:
            return "—"

        if user.is_cosmetologist_verified:
            return "Підтверджено"

        return "Очікує підтвердження"

    @admin.action(
        description=(
                "Підтвердити вибраних косметологів"
        )
    )
    def verify_cosmetologists(
            self,
            request,
            queryset,
    ):
        cosmetologists = queryset.filter(
            user_type=User.UserType.COSMETOLOGIST,
            is_cosmetologist_verified=False,
        )

        verified_count = 0

        for user in cosmetologists:
            user.verify_cosmetologist(
                verified_by=request.user,
            )
            verified_count += 1

        skipped_count = (
                queryset.count() - verified_count
        )

        if verified_count:
            self.message_user(
                request,
                (
                    "Підтверджено косметологів: "
                    f"{verified_count}."
                ),
                level=messages.SUCCESS,
            )

        if skipped_count:
            self.message_user(
                request,
                (
                    "Пропущено користувачів: "
                    f"{skipped_count}. Вони не є "
                    "косметологами або вже підтверджені."
                ),
                level=messages.WARNING,
            )

    @admin.action(
        description=(
                "Скасувати підтвердження косметологів"
        )
    )
    def revoke_cosmetologist_verification(
            self,
            request,
            queryset,
    ):
        verified_cosmetologists = queryset.filter(
            user_type=User.UserType.COSMETOLOGIST,
            is_cosmetologist_verified=True,
        )

        revoked_count = 0

        for user in verified_cosmetologists:
            user.revoke_cosmetologist_verification()
            revoked_count += 1

        skipped_count = (
                queryset.count() - revoked_count
        )

        if revoked_count:
            self.message_user(
                request,
                (
                    "Скасовано підтверджень: "
                    f"{revoked_count}."
                ),
                level=messages.SUCCESS,
            )

        if skipped_count:
            self.message_user(
                request,
                (
                    "Пропущено користувачів: "
                    f"{skipped_count}. Вони не мають "
                    "активного підтвердження."
                ),
                level=messages.WARNING,
            )
