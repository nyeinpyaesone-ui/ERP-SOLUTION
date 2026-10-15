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

# Registry mapping declared signal names to their Signal objects. Used by
# ModuleSignalHandler.register_handler to derive stable trigger keys that
# match execute_triggered_actions()'s "<trigger>_<module>" lookup format.
_SIGNAL_REGISTRY: Dict[str, Signal] = {
    "module_initialized": module_initialized,
    "module_enabled": module_enabled,
    "module_disabled": module_disabled,
    "record_created": record_created,
    "record_updated": record_updated,
    "record_deleted": record_deleted,
    "record_restored": record_restored,
    "low_stock_alert": low_stock_alert,
    "stock_movement_completed": stock_movement_completed,
    "approval_required": approval_required,
    "approval_granted": approval_granted,
    "approval_rejected": approval_rejected,
    "payment_processed": payment_processed,
    "invoice_generated": invoice_generated,
    "order_completed": order_completed,
}


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
        signal,
        handler: Any,
        module_name: Optional[str] = None,
        priority: int = 0,
        trigger_name: Optional[str] = None,
    ) -> None:
        """
        Register a custom signal handler.

        Accepts either a Django ``Signal`` object or its declared name
        (e.g. ``"stock_movement_completed"``); when a name is given it is
        resolved through ``_SIGNAL_REGISTRY``.

        Args:
            signal: The Django Signal (or its registered name) to handle
            handler: The callable to execute
            module_name: Optional module name for filtering and trigger keys
            priority: Handler priority (higher = executed first)
            trigger_name: Optional trigger name; defaults to the signal's
                global name so ``execute_triggered_actions`` can find it.
        """
        # Allow callers to pass the signal by name as well as by object.
        if isinstance(signal, str):
            trigger_name = trigger_name or signal
            signal = _SIGNAL_REGISTRY[signal]

        # Resolve the signal's declared global name (e.g. "low_stock_alert")
        # from the module-level registry so trigger lookups stay stable.
        if trigger_name is None:
            trigger_name = next(
                (n for n, s in _SIGNAL_REGISTRY.items() if s is signal),
                str(id(signal)),
            )

        # Registry key must match execute_triggered_actions(): "<trigger>_<module>".
        key = f"{trigger_name}_{module_name}"
        entries = self._registered_handlers.setdefault(key, [])
        # Replace any previous registration of the same handler so
        # re-registering never duplicates entries or double-connects.
        entries[:] = [e for e in entries if e["handler"] is not handler]
        entries.append({"handler": handler, "priority": priority, "module": module_name})
        # Django dispatches receivers in connection order, so emulate
        # "higher priority = executed first" by sorting before connecting.
        entries.sort(key=lambda x: x["priority"], reverse=True)

        # Disconnect first so re-registering never double-connects a handler.
        # dispatch_uid alone identifies the connection (passing ``sender`` to
        # disconnect() would filter by sender and fail to remove a receiver
        # connected without one).
        # Note: passing dispatch_uid makes Django store a strong reference to
        # the receiver (Django 4.0+ removed the ``weakref`` connect() kwarg).
        signal.disconnect(dispatch_uid=self._dispatch_uid(signal, handler))
        signal.connect(handler, dispatch_uid=self._dispatch_uid(signal, handler))

    @staticmethod
    def _dispatch_uid(signal: Signal, handler: Any) -> str:
        """Stable unique id for a (signal, handler) connection."""
        return f"{id(signal)}:{getattr(handler, '__qualname__', str(handler))}"

    def unregister_handler(self, signal, handler: Any) -> None:
        """Unregister a signal handler (accepts a Signal object or its name)."""
        if isinstance(signal, str):
            signal = _SIGNAL_REGISTRY[signal]
        signal.disconnect(dispatch_uid=self._dispatch_uid(signal, handler))
        for entries in self._registered_handlers.values():
            entries[:] = [e for e in entries if e["handler"] is not handler]

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

    def _on_record_created(self, sender: Model, instance: Model, created: bool, **kwargs) -> None:
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
        # Trigger name must match the signal name declared in
        # trigger_config.yaml ("stock_movement_completed"); the previous
        # "stock_movement" key never matched any configured trigger.
        if self.check_trigger("inventory", "stock_movement_completed"):
            context = {
                "movement": movement,
                "movement_type": movement_type,
            }
            self.execute_triggered_actions("inventory", "stock_movement_completed", context)


# Global signal handler instance
signal_handler = ModuleSignalHandler()
