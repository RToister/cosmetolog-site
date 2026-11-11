from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path(
        "",
        views.product_list,
        name="product-list",
    ),
    path(
        "products/<int:pk>/",
        views.product_detail,
        name="product-detail",
    ),
    path(
        "cart/",
        views.cart_detail,
        name="cart-detail",
    ),
    path(
        "cart/add/<int:product_id>/",
        views.cart_add,
        name="cart-add",
    ),
    path(
        "cart/update/<int:product_id>/",
        views.cart_update,
        name="cart-update",
    ),
    path(
        "cart/remove/<int:product_id>/",
        views.cart_remove,
        name="cart-remove",
    ),
    path(
        "checkout/",
        views.checkout,
        name="checkout",
    ),
    path(
        "orders/<int:order_id>/success/",
        views.order_success,
        name="order-success",
    ),
]
