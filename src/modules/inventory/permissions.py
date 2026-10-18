"""
Inventory Management Permissions
=================================
Role-based access control for inventory API endpoints.

Policy:
- All authenticated users may read inventory data (read-only viewsets
  such as StockLevel keep ``IsAuthenticated``).
- Mutating master data (products, categories, warehouses) requires the
  ``inventory.can_manage_master_data`` permission or staff status.
- Recording stock movements requires the ``inventory.record_movements``
  permission or staff status.
- Stock adjustments and movement edits/deletes are restricted to staff
  (or holders of ``inventory.can_adjust_stock``), so audit trails cannot
  be tampered with by regular users.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class _HasPermissionOrStaff(BasePermission):
    """Base class allowing write access to staff or explicit permission holders."""

    required_permission: str = ""

    def has_permission(self, request, view):
        """Reads need only authentication; writes need the role."""
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_staff
                or (self.required_permission and request.user.has_perm(self.required_permission))
            )
        )


class CanManageMasterData(_HasPermissionOrStaff):
    """Write access to products/categories/warehouses."""

    required_permission = "inventory.can_manage_master_data"


class CanRecordMovements(_HasPermissionOrStaff):
    """Create stock movements (audited via model-level validation)."""

    required_permission = "inventory.record_movements"


class CanAdjustStock(_HasPermissionOrStaff):
    """Adjust stock, and modify/delete existing movement records."""

    required_permission = "inventory.can_adjust_stock"

    def has_object_permission(self, request, view, obj):
        """Same policy at the object level (used by detail actions)."""
        return self.has_permission(request, view)
