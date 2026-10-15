"""
Inventory Module Configuration
"""

from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.modules.inventory"
    verbose_name = "Inventory Management"

    def ready(self):
        """Register inventory signal handlers exactly once."""
        from . import handlers  # noqa: F401  (connects receivers via @receiver)
