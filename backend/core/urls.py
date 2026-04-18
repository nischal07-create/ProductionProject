from django.urls import path # type: ignore
from .views import health, home, register

urlpatterns = [
    path("", home),
    path("health/", health),
    path("auth/register/", register, name="register"),
]