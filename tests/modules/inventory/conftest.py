"""Shared fixtures for the inventory test package."""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def staff_user(db):
    """Create a staff user with write access to inventory endpoints."""
    return User.objects.create_user(
        username="warehouse_manager",
        email="manager@example.com",
        password="staffpassword123",
        is_staff=True,
    )


@pytest.fixture
def regular_user(db):
    """Create a non-staff authenticated user (read-only for writes)."""
    return User.objects.create_user(
        username="regularuser",
        email="regular@example.com",
        password="userpassword123",
    )
