"""
Inventory Management Models
============================
Core models for stock tracking, warehouse management, and inventory operations.
"""

import logging

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F

logger = logging.getLogger(__name__)


class Warehouse(models.Model):
    """Represents a warehouse or storage location."""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Warehouses"

    def __str__(self):
        """Return the warehouse code and name."""
        return f"{self.code} - {self.name}"


class Category(models.Model):
    """Product categories for inventory classification."""

    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        """Return the category name."""
        return self.name


class Product(models.Model):
    """Main product model for inventory items."""

    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="products"
    )
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    cost_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], default=0
    )
    reorder_level = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        """Return the product SKU and name."""
        return f"{self.sku} - {self.name}"

    @property
    def total_stock(self):
        """Calculate total stock across all warehouses (single query)."""
        return self.stock_levels.aggregate(total=models.Sum("quantity"))["total"] or 0


class StockLevel(models.Model):
    """Tracks stock levels per product per warehouse."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_levels")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="stock_levels")
    quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)
    last_counted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["product", "warehouse"]
        ordering = ["warehouse", "product"]

    def __str__(self):
        """Return the product, warehouse, and current quantity."""
        return f"{self.product.sku} @ {self.warehouse.code}: {self.quantity}"

    @property
    def available_quantity(self):
        """Calculate available quantity (total - reserved)."""
        return self.quantity - self.reserved_quantity


class StockMovement(models.Model):
    """Tracks all stock movements (in/out/transfer)."""

    MOVEMENT_TYPES = [
        ("IN", "Stock In"),
        ("OUT", "Stock Out"),
        ("TRANSFER_IN", "Transfer In"),
        ("TRANSFER_OUT", "Transfer Out"),
        ("ADJUSTMENT", "Adjustment"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="movements")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="movements")
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()  # Can be negative for out
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    performed_by = models.CharField(max_length=100)  # User ID or name
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "-created_at"]),
            models.Index(fields=["warehouse", "-created_at"]),
        ]

    def __str__(self):
        """Return the movement type, product SKU, and quantity."""
        return f"{self.movement_type}: {self.product.sku} ({self.quantity})"

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Create the movement and apply its stock effect exactly once.

        Side effects (stock level updates) only run when the movement is
        first created, so re-saving an existing movement never double-applies
        the quantity change. Stock updates use atomic ``F()`` expressions to
        avoid lost updates under concurrency.
        """
        is_new = self.pk is None

        if is_new:
            if self.quantity < 0:
                raise ValidationError({"quantity": "Quantity must be a positive integer."})

            # Validate outbound movements against current available stock
            # inside the same transaction that mutates the stock level.
            if self.movement_type in ("OUT", "TRANSFER_OUT"):
                stock_level = (
                    StockLevel.objects.select_for_update()
                    .filter(product=self.product, warehouse=self.warehouse)
                    .first()
                )
                available = (
                    stock_level.quantity - stock_level.reserved_quantity if stock_level else 0
                )
                if self.quantity > available:
                    raise ValidationError({"quantity": "Insufficient stock for this movement"})

        super().save(*args, **kwargs)

        if not is_new:
            return

        stock_level, _created = StockLevel.objects.get_or_create(
            product=self.product, warehouse=self.warehouse, defaults={"quantity": 0}
        )

        if self.movement_type in ("IN", "TRANSFER_IN"):
            StockLevel.objects.filter(pk=stock_level.pk).update(
                quantity=F("quantity") + self.quantity
            )
        elif self.movement_type in ("OUT", "TRANSFER_OUT"):
            StockLevel.objects.filter(pk=stock_level.pk).update(
                quantity=F("quantity") - self.quantity
            )
        elif self.movement_type == "ADJUSTMENT":
            StockLevel.objects.filter(pk=stock_level.pk).update(quantity=self.quantity)

        # Refresh in-memory instance so callers see the persisted value.
        stock_level.refresh_from_db()

        self.emit_signals(stock_level)

    def emit_signals(self, stock_level=None):
        """Broadcast inventory events for cross-module reactions.

        Emitted after the movement and its stock side effects have been
        committed inside the surrounding transaction. Failures in external
        receivers must never corrupt inventory data, so receiver errors are
        contained and logged rather than propagated.
        """
        from src.core.signals import (
            low_stock_alert,
            signal_handler,
            stock_movement_completed,
        )

        if stock_level is None:
            stock_level = StockLevel.objects.filter(
                product=self.product, warehouse=self.warehouse
            ).first()

        try:
            signal_handler.emit_event(
                stock_movement_completed,
                sender=StockMovement,
                movement=self,
                movement_type=self.movement_type,
            )

            quantity = stock_level.quantity if stock_level else 0
            if quantity <= self.product.reorder_level:
                signal_handler.emit_event(
                    low_stock_alert,
                    sender=Product,
                    product=self.product,
                    current_level=quantity,
                    reorder_level=self.product.reorder_level,
                    warehouse=self.warehouse,
                )
        except Exception:  # noqa: BLE001 - eventing must not break movements
            logger.exception("Failed to emit inventory signals for movement %s", self.pk)
