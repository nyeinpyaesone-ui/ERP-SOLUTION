"""Procurement Module Configuration"""

from django.apps import AppConfig


class ProcurementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.modules.procurement"
    verbose_name = "Procurement & Purchasing"
