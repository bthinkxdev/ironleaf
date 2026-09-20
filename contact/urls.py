from django.urls import path

from . import views

app_name = "contact"

urlpatterns = [
    path("", views.contact, name="contact"),
    path("captcha/", views.captcha_image, name="captcha"),
]
