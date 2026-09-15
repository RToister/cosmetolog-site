from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

admin.site.site_header = "DR TOISTER — панель керування"
admin.site.site_title = "DR TOISTER"
admin.site.index_title = "Керування клінікою"

urlpatterns = [
    path(
        "",
        TemplateView.as_view(
            template_name="home.html",
        ),
        name="home",
    ),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path(
        "appointments/",
        include("appointments.urls"),
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
