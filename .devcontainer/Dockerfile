FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}" \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       postgresql-client \
       redis-tools \
       jq \
       curl \
       unzip \
       zip \
       build-essential \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && python -m venv "${VIRTUAL_ENV}" \
    && "${VIRTUAL_ENV}/bin/pip" install --upgrade pip setuptools wheel

COPY requirements.txt /tmp/requirements.txt
RUN "${VIRTUAL_ENV}/bin/pip" install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

USER vscode

WORKDIR /workspaces/ERP-SOLUTION
