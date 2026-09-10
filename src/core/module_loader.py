"""
Module Loader - Dynamic module discovery and registration system.
Enables plug-and-play architecture for ERP modules.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from django.conf import settings


@dataclass
class ModuleConfig:
    """Configuration for a single ERP module."""

    name: str
    enabled: bool
    api_prefix: str
    priority: int = 99
    triggers: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    version: str = "1.0.0"

    @property
    def app_label(self) -> str:
        """Return the Django app label for this module."""
        return f"src.modules.{self.name}"

    @property
    def urls_module(self) -> str:
        """Return the dotted path to the URLs module."""
        return f"{self.app_label}.urls"

    @property
    def is_ready(self) -> bool:
        """Check if module has required files."""
        module_path = Path(settings.BASE_DIR) / "src" / "modules" / self.name
        return module_path.exists() and (module_path / "urls.py").exists()


class ModuleLoader:
    """
    Dynamic module discovery and registration system.

    Features:
    - Auto-discovery of modules from trigger_config.yaml
    - Priority-based loading order
    - Dependency resolution
    - Runtime module activation/deactivation
    - Trigger-based event system integration
    """

    _instance: Optional["ModuleLoader"] = None
    _modules: Dict[str, ModuleConfig] = {}
    _config_path: Optional[Path] = None

    def __new__(cls) -> "ModuleLoader":
        """Return the shared module loader instance."""
        if cls._instance is None:
            cls._instance = super(ModuleLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Load module configuration once for the shared instance."""
        if self._modules:
            return

        self._load_config()

    def _load_config(self) -> None:
        """Load module configuration from YAML file."""
        # Try multiple possible locations for trigger_config.yaml
        possible_paths = [
            Path(settings.BASE_DIR).parent
            / "trigger_config.yaml",  # Original (when BASE_DIR is /workspace/src)
            Path(settings.BASE_DIR)
            / "trigger_config.yaml",  # Alternative (when BASE_DIR is /workspace)
            Path(__file__).parent.parent.parent
            / "trigger_config.yaml",  # Relative to this file
        ]

        config_path = None
        for path in possible_paths:
            if path.exists():
                config_path = path
                break

        if config_path is None:
            # Fallback to default configuration
            self._load_defaults()
            return

        self._config_path = config_path

        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            for mod_data in config.get("modules", []):
                mod_config = ModuleConfig(
                    name=mod_data["name"],
                    enabled=mod_data.get("enabled", False),
                    api_prefix=mod_data.get("api_prefix", mod_data["name"]),
                    priority=mod_data.get("priority", 99),
                    triggers=mod_data.get("triggers", []),
                    dependencies=mod_data.get("dependencies", []),
                    version=mod_data.get("version", "1.0.0"),
                )

                if mod_config.enabled and mod_config.is_ready:
                    self._modules[mod_config.name] = mod_config

        except Exception as e:
            if settings.DEBUG:
                print(f"Warning: Failed to load trigger_config.yaml: {e}")
            self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default module configuration."""
        default_modules = [
            ModuleConfig(
                name="inventory", enabled=True, api_prefix="inventory", priority=1
            ),
            ModuleConfig(name="hr", enabled=False, api_prefix="hr", priority=2),
            ModuleConfig(
                name="finance", enabled=False, api_prefix="finance", priority=3
            ),
            ModuleConfig(name="sales", enabled=False, api_prefix="sales", priority=4),
            ModuleConfig(
                name="procurement", enabled=False, api_prefix="procurement", priority=5
            ),
            ModuleConfig(
                name="manufacturing",
                enabled=False,
                api_prefix="manufacturing",
                priority=6,
            ),
        ]

        for mod in default_modules:
            if mod.enabled and mod.is_ready:
                self._modules[mod.name] = mod

    def get_enabled_apps(self) -> List[str]:
        """Return list of enabled app labels in priority order."""
        enabled = [m for m in self._modules.values() if m.enabled]
        enabled.sort(key=lambda x: x.priority)
        return [m.app_label for m in enabled]

    def get_all_modules(self) -> Dict[str, ModuleConfig]:
        """Return all registered modules."""
        return self._modules.copy()

    def get_module(self, name: str) -> Optional[ModuleConfig]:
        """Get configuration for a specific module."""
        return self._modules.get(name)

    def get_api_prefix(self, module_name: str) -> str:
        """Get API prefix for a module."""
        mod = self._modules.get(module_name)
        return mod.api_prefix if mod else module_name

    def get_urls_patterns(self) -> List[tuple]:
        """
        Return URL patterns for all enabled modules.

        Returns:
            List of tuples: (path_prefix, urlconf_module, namespace)
        """
        patterns = []
        enabled = [m for m in self._modules.values() if m.enabled]
        enabled.sort(key=lambda x: x.priority)

        for mod in enabled:
            if mod.is_ready:
                patterns.append((f"api/{mod.api_prefix}/", mod.urls_module, mod.name))

        return patterns

    def is_trigger_active(self, module_name: str, trigger_name: str) -> bool:
        """Check if a specific trigger is active for a module."""
        mod = self._modules.get(module_name)
        if mod:
            return trigger_name in mod.triggers
        return False

    def get_triggers_for_module(self, module_name: str) -> List[str]:
        """Get all active triggers for a module."""
        mod = self._modules.get(module_name)
        return mod.triggers if mod else []

    def enable_module(self, name: str) -> bool:
        """Enable a module dynamically."""
        mod = self._modules.get(name)
        if mod and mod.is_ready:
            mod.enabled = True
            return True
        return False

    def disable_module(self, name: str) -> bool:
        """Disable a module dynamically."""
        mod = self._modules.get(name)
        if mod:
            mod.enabled = False
            return True
        return False

    def reload_config(self) -> None:
        """Reload configuration from YAML file."""
        self._modules.clear()
        self._load_config()

    @property
    def enabled_count(self) -> int:
        """Return count of enabled modules."""
        return sum(1 for m in self._modules.values() if m.enabled)

    @property
    def total_count(self) -> int:
        """Return total count of registered modules."""
        return len(self._modules)


# Singleton instance
module_loader = ModuleLoader()
