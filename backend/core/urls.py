from django.urls import path # type: ignore
from .views import (
    health,
    home,
    register,
    operator_portal,
    forgot_password_page,
    request_password_reset,
    confirm_password_reset,
    session_status,
)

urlpatterns = [
    path("", home),
    path("health/", health),
    path("auth/register/", register, name="register"),
    path("auth/password-reset/request/", request_password_reset, name="password-reset-request"),
    path("auth/password-reset/confirm/", confirm_password_reset, name="password-reset-confirm"),
    path("auth/session/", session_status, name="session-status"),
    path("operator/", operator_portal, name="operator-portal"),
    path("forgot-password/", forgot_password_page, name="forgot-password"),
]