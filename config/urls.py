"""
URL Configuration for ERP System
=================================
Dynamic URL routing based on module configuration.
"""

from typing import TYPE_CHECKING, Any, Optional

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

if TYPE_CHECKING:
    from src.core.module_loader import ModuleLoader

# Import dynamic module loader
try:
    from src.core.module_loader import module_loader as _module_loader

    module_loader: Optional[Any] = _module_loader
except ImportError:
    module_loader = None

urlpatterns = [
    # Admin interface
    path("admin/", admin.site.urls),
    # API endpoints
    path("api/", include("src.api.urls")),
]

# Dynamically add module URLs if loader is available
if module_loader:
    try:
        url_patterns = module_loader.get_urls_patterns()
        for path_prefix, urlconf_module, namespace in url_patterns:
            urlpatterns.append(
                path(
                    path_prefix,
                    include((urlconf_module, namespace), namespace=namespace),
                )
            )
    except Exception as e:
        if settings.DEBUG:
            print(f"Warning: Failed to load dynamic URLs: {e}")

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "ERP System Administration"
admin.site.site_title = "ERP Admin"
admin.site.index_title = "Welcome to ERP System Administration"
