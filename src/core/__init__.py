"""
Core module initialization
Provides shared utilities, base classes, and dynamic module loading for the ERP system.
"""

# Lazy imports to avoid Django app registry issues
__all__ = [
    "BaseModel",
    "ModuleLoader",
    "ModuleConfig",
    "ModuleSignalHandler",
]


def __getattr__(name):
    """Lazy loading of core components."""
    if name == "BaseModel":
        from .base_model import BaseModel

        return BaseModel
    elif name == "ModuleLoader":
        from .module_loader import ModuleLoader

        return ModuleLoader
    elif name == "ModuleConfig":
        from .module_loader import ModuleConfig

        return ModuleConfig
    elif name == "ModuleSignalHandler":
        from .signals import ModuleSignalHandler

        return ModuleSignalHandler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
