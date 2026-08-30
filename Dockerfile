# =============================================================================
# Enterprise ERP Solution - Production Dockerfile
# Multi-stage build for optimized production deployment
# Target Environment: Docker Hub
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Base Python Image
# -----------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS base

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

# Install system dependencies required for ERP application
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Database clients
    postgresql-client \
    # Redis tools for caching
    redis-tools \
    # Build essentials for compiling packages
    build-essential \
    libpq-dev \
    # Utilities
    curl \
    jq \
    git \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# -----------------------------------------------------------------------------
# Stage 2: Dependencies Installation
# -----------------------------------------------------------------------------
FROM base AS dependencies

# Copy requirements first for better layer caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv ${VIRTUAL_ENV} && \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 3: Build Stage (for any compilation/assets if needed)
# -----------------------------------------------------------------------------
FROM dependencies AS build

# Copy application source code
COPY src/ ./src/
COPY config/ ./config/

# Set Django settings module for collection
ENV DJANGO_SETTINGS_MODULE=config.settings.production

# Collect static files (Django specific)
RUN mkdir -p /app/staticfiles && \
    cd src && python manage.py collectstatic --noinput || true

# -----------------------------------------------------------------------------
# Stage 4: Production Runtime
# -----------------------------------------------------------------------------
FROM base AS production

# Labels for image metadata
LABEL maintainer="ERP Solutions Team" \
      version="1.0.0" \
      description="Enterprise Resource Planning Solution - Production Container" \
      org.opencontainers.image.source="https://github.com/nyeinpyaesone-ui/ERP-SOLUTION" \
      org.opencontainers.image.description="Enterprise ERP System for business operations"

# Copy virtual environment from dependencies stage
COPY --from=dependencies /opt/venv /opt/venv

# Copy application code from build stage
COPY --from=build /app/src ./src
COPY --from=build /app/config ./config
COPY --from=build /app/staticfiles ./staticfiles

# Copy additional configuration files
COPY scripts/ ./scripts/
COPY docs/ ./docs/

# Create entrypoint script
RUN printf '#!/bin/bash\n\
set -e\n\
\n\
# Wait for database to be ready (if POSTGRES_HOST is set)\n\
if [ ! -z "${POSTGRES_HOST}" ]; then\n\
    echo "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}..."\n\
    while ! nc -z ${POSTGRES_HOST} ${POSTGRES_PORT:-5432}; do\n\
        sleep 0.1\n\
    done\n\
    echo "PostgreSQL is available"\n\
fi\n\
\n\
# Run database migrations\n\
echo "Running database migrations..."\n\
cd src && python manage.py migrate --noinput || true\n\
\n\
# Collect static files again to ensure they'\''re up to date\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput || true\n\
\n\
# Execute the main command\n\
exec "$@"' > /entrypoint.sh && chmod +x /entrypoint.sh

# Change ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose application port (default Django port)
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default command - can be overridden in docker-compose or k8s
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "config.wsgi:application"]

# -----------------------------------------------------------------------------
# Stage 5: Development Image (optional, for local development)
# -----------------------------------------------------------------------------
FROM dependencies AS development

# Install development dependencies
RUN pip install ipython django-extensions Werkzeug

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY tests/ ./tests/
COPY pytest.ini .
COPY setup.cfg .

# Expose port for development server
EXPOSE 8000

# Default command for development
CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"]
