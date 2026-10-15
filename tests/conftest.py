"""
Pytest Configuration and Fixtures
==================================
Global test configuration, fixtures, and settings.

Note: the canonical user fixtures live in ``tests/fixtures.py`` (imported
below so they are available to every test). The dict-returning versions
that previously shadowed them here were removed because tests expect real
``User`` instances.
"""

import os

# Configure Django settings before importing models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")

# Re-export shared fixtures for automatic discovery by pytest.
from tests.fixtures import (  # noqa: E402,F401
    api_client,
    authenticated_client,
    sample_superuser,
    sample_user,
)
