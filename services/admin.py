from django.contrib import admin

from .models import Procedure, ProcedureCategory


@admin.register(ProcedureCategory)
class ProcedureCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "duration_minutes",
        "price",
        "is_active",
    )
    list_filter = ("category", "is_active")
    search_fields = ("name", "description")
    list_editable = ("price", "is_active")
