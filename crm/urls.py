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
        "customers/create/",
        views.customer_create,
        name="customer-create",
    ),
    path(
        "customers/<int:pk>/",
        views.customer_detail,
        name="customer-detail",
    ),
    path(
        "customers/<int:pk>/edit/",
        views.customer_update,
        name="customer-update",
    ),
    path(
        "customers/<int:pk>/toggle-active/",
        views.customer_toggle_active,
        name="customer-toggle-active",
    ),
    path(
        (
            "customers/<int:pk>/"
            "verify-cosmetologist/"
        ),
        views.verify_cosmetologist,
        name="verify-cosmetologist",
    ),
    path(
        (
            "customers/<int:pk>/"
            "revoke-cosmetologist/"
        ),
        views.revoke_cosmetologist_verification,
        name=(
            "revoke-cosmetologist-verification"
        ),
    ),
]
