# Multi-stage Production Dockerfile for ERP-SOLUTION
# Optimized for Django 4.2+ with PostgreSQL + Redis + Celery
#
# Stage names: the builder stage is named "builder"; the final runtime stage
# is named "production" so `docker build --target production` (used by CI)
# resolves correctly. With a single final stage, building without --target
# still ends in this same image.

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

# Install Python dependencies and compile bytecode.
# NOTE: only requirements.txt is copied into the builder, so there are no
# src/, config/ or tests/ directories here — compiling them silently did
# nothing (compileall exits 0 even when paths are missing). Bytecode is now
# compiled in the runtime stage after the code has been copied in.
RUN pip wheel --no-cache-dir --wheel-dir /usr/src/app/wheels -r requirements.txt

# =============================================================================
# Stage 2: Runtime ("production") - Minimal production image
# =============================================================================
FROM python:3.11-slim AS production

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

# NOTE: WORKDIR must be /app (repo root layout), not /app/src. The COPY
# commands below place src/, config/ and tests/ as siblings under /app,
# which is what `import config.settings...` requires. Previously the code
# ended up at /app/src/src/ and every management command silently failed.
WORKDIR /app

# Copy wheels from builder and install
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --no-cache /wheels/* \
    && rm -rf /wheels

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser trigger_config.yaml ./

# Compile bytecode for the copied code (moved here from the builder stage,
# which never had the source files available). PYTHONDONTWRITEBYTECODE only
# affects runtime imports, not this explicit step.
RUN python -m compileall -q src/ config/

# Set environment variables
ENV DJANGO_SETTINGS_MODULE=config.settings.production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Collect static files (required for production). manage.py lives in src/;
# it adds the repo root to sys.path so `config.settings.production` imports.
RUN python src/manage.py collectstatic --noinput --clear

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
