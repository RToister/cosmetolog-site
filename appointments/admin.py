from django.contrib import admin

from .models import Booking, VisitComment


class VisitCommentInline(admin.StackedInline):
    model = VisitComment
    extra = 0
    max_num = 1
    fields = ("text",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "client_name",
        "client_phone",
        "procedure",
        "date",
        "start_time",
        "end_time",
        "status",
        "source",
        "price_at_booking",
    )
    list_filter = (
        "status",
        "source",
        "date",
        "procedure",
    )
    search_fields = (
        "client_name",
        "client_phone",
        "client__username",
        "client__first_name",
        "procedure__name",
    )
    autocomplete_fields = (
        "client",
        "procedure",
    )
    readonly_fields = (
        "created_by",
        "end_time",
        "price_at_booking",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "date"
    ordering = ("-date", "-start_time")
    list_select_related = (
        "client",
        "procedure",
    )
    inlines = (VisitCommentInline,)

    fieldsets = (
        (
            "Клієнт",
            {
                "fields": (
                    "client",
                    "client_name",
                    "client_phone",
                )
            },
        ),
        (
            "Запис",
            {
                "fields": (
                    "procedure",
                    "date",
                    "start_time",
                    "end_time",
                    "price_at_booking",
                    "status",
                    "source",
                    "client_note",
                )
            },
        ),
        (
            "Системна інформація",
            {
                "fields": (
                    "created_by",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for deleted_object in formset.deleted_objects:
            deleted_object.delete()

        for instance in instances:
            if isinstance(instance, VisitComment):
                instance.author = request.user

            instance.save()

        formset.save_m2m()


@admin.register(VisitComment)
class VisitCommentAdmin(admin.ModelAdmin):
    list_display = (
        "booking",
        "author",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "booking__client_name",
        "booking__client_phone",
        "text",
    )
    autocomplete_fields = ("booking",)
    readonly_fields = (
        "author",
        "created_at",
        "updated_at",
    )

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user

        super().save_model(request, obj, form, change)
