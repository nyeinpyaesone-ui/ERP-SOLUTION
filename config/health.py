"""Health endpoints for container and load-balancer probes."""

from django.http import HttpRequest, HttpResponse


def health_check(request: HttpRequest) -> HttpResponse:
    """Return HTTP 200 while the Django process can serve requests.

    This is intentionally a liveness check: it does not query PostgreSQL or
    Redis. Dependency readiness should be monitored independently.
    """
    return HttpResponse("ok", content_type="text/plain; charset=utf-8")
