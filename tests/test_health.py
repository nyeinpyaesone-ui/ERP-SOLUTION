"""Tests for the process liveness endpoint."""

import pytest


@pytest.mark.django_db
def test_health_endpoint_returns_ok(client):
    response = client.get("/health/")

    assert response.status_code == 200
    assert response.content == b"ok"
    assert response["Content-Type"].startswith("text/plain")
