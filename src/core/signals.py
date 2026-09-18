"""
Signals - Centralized signal handling for module events and triggers.
Provides decoupled event-driven architecture for inter-module communication.
"""

from typing import Any, Dict, List, Optional

from django.db.models import Model
from django.dispatch import Signal

from .module_loader import module_loader

# =============================================================================
# Core ERP Signals
# =============================================================================

# Module lifecycle signals
module_initialized = Signal()
module_enabled = Signal()
module_disabled = Signal()

# Data operation signals (generic)
record_created = Signal()
record_updated = Signal()
record_deleted = Signal()
record_restored = Signal()

# Business event signals
low_stock_alert = Signal()
stock_movement_completed = Signal()
approval_required = Signal()
approval_granted = Signal()
approval_rejected = Signal()
payment_processed = Signal()
invoice_generated = Signal()
order_completed = Signal()


class ModuleSignalHandler:
    """
    Centralized handler for ERP module signals.

    Features:
    - Automatic trigger execution based on module configuration
    - Cross-module event propagation
    - Conditional signal processing
    - Audit logging integration
    """

    def __init__(self) -> None:
        """Initialize custom handlers and connect the default receivers."""
        self._registered_handlers: Dict[str, List[Any]] = {}
        self._connect_default_handlers()

    def _connect_default_handlers(self) -> None:
        """Connect default signal handlers."""
        record_created.connect(self._on_record_created)
        record_updated.connect(self._on_record_updated)
        record_deleted.connect(self._on_record_deleted)
        low_stock_alert.connect(self._on_low_stock_alert)
        stock_movement_completed.connect(self._on_stock_movement)

    def register_handler(
        self,
        signal: Signal,
        handler: Any,
        module_name: Optional[str] = None,
        priority: int = 0,
    ) -> None:
        """
        Register a custom signal handler.

        Args:
            signal: The Django Signal to handle
            handler: The callable to execute
            module_name: Optional module name for filtering
            priority: Handler priority (higher = executed first)
        """
        key = f"{signal.name}_{module_name or 'global'}"

        if key not in self._registered_handlers:
            self._registered_handlers[key] = []

        self._registered_handlers[key].append(
            {"handler": handler, "priority": priority, "module": module_name}
        )

        # Sort by priority (descending)
        self._registered_handlers[key].sort(key=lambda x: x["priority"], reverse=True)

        signal.connect(handler)

    def unregister_handler(self, signal: Signal, handler: Any) -> None:
        """Unregister a signal handler."""
        signal.disconnect(handler)

    def emit_event(
        self,
        signal: Signal,
        sender: Any = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[tuple]:
        """
        Emit a signal event with optional data payload.

        Args:
            signal: The signal to emit
            sender: The sender of the signal
            data: Optional data dictionary
            **kwargs: Additional keyword arguments

        Returns:
            List of (receiver, response) tuples
        """
        if data:
            kwargs["data"] = data

        return signal.send(sender=sender, **kwargs)

    def check_trigger(self, module_name: str, trigger_name: str) -> bool:
        """
        Check if a specific trigger is active for a module.

        Args:
            module_name: Name of the module
            trigger_name: Name of the trigger

        Returns:
            True if trigger is active
        """
        return module_loader.is_trigger_active(module_name, trigger_name)

    def execute_triggered_actions(
        self, module_name: str, trigger_name: str, context: Dict[str, Any]
    ) -> List[Any]:
        """
        Execute all actions associated with a trigger.

        Args:
            module_name: Name of the triggering module
            trigger_name: Name of the trigger
            context: Execution context data

        Returns:
            List of action results
        """
        if not self.check_trigger(module_name, trigger_name):
            return []

        results = []
        # Find and execute handlers for this trigger
        key = f"{trigger_name}_{module_name}"

        if key in self._registered_handlers:
            for handler_info in self._registered_handlers[key]:
                try:
                    result = handler_info["handler"](
                        sender=self, module=module_name, trigger=trigger_name, **context
                    )
                    results.append(result)
                except Exception as e:
                    # Log error but continue with other handlers
                    print(f"Error executing trigger {trigger_name}: {e}")

        return results

    # -------------------------------------------------------------------------
    # Default Signal Handlers
    # -------------------------------------------------------------------------

    def _on_record_created(
        self, sender: Model, instance: Model, created: bool, **kwargs
    ) -> None:
        """Handle record creation events."""
        if created:
            # Auto-audit logging could be added here
            pass

    def _on_record_updated(self, sender: Model, instance: Model, **kwargs) -> None:
        """Handle record update events."""
        # Track changes for audit trail
        pass

    def _on_record_deleted(self, sender: Model, instance: Model, **kwargs) -> None:
        """Handle record deletion events."""
        # Soft delete verification
        if hasattr(instance, "is_deleted") and instance.is_deleted:
            pass

    def _on_low_stock_alert(
        self,
        sender: Any,
        product: Any = None,
        current_level: int = 0,
        reorder_level: int = 0,
        warehouse: Any = None,
        **kwargs,
    ) -> None:
        """
        Handle low stock alerts.

        This trigger can activate:
        - Procurement module: Auto-create purchase order
        - Sales module: Mark product as backorder
        - HR module: Notify warehouse manager
        """
        if self.check_trigger("inventory", "low_stock_alert"):
            context = {
                "product": product,
                "current_level": current_level,
                "reorder_level": reorder_level,
                "warehouse": warehouse,
            }
            self.execute_triggered_actions("inventory", "low_stock_alert", context)

    def _on_stock_movement(
        self, sender: Any, movement: Any = None, movement_type: str = "", **kwargs
    ) -> None:
        """
        Handle stock movement completions.

        This trigger can activate:
        - Finance module: Update inventory valuation
        - Sales module: Confirm order fulfillment
        """
        if self.check_trigger("inventory", "stock_movement"):
            context = {
                "movement": movement,
                "movement_type": movement_type,
            }
            self.execute_triggered_actions("inventory", "stock_movement", context)


# Global signal handler instance
signal_handler = ModuleSignalHandler()
