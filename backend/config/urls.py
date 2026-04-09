from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from core.views import landing_page, user_portal

urlpatterns = [
    path("", landing_page),
    path("app/", user_portal),
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),

    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/trips/", include("trips.urls")),
]