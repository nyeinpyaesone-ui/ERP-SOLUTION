"""
Inventory Module URL Configuration
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CategoryViewSet, ProductViewSet, StockLevelViewSet,
                    StockMovementViewSet, WarehouseViewSet)

router = DefaultRouter()
router.register(r"warehouses", WarehouseViewSet)
router.register(r"categories", CategoryViewSet)
router.register(r"products", ProductViewSet)
router.register(r"stock-levels", StockLevelViewSet)
router.register(r"stock-movements", StockMovementViewSet)

app_name = "inventory"

urlpatterns = [
    path("", include(router.urls)),
]
