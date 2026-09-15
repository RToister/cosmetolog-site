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
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "category",
        "retail_price",
        "professional_price",
        "availability",
        "stock_quantity",
        "is_active",
    )
    list_filter = (
        "category",
        "availability",
        "is_active",
    )
    search_fields = (
        "name",
        "sku",
        "description",
    )
    list_editable = (
        "retail_price",
        "professional_price",
        "stock_quantity",
        "is_active",
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    autocomplete_fields = ("product",)
    readonly_fields = ("price_at_purchase", "display_subtotal")

    @admin.display(description="Subtotal")
    def display_subtotal(self, obj):
        if not obj.pk:
            return "—"

        return obj.subtotal

    def has_add_permission(self, request, obj=None):
        if obj and obj.status != Order.Status.PENDING:
            return False

        return super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status != Order.Status.PENDING:
            return False

        return super().has_delete_permission(request, obj)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "client",
        "source",
        "status",
        "payment_method",
        "total_price",
        "created_at",
    )
    list_filter = (
        "status",
        "source",
        "payment_method",
        "created_at",
    )
    search_fields = (
        "client__username",
        "client__first_name",
        "client__last_name",
        "client__phone_number",
    )
    autocomplete_fields = (
        "client",
        "created_by",
    )
    readonly_fields = (
        "status",
        "total_price",
        "paid_at",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    inlines = (OrderItemInline,)
    actions = (
        "mark_selected_as_paid",
        "cancel_selected_orders",
    )

    @admin.action(description="Mark selected orders as paid")
    def mark_selected_as_paid(self, request, queryset):
        completed = 0

        for order in queryset:
            try:
                order.mark_as_paid()
                completed += 1
            except ValidationError as error:
                self.message_user(
                    request,
                    f"Order #{order.pk}: {error}",
                    level=messages.ERROR,
                )

        if completed:
            self.message_user(
                request,
                f"Paid orders: {completed}",
                level=messages.SUCCESS,
            )

    @admin.action(description="Cancel selected orders")
    def cancel_selected_orders(self, request, queryset):
        for order in queryset:
            order.cancel()

        self.message_user(
            request,
            f"Cancelled orders: {queryset.count()}",
            level=messages.SUCCESS,
        )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "product",
        "quantity",
        "price_at_purchase",
        "display_subtotal",
    )
    search_fields = (
        "product__name",
        "product__sku",
        "order__client__username",
    )
    autocomplete_fields = (
        "order",
        "product",
    )
    readonly_fields = ("price_at_purchase",)

    @admin.display(description="Subtotal")
    def display_subtotal(self, obj):
        return obj.subtotal
