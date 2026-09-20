from django.urls import path
from django.views.generic import TemplateView

app_name = "pages"

urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html", extra_context={"active": "home"}), name="home"),
    path("about/", TemplateView.as_view(template_name="pages/about.html", extra_context={"active": "about"}), name="about"),
    path("services/", TemplateView.as_view(template_name="pages/services.html", extra_context={"active": "services"}), name="services"),
    path("trading/", TemplateView.as_view(template_name="pages/trading.html", extra_context={"active": "trading"}), name="trading"),
]
