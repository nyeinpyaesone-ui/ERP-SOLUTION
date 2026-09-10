"""
Test for core module - Module Loader, Base Model, and Signals
"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


# =============================================================================
# Module Loader Tests
# =============================================================================


@pytest.mark.unit
def test_module_loader_singleton():
    """Test that ModuleLoader is a singleton."""
    from src.core.module_loader import ModuleLoader

    loader1 = ModuleLoader()
    loader2 = ModuleLoader()

    assert loader1 is loader2


@pytest.mark.unit
def test_module_loader_inventory_enabled():
    """Test that inventory module is enabled by default."""
    from src.core.module_loader import module_loader

    inventory_module = module_loader.get_module("inventory")

    assert inventory_module is not None
    assert inventory_module.enabled is True
    assert inventory_module.api_prefix == "inventory"
    assert inventory_module.priority == 1


@pytest.mark.unit
def test_module_loader_get_enabled_apps():
    """Test getting list of enabled apps."""
    from src.core.module_loader import module_loader

    enabled_apps = module_loader.get_enabled_apps()

    assert isinstance(enabled_apps, list)
    assert len(enabled_apps) >= 1
    assert "src.modules.inventory" in enabled_apps


@pytest.mark.unit
def test_module_loader_get_api_prefix():
    """Test getting API prefix for modules."""
    from src.core.module_loader import module_loader

    assert module_loader.get_api_prefix("inventory") == "inventory"
    assert module_loader.get_api_prefix("hr") == "hr"


@pytest.mark.unit
def test_module_loader_urls_patterns():
    """Test getting URL patterns for enabled modules."""
    from src.core.module_loader import module_loader

    patterns = module_loader.get_urls_patterns()

    assert isinstance(patterns, list)
    # Should have at least inventory
    assert len(patterns) >= 1

    # Check inventory pattern structure
    inventory_pattern = next((p for p in patterns if "inventory" in p[0]), None)
    if inventory_pattern:
        assert "api/inventory/" in inventory_pattern[0]
        assert inventory_pattern[2] == "inventory"


# =============================================================================
# Signal Handler Tests
# =============================================================================


@pytest.mark.unit
def test_signal_handler_exists():
    """Test that signal_handler instance exists."""
    from src.core.signals import signal_handler

    assert signal_handler is not None


@pytest.mark.unit
def test_signal_handler_check_trigger():
    """Test checking triggers via signal handler."""
    from src.core.signals import signal_handler

    # Inventory module has these triggers defined in trigger_config.yaml
    assert signal_handler.check_trigger("inventory", "low_stock_alert") is True
    assert signal_handler.check_trigger("inventory", "stock_movement") is True
    # HR is disabled, so check_trigger returns None (module not loaded)
    result = signal_handler.check_trigger("hr", "employee_onboarded")
    assert (
        result is False or result is None
    )  # Either is acceptable for disabled modules


@pytest.mark.unit
def test_signal_handler_execute_triggered_actions(db):
    """Test executing triggered actions."""
    from src.core.signals import signal_handler
    from src.modules.inventory.models import Warehouse

    warehouse = Warehouse.objects.create(
        code="WH004", name="Trigger Test Warehouse", address="Test Location"
    )

    # Execute low_stock_alert trigger
    results = signal_handler.execute_triggered_actions(
        module_name="inventory",
        trigger_name="low_stock_alert",
        context={
            "product": None,
            "current_level": 5,
            "reorder_level": 10,
            "warehouse": warehouse,
        },
    )

    # Should return empty list since no handlers registered yet
    assert isinstance(results, list)


@pytest.mark.unit
def test_core_module_imports():
    """Test that core module can be imported."""
    from src import core

    assert core is not None


@pytest.mark.unit
def test_version():
    """Test version string exists."""
    from src import __version__

    assert __version__ == "0.1.0"


@pytest.mark.unit
def test_module_loader_reload():
    """Test reloading module configuration."""
    from src.core.module_loader import module_loader

    # Reload should work without errors
    module_loader.reload_config()

    # Inventory should still be loaded
    assert module_loader.get_module("inventory") is not None


@pytest.mark.unit
def test_module_loader_counts():
    """Test module count properties."""
    from src.core.module_loader import module_loader

    assert module_loader.total_count >= 1
    assert module_loader.enabled_count >= 1
    assert module_loader.enabled_count <= module_loader.total_count


@pytest.mark.unit
def test_base_model_string_representation(db):
    """Test BaseModel __str__ method via inventory models."""
    from src.modules.inventory.models import Warehouse

    warehouse = Warehouse.objects.create(
        code="WH_STR", name="String Test Warehouse", address="Test Address"
    )

    # Should return string representation
    result = str(warehouse)
    assert "WH_STR" in result
    assert "String Test Warehouse" in result
