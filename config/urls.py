"""
URL Configuration for ERP System
=================================
Dynamic URL routing based on module configuration.
"""

from typing import Any, Optional

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# Import dynamic module loader (kept available for programmatic inspection;
# URL registration intentionally goes through src/api/urls.py only — see the
# note below urlpatterns).
try:
    from src.core.module_loader import module_loader as _module_loader

    module_loader: Optional[Any] = _module_loader
except ImportError:
    module_loader = None

urlpatterns = [
    # Admin interface
    path("admin/", admin.site.urls),
    # API endpoints (module routes are registered here; see src/api/urls.py)
    path("api/", include("src.api.urls")),
]

# NOTE: Module URLs are wired through src/api/urls.py only. The dynamic
# module loader's get_urls_patterns() would register the same routes a
# second time under conflicting namespaces, so it is intentionally not
# used for URL registration here.

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "ERP System Administration"
admin.site.site_title = "ERP Admin"
admin.site.index_title = "Welcome to ERP System Administration"
