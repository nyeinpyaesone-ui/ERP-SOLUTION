"""Finance Module Configuration"""

from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.modules.finance"
    verbose_name = "Finance & Accounting"
