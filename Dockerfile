# Multi-stage Production Dockerfile for ERP-SOLUTION
# Optimized for Django 4.2+ with PostgreSQL + Redis + Celery

# =============================================================================
# Stage 1: Builder - Install dependencies and compile bytecode
# =============================================================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies and compile bytecode
RUN pip wheel --no-cache-dir --wheel-dir /usr/src/app/wheels -r requirements.txt \
    && python -m compileall src/ config/ tests/

# =============================================================================
# Stage 2: Runtime - Minimal production image
# =============================================================================
FROM python:3.11-slim

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

WORKDIR /app/src

# Copy wheels from builder and install
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --no-cache /wheels/* \
    && rm -rf /wheels

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser tests/ ./tests/

# Set environment variables
ENV DJANGO_SETTINGS_MODULE=config.settings.production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Collect static files (required for production)
RUN python manage.py collectstatic --noinput --clear || true

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1

# Production WSGI server with optimized settings for ERP workload
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--threads", "2", \
     "--worker-class", "sync", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--capture-output", \
     "config.wsgi:application"]
