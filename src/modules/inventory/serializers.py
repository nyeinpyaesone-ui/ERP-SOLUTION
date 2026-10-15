"""
Inventory Management Serializers
=================================
DRF serializers for inventory models.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import Category, Product, StockLevel, StockMovement, Warehouse


class WarehouseSerializer(serializers.ModelSerializer):
    """Serializer for Warehouse model."""

    class Meta:
        model = Warehouse
        fields = [
            "id",
            "name",
            "code",
            "address",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""

    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "parent", "description", "children_count", "created_at"]
        read_only_fields = ["created_at"]

    def get_children_count(self, obj):
        """Return the number of direct child categories."""
        return obj.children.count() if hasattr(obj, "children") else 0


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""

    category_name = serializers.SerializerMethodField()
    total_stock = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "name",
            "description",
            "category",
            "category_name",
            "unit_price",
            "cost_price",
            "reorder_level",
            "is_active",
            "total_stock",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_category_name(self, obj):
        """Return the category name, tolerating a null category."""
        return obj.category.name if obj.category else None


class StockLevelSerializer(serializers.ModelSerializer):
    """Serializer for StockLevel model."""

    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    available_quantity = serializers.ReadOnlyField()

    class Meta:
        model = StockLevel
        fields = [
            "id",
            "product",
            "product_sku",
            "product_name",
            "warehouse",
            "warehouse_name",
            "quantity",
            "reserved_quantity",
            "available_quantity",
            "last_counted_at",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]


class StockMovementSerializer(serializers.ModelSerializer):
    """Serializer for StockMovement model.

    Business validation (sufficient stock, positive quantity) lives in
    ``StockMovement.save()`` so it cannot be bypassed through this
    endpoint; here we surface those errors as 400 responses.
    """

    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "product",
            "product_sku",
            "product_name",
            "warehouse",
            "warehouse_name",
            "movement_type",
            "quantity",
            "reference",
            "notes",
            "performed_by",
            "created_at",
        ]
        read_only_fields = ["created_at", "performed_by"]

    def validate_quantity(self, value):
        """Quantities are always positive; direction comes from movement_type."""
        if value < 0:
            raise serializers.ValidationError("Quantity must be a positive integer.")
        return value

    def create(self, validated_data):
        """Create a movement, translating model validation errors to 400s."""
        # Audit trail: stamp the acting user server-side so ``performed_by``
        # cannot be spoofed through the plain POST endpoint (the field is
        # read-only here; views inject it into the serializer context).
        if "performed_by" not in validated_data:
            validated_data["performed_by"] = self.context.get("user", "system")
        try:
            return super().create(validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(get_error_detail(exc)) from exc


def get_error_detail(exc_info):
    """Convert a Django ValidationError into an DRF-style error dict/list."""
    error_dict = {}
    error_list = []
    for e in exc_info.error_list:
        try:
            key = e.params["field"]
        except (AttributeError, KeyError, TypeError):
            error_list.append(e.messages[0])
        else:
            error_dict.setdefault(key, []).extend(e.messages)
    return error_dict or error_list


class StockAdjustmentSerializer(serializers.Serializer):
    """Serializer for stock adjustment operations."""

    product_id = serializers.IntegerField()
    warehouse_id = serializers.IntegerField()
    movement_type = serializers.ChoiceField(choices=StockMovement.MOVEMENT_TYPES)
    quantity = serializers.IntegerField()
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        """Validate referenced records and quantity sign.

        Stock-sufficiency checks are enforced atomically in
        ``StockMovement.save()`` (with a row lock), so we do not duplicate
        the read here — that would be vulnerable to TOCTOU races.
        """
        # Validate product exists
        if not Product.objects.filter(id=data["product_id"]).exists():
            raise serializers.ValidationError({"product_id": "Product does not exist"})

        # Validate warehouse exists
        if not Warehouse.objects.filter(id=data["warehouse_id"]).exists():
            raise serializers.ValidationError({"warehouse_id": "Warehouse does not exist"})

        # Quantities are always positive; direction comes from movement_type
        if data["quantity"] < 0:
            raise serializers.ValidationError({"quantity": "Quantity must be a positive integer."})

        return data

    def create(self, validated_data):
        """Create a stock movement from validated adjustment data."""
        return StockMovement.objects.create(**validated_data)


class StockTransferSerializer(serializers.Serializer):
    """Move stock between two warehouses as an atomic OUT + IN pair."""

    product_id = serializers.IntegerField()
    source_warehouse_id = serializers.IntegerField()
    destination_warehouse_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        """Ensure both warehouses exist and they are distinct."""
        if data["source_warehouse_id"] == data["destination_warehouse_id"]:
            raise serializers.ValidationError(
                {"destination_warehouse_id": "Source and destination must differ"}
            )
        if not Product.objects.filter(id=data["product_id"]).exists():
            raise serializers.ValidationError({"product_id": "Product does not exist"})
        wh_ids = [data["source_warehouse_id"], data["destination_warehouse_id"]]
        if not Warehouse.objects.filter(id__in=wh_ids).count() == 2:
            raise serializers.ValidationError("One or more warehouses do not exist")
        return data

    @transaction.atomic
    def create(self, validated_data):
        """Create paired TRANSFER_OUT / TRANSFER_IN movements atomically.

        The OUT movement is validated against available stock inside
        ``StockMovement.save()``; if it fails, the whole transfer rolls back.
        """
        common = {
            "product_id": validated_data["product_id"],
            "quantity": validated_data["quantity"],
            "reference": validated_data.get("reference", ""),
            "notes": validated_data.get("notes", ""),
            "performed_by": self.context.get("user", "system"),
        }
        out = StockMovement.objects.create(
            movement_type="TRANSFER_OUT",
            warehouse_id=validated_data["source_warehouse_id"],
            **common,
        )
        transfer_in = StockMovement.objects.create(
            movement_type="TRANSFER_IN",
            warehouse_id=validated_data["destination_warehouse_id"],
            **common,
        )
        return {"transfer_out": out, "transfer_in": transfer_in}
