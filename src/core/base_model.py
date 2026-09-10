"""
Base Model - Abstract base class with common fields and methods for all ERP models.
Provides audit tracking, soft delete, and standardized metadata.
"""

from typing import Any, Optional

from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """
    Abstract base model providing:
    - Created/Updated timestamps
    - Created/Updated by user tracking
    - Soft delete capability
    - Active status flag
    - Unique identifier (UUID)
    """

    created_at = models.DateTimeField(
        verbose_name="Created At",
        auto_now_add=True,
        help_text="Timestamp when the record was created",
    )
    updated_at = models.DateTimeField(
        verbose_name="Updated At",
        auto_now=True,
        help_text="Timestamp when the record was last updated",
    )
    created_by = models.ForeignKey(
        to="auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
        verbose_name="Created By",
        help_text="User who created this record",
    )
    updated_by = models.ForeignKey(
        to="auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
        verbose_name="Updated By",
        help_text="User who last updated this record",
    )
    is_active = models.BooleanField(
        verbose_name="Is Active",
        default=True,
        db_index=True,
        help_text="Soft delete flag - False means logically deleted",
    )
    is_deleted = models.BooleanField(
        verbose_name="Is Deleted",
        default=False,
        db_index=True,
        help_text="Soft delete marker",
    )
    deleted_at = models.DateTimeField(
        verbose_name="Deleted At",
        null=True,
        blank=True,
        help_text="Timestamp when soft deleted",
    )
    deleted_by = models.ForeignKey(
        to="auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_deleted",
        verbose_name="Deleted By",
        help_text="User who deleted this record",
    )
    remarks = models.TextField(
        verbose_name="Remarks",
        blank=True,
        null=True,
        help_text="Additional notes or comments",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_deleted"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        """String representation - override in child classes."""
        return f"{self.__class__.__name__} ({getattr(self, 'id', 'N/A')})"

    def soft_delete(
        self, user: Optional[Any] = None, remarks: Optional[str] = None
    ) -> None:
        """
        Perform soft delete on this record.

        Args:
            user: The user performing the deletion
            remarks: Optional reason for deletion
        """
        self.is_active = False
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        if remarks:
            self.remarks = remarks
        self.save(
            update_fields=[
                "is_active",
                "is_deleted",
                "deleted_at",
                "deleted_by",
                "remarks",
                "updated_at",
            ]
        )

    def restore(self, user: Optional[Any] = None) -> None:
        """
        Restore a soft-deleted record.

        Args:
            user: The user performing the restoration
        """
        self.is_active = True
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(
            update_fields=[
                "is_active",
                "is_deleted",
                "deleted_at",
                "deleted_by",
                "updated_at",
            ]
        )

    @property
    def age_days(self) -> int:
        """Return the age of the record in days."""
        delta = timezone.now() - self.created_at
        return delta.days

    @classmethod
    def active_objects(cls) -> models.QuerySet:
        """Return only active (non-deleted) objects."""
        return cls.objects.filter(is_active=True, is_deleted=False)

    @classmethod
    def deleted_objects(cls) -> models.QuerySet:
        """Return only soft-deleted objects."""
        return cls.objects.filter(is_deleted=True)
