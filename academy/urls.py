from django.urls import path

from . import views

app_name = "academy"

urlpatterns = [
    path(
        "",
        views.course_list,
        name="course-list",
    ),
    path(
        "courses/<int:pk>/",
        views.course_detail,
        name="course-detail",
    ),
    path(
        "applications/<int:application_id>/success/",
        views.application_success,
        name="application-success",
    ),
]
