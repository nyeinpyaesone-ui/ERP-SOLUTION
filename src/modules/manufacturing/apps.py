"""Manufacturing Module Configuration"""

from django.apps import AppConfig


class ManufacturingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.modules.manufacturing"
    verbose_name = "Manufacturing & Production"
