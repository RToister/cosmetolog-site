from django.contrib import admin

from .models import BlockedDate, WorkingHour


@admin.register(WorkingHour)
class WorkingHourAdmin(admin.ModelAdmin):
    list_display = (
        "day_of_week",
        "start_time",
        "end_time",
        "is_active",
    )
    list_filter = ("is_active",)
    list_editable = ("start_time", "end_time", "is_active")
    ordering = ("day_of_week",)


@admin.register(BlockedDate)
class BlockedDateAdmin(admin.ModelAdmin):
    list_display = ("date", "reason")
    search_fields = ("reason",)
    date_hierarchy = "date"
    ordering = ("date",)
