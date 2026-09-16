from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path(
        "register/",
        views.register,
        name="register",
    ),
    path(
        "registration/pending/",
        views.registration_pending,
        name="registration-pending",
    ),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path(
        "dashboard/",
        views.dashboard,
        name="dashboard",
    ),
    path(
        "profile/edit/",
        views.profile_update,
        name="profile-update",
    ),
]
