from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import (
    Order,
    OrderItem,
    Product,
    ProductCategory,
)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "products_count",
    )
    search_fields = (
        "name",
        "description",
    )

    @admin.display(description="Кількість товарів")
    def products_count(self, obj):
        return obj.products.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "category",
        "availability",
        "retail_price",
        "professional_price",
        "stock_quantity",
        "is_active",
    )
    list_filter = (
        "availability",
        "category",
        "is_active",
    )
    search_fields = (
        "name",
        "sku",
        "description",
        "usage_recommendations",
    )
    list_editable = (
        "stock_quantity",
        "is_active",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = (
        "name",
    )

    fieldsets = (
        (
            "Основна інформація",
            {
                "fields": (
                    "category",
                    "name",
                    "sku",
                    "description",
                    "usage_recommendations",
                    "image",
                )
            },
        ),
        (
            "Ціни та доступність",
            {
                "fields": (
                    "retail_price",
                    "professional_price",
                    "availability",
                )
            },
        ),
        (
            "Склад",
            {
                "fields": (
                    "stock_quantity",
                    "is_active",
                )
            },
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


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    autocomplete_fields = (
        "product",
    )
    readonly_fields = (
        "price_at_purchase",
        "subtotal_display",
    )
    fields = (
        "product",
        "quantity",
        "price_at_purchase",
        "subtotal_display",
    )

    @admin.display(description="Сума")
    def subtotal_display(self, obj):
        if not obj.pk:
            return "Буде розраховано після збереження"

        return f"{obj.subtotal:.2f} грн"

    def has_add_permission(
            self,
            request,
            obj=None,
    ):
        if (
                obj
                and obj.status != Order.Status.PENDING
        ):
            return False

        return super().has_add_permission(
            request,
            obj,
        )

    def has_delete_permission(
            self,
            request,
            obj=None,
    ):
        if (
                obj
                and obj.status != Order.Status.PENDING
        ):
            return False

        return super().has_delete_permission(
            request,
            obj,
        )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "client_name",
        "client_phone",
        "client_type",
        "total_price_display",
        "status",
        "source",
        "payment_method",
        "created_at",
    )
    list_filter = (
        "status",
        "source",
        "payment_method",
        "created_at",
    )
    search_fields = (
        "client_name",
        "client_phone",
        "client__username",
        "client__first_name",
        "client__last_name",
    )
    readonly_fields = (
        "total_price",
        "paid_at",
        "created_at",
        "updated_at",
        "created_by",
    )
    autocomplete_fields = (
        "client",
    )
    date_hierarchy = "created_at"
    inlines = (
        OrderItemInline,
    )
    actions = (
        "mark_selected_as_paid",
        "cancel_selected_orders",
    )

    fieldsets = (
        (
            "Покупець",
            {
                "fields": (
                    "client",
                    "client_name",
                    "client_phone",
                )
            },
        ),
        (
            "Замовлення",
            {
                "fields": (
                    "status",
                    "source",
                    "payment_method",
                    "total_price",
                )
            },
        ),
        (
            "Системна інформація",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_by",
                    "paid_at",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    @admin.display(description="Тип покупця")
    def client_type(self, obj):
        if obj.client_is_cosmetologist:
            return "Косметолог"

        if obj.client_id:
            return "Зареєстрований клієнт"

        return "Гість"

    @admin.display(description="Загальна сума")
    def total_price_display(self, obj):
        return f"{obj.total_price:.2f} грн"

    def save_model(
            self,
            request,
            obj,
            form,
            change,
    ):
        if not obj.created_by_id:
            obj.created_by = request.user

        if obj.source == Order.Source.ONLINE:
            obj.source = Order.Source.CLINIC

        super().save_model(
            request,
            obj,
            form,
            change,
        )

    def save_related(
            self,
            request,
            form,
            formsets,
            change,
    ):
        super().save_related(
            request,
            form,
            formsets,
            change,
        )

        form.instance.recalculate_total()

    @admin.action(
        description=(
                "Позначити вибрані замовлення оплаченими"
        )
    )
    def mark_selected_as_paid(
            self,
            request,
            queryset,
    ):
        completed_count = 0

        for order in queryset:
            try:
                order.mark_as_paid()
                completed_count += 1
            except ValidationError as error:
                self.message_user(
                    request,
                    (
                        f"Замовлення №{order.pk}: "
                        f"{'; '.join(error.messages)}"
                    ),
                    level=messages.ERROR,
                )

        if completed_count:
            self.message_user(
                request,
                (
                    f"Оплачено замовлень: "
                    f"{completed_count}."
                ),
                level=messages.SUCCESS,
            )

    @admin.action(
        description="Скасувати вибрані замовлення"
    )
    def cancel_selected_orders(
            self,
            request,
            queryset,
    ):
        cancelled_count = 0

        for order in queryset:
            try:
                order.cancel()
                cancelled_count += 1
            except ValidationError as error:
                self.message_user(
                    request,
                    (
                        f"Замовлення №{order.pk}: "
                        f"{'; '.join(error.messages)}"
                    ),
                    level=messages.ERROR,
                )

        if cancelled_count:
            self.message_user(
                request,
                (
                    f"Скасовано замовлень: "
                    f"{cancelled_count}."
                ),
                level=messages.SUCCESS,
            )
