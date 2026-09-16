from django.urls import path

from . import views

app_name = "appointments"

urlpatterns = [
    path(
        "book/",
        views.booking_create,
        name="booking-create",
    ),
    path(
        "success/",
        views.booking_success,
        name="booking-success",
    ),
    path(
        "available-times/",
        views.available_times,
        name="available-times",
    ),
    path(
        "manage/",
        views.booking_manage_list,
        name="manage-list",
    ),
    path(
        "manage/create/",
        views.booking_manage_create,
        name="manage-create",
    ),
    path(
        "manage/<int:pk>/",
        views.booking_manage_detail,
        name="manage-detail",
    ),
    path(
        "manage/<int:pk>/edit/",
        views.booking_manage_update,
        name="manage-update",
    ),
    path(
        "manage/<int:pk>/status/",
        views.booking_status_update,
        name="status-update",
    ),
    path(
        "manage/<int:pk>/comment/",
        views.booking_comment_update,
        name="comment-update",
    ),
]
