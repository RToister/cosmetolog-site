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
]
