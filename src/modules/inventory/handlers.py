"""
Inventory Signal Handlers
==========================
Receivers for core ERP signals emitted by inventory models.

Registered once from ``InventoryConfig.ready()`` using Django's
``@receiver`` decorator with ``dispatch_uid`` so repeated imports can
never double-connect a handler.
"""

import logging

from django.dispatch import receiver

from src.core.signals import low_stock_alert, stock_movement_completed

logger = logging.getLogger(__name__)


@receiver(
    stock_movement_completed,
    dispatch_uid="inventory.log_stock_movement",
)
def log_stock_movement(sender, movement=None, movement_type="", **kwargs):
    """Audit-log completed stock movements (finance valuation hook point)."""
    if movement is not None:
        logger.info(
            "Stock movement completed: %s x%s %s @ %s",
            movement_type,
            getattr(movement, "quantity", "?"),
            getattr(getattr(movement, "product", None), "sku", "?"),
            getattr(getattr(movement, "warehouse", None), "code", "?"),
        )


@receiver(
    low_stock_alert,
    dispatch_uid="inventory.handle_low_stock",
)
def handle_low_stock(
    sender, product=None, current_level=0, reorder_level=0, warehouse=None, **kwargs
):
    """React to low-stock events (procurement auto-PO hook point)."""
    logger.warning(
        "Low stock alert: %s at %s (%s <= reorder level %s)",
        getattr(product, "sku", "?"),
        getattr(warehouse, "code", "?"),
        current_level,
        reorder_level,
    )
