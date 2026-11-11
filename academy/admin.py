from django.contrib import admin

from .models import Course, CourseEnrollment


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "audience",
        "training_type",
        "format",
        "duration_hours",
        "price",
        "start_date",
        "is_published",
    )
    list_filter = (
        "audience",
        "training_type",
        "format",
        "is_published",
        "start_date",
    )
    search_fields = (
        "title",
        "description",
        "location",
        "organization_details",
    )
    list_editable = (
        "price",
        "is_published",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    date_hierarchy = "start_date"
    ordering = (
        "audience",
        "start_date",
        "title",
    )

    fieldsets = (
        (
            "Основна інформація",
            {
                "fields": (
                    "title",
                    "description",
                    "image",
                )
            },
        ),
        (
            "Цільова аудиторія та формат",
            {
                "fields": (
                    "audience",
                    "training_type",
                    "format",
                    "duration_hours",
                )
            },
        ),
        (
            "Організація навчання",
            {
                "fields": (
                    "price",
                    "start_date",
                    "location",
                    "organization_details",
                )
            },
        ),
        (
            "Публікація",
            {"fields": ("is_published",)},
        ),
        (
            "Системна інформація",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "applicant_name",
        "applicant_phone",
        "course",
        "course_audience",
        "status",
        "source",
        "price_at_enrollment",
        "enrolled_at",
    )
    list_filter = (
        "status",
        "source",
        "course__audience",
        "course",
        "enrolled_at",
    )
    search_fields = (
        "applicant_name",
        "applicant_phone",
        "student__username",
        "student__first_name",
        "student__last_name",
        "student__phone_number",
        "course__title",
    )
    autocomplete_fields = (
        "student",
        "course",
    )
    readonly_fields = (
        "price_at_enrollment",
        "created_by",
        "enrolled_at",
        "updated_at",
    )
    date_hierarchy = "enrolled_at"
    ordering = ("-enrolled_at",)

    fieldsets = (
        (
            "Заявник",
            {
                "fields": (
                    "student",
                    "applicant_name",
                    "applicant_phone",
                    "applicant_comment",
                )
            },
        ),
        (
            "Курс і заявка",
            {
                "fields": (
                    "course",
                    "status",
                    "source",
                    "price_at_enrollment",
                )
            },
        ),
        (
            "Системна інформація",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_by",
                    "enrolled_at",
                    "updated_at",
                ),
            },
        ),
    )

    @admin.display(description="Для кого")
    def course_audience(self, obj):
        return obj.course.get_audience_display()

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):
        if not obj.created_by_id:
            obj.created_by = request.user

        if obj.source == CourseEnrollment.Source.ONLINE:
            obj.source = CourseEnrollment.Source.CLINIC

        super().save_model(
            request,
            obj,
            form,
            change,
        )
