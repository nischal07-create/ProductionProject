from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from core.views import landing_page, user_portal
from trips.views import trekking_routes_list, trekking_route_detail, trekking_offline_pack

urlpatterns = [
    path("", landing_page),
    path("app/", user_portal),
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),

    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/trips/", include("trips.urls")),
    path("api/trekking/routes/", trekking_routes_list, name="trekking-routes-list-backup"),
    path("api/trekking/routes/<slug:route_id>/", trekking_route_detail, name="trekking-route-detail-backup"),
    path("api/trekking/routes/<slug:route_id>/offline/", trekking_offline_pack, name="trekking-route-offline-backup"),
]