"""
API URL Configuration
"""

from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

app_name = "api"

urlpatterns = [
    # Authentication endpoints (JWT via simplejwt — matches the default
    # authentication class configured in settings; without these routes the
    # API advertises JWT auth but clients can never obtain a token).
    # NOTE: explicit view routes are used because ``rest_framework_simplejwt``
    # ships no ``urls`` module.
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # Module API endpoints
    path("inventory/", include("src.modules.inventory.urls")),
    # path('hr/', include('src.modules.hr.api.urls')),
    # path('finance/', include('src.modules.finance.api.urls')),
    # path('sales/', include('src.modules.sales.api.urls')),
    # path('procurement/', include('src.modules.procurement.api.urls')),
    # path('manufacturing/', include('src.modules.manufacturing.api.urls')),
]
