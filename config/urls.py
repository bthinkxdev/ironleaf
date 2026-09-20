from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from config import settings

urlpatterns = [
    path(settings.env("DJANGO_ADMIN_URL", "admin/"), admin.site.urls),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("contact/", include("contact.urls")),
    path("", include("pages.urls")),
]

handler404 = "pages.views.not_found"
handler500 = "pages.views.server_error"
