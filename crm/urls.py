from django.urls import path

from . import views

app_name = "crm"

urlpatterns = [
    path(
        "",
        views.customer_list,
        name="customer-list",
    ),
    path(
        "customers/<int:pk>/",
        views.customer_detail,
        name="customer-detail",
    ),
]
