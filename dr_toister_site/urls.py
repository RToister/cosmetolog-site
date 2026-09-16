from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from . import views

admin.site.site_header = (
    "DR TOISTER — панель керування"
)
admin.site.site_title = "DR TOISTER"
admin.site.index_title = "Керування клінікою"

urlpatterns = [
    path(
        "",
        views.home,
        name="home",
    ),
    path(
        "about/",
        views.about,
        name="about",
    ),
    path(
        "services/",
        views.service_list,
        name="service-list",
    ),
    path(
        "results/",
        views.results,
        name="results",
    ),
    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "accounts/",
        include("accounts.urls"),
    ),
    path(
        "appointments/",
        include("appointments.urls"),
    ),
    path(
        "shop/",
        include("shop.urls"),
    ),
    path(
        "academy/",
        include("academy.urls"),
    ),
    path(
        "analytics/",
        include("analytics.urls"),
    ),
    path(
        "crm/",
        include("crm.urls"),
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
