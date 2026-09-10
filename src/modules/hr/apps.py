"""
HR Module Configuration
"""

from django.apps import AppConfig


class HRConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.modules.hr"
    verbose_name = "Human Resources Management"

    def ready(self):
        """Initialize HR module signals and handlers."""
        # Register HR-specific signal handlers here
        pass
