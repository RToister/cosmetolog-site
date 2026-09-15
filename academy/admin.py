from django.contrib import admin

from .models import Course, CourseEnrollment


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "format",
        "duration_hours",
        "price",
        "start_date",
        "is_published",
    )
    list_filter = (
        "format",
        "is_published",
        "start_date",
    )
    search_fields = (
        "title",
        "description",
        "location",
    )
    list_editable = (
        "price",
        "is_published",
    )
    date_hierarchy = "start_date"


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course",
        "status",
        "source",
        "price_at_enrollment",
        "enrolled_at",
    )
    list_filter = (
        "status",
        "source",
        "course",
        "enrolled_at",
    )
    search_fields = (
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

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)
