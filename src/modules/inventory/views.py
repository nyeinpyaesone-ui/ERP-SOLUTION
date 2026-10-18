"""
Inventory Management Views
===========================
API views for inventory operations.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Category, Product, StockLevel, StockMovement, Warehouse
from .permissions import CanAdjustStock, CanManageMasterData, CanRecordMovements
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    StockAdjustmentSerializer,
    StockLevelSerializer,
    StockMovementSerializer,
    StockTransferSerializer,
    WarehouseSerializer,
    get_error_detail,
)


class WarehouseViewSet(viewsets.ModelViewSet):
    """ViewSet for warehouse management."""

    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated, CanManageMasterData]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code", "address"]
    ordering_fields = ["name", "code", "created_at"]


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for product category management."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, CanManageMasterData]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for product management."""

    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, CanManageMasterData]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "is_active"]
    search_fields = ["sku", "name", "description"]
    ordering_fields = ["name", "sku", "unit_price", "created_at"]

    @action(detail=True, methods=["get"])
    def stock_summary(self, request, pk=None):
        """Get stock summary for a product across all warehouses."""
        product = self.get_object()
        stock_levels = StockLevel.objects.filter(product=product).select_related("warehouse")

        summary = {
            "product": ProductSerializer(product).data,
            "total_stock": sum(sl.quantity for sl in stock_levels),
            "total_reserved": sum(sl.reserved_quantity for sl in stock_levels),
            "warehouses": StockLevelSerializer(stock_levels, many=True).data,
        }

        return Response(summary)


class StockLevelViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing stock levels."""

    queryset = StockLevel.objects.select_related("product", "warehouse").all()
    serializer_class = StockLevelSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["product", "warehouse"]
    ordering_fields = ["quantity", "updated_at"]

    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        """Get products with stock below reorder level."""
        low_stock_items = StockLevel.objects.filter(
            quantity__lte=F("product__reorder_level")
        ).select_related("product", "warehouse")

        serializer = self.get_serializer(low_stock_items, many=True)
        return Response(serializer.data)


class StockMovementViewSet(viewsets.ModelViewSet):
    """ViewSet for stock movement tracking.

    Writes are permission-scoped: creating movements requires the
    ``record_movements`` role; editing/deleting movement records (audit
    trail tampering) is restricted to stock managers/staff.
    """

    queryset = (
        StockMovement.objects.select_related("product", "warehouse").all().order_by("-created_at")
    )
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated, CanRecordMovements | CanAdjustStock]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["product", "warehouse", "movement_type"]
    ordering_fields = ["created_at"]

    def get_permissions(self):
        """Require the stricter adjustment role for destructive/override ops."""
        if self.action in ("destroy", "update", "partial_update", "adjust_stock"):
            return [IsAuthenticated(), CanAdjustStock()]
        return super().get_permissions()

    def get_serializer_context(self):
        """Inject the acting username so ``performed_by`` is server-stamped.

        The serializer marks ``performed_by`` read-only, so clients cannot
        spoof the audit trail through the plain POST endpoint.
        """
        context = super().get_serializer_context()
        user = getattr(self.request, "user", None)
        if user is not None and user.is_authenticated:
            context["user"] = user.get_username()
        return context

    @action(detail=False, methods=["post"])
    def adjust_stock(self, request):
        """Perform stock adjustment."""
        serializer = StockAdjustmentSerializer(data=request.data)

        if serializer.is_valid():
            try:
                movement = serializer.save(performed_by=request.user.get_username())
            except DjangoValidationError as exc:
                raise serializers.ValidationError(get_error_detail(exc)) from exc
            return Response(StockMovementSerializer(movement).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def transfer_stock(self, request):
        """Move stock between two warehouses as an atomic OUT + IN pair."""
        serializer = StockTransferSerializer(
            data=request.data, context={"user": request.user.get_username()}
        )

        if serializer.is_valid():
            try:
                result = serializer.save()
            except DjangoValidationError as exc:
                raise serializers.ValidationError(get_error_detail(exc)) from exc
            return Response(
                {
                    "transfer_out": StockMovementSerializer(result["transfer_out"]).data,
                    "transfer_in": StockMovementSerializer(result["transfer_in"]).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
