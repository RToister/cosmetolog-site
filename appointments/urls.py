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
]
