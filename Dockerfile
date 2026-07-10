# ======================================================================================
# SECURE MULTI-STAGE DOCKERFILE FOR WARREN BOT
#
# Base: Chainguard distroless Python (minimal CVEs, non-root by default, no shell in
# the runtime layer). All shell/pip work happens in the `-dev` build stages; the final
# runtime stage only COPYs the built virtualenv and runs as the nonroot user (65532),
# matching docker-compose.secure.yml.
# ======================================================================================

# Base images as build args so they can be pinned to immutable digests in one place, e.g.:
#   --build-arg PYTHON_DEV_IMAGE=chainguard/python@sha256:<dev-digest>
#   --build-arg PYTHON_RUNTIME_IMAGE=chainguard/python@sha256:<runtime-digest>
# builder/installer MUST match the runtime Python minor version, or the venv's compiled
# wheels (numpy/pandas/scipy) won't import in the runtime stage. Pinning by digest guarantees
# that and makes builds reproducible; the floating :latest defaults are convenient but not.
ARG PYTHON_DEV_IMAGE=chainguard/python:latest-dev
ARG PYTHON_RUNTIME_IMAGE=chainguard/python:latest

# ------------------------------------------------------------------------------------------
# BUILD STAGE — export the locked deps and compile the project into a wheel
# ------------------------------------------------------------------------------------------
FROM ${PYTHON_DEV_IMAGE} AS builder

# Reproducible, quiet, no-bytecode builds
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Poetry pinned for reproducibility (root only for build tooling; stage is discarded).
USER root
RUN pip install --no-cache-dir poetry==2.1.0

WORKDIR /build

# Preserve the src/ layout so poetry-core discovers the warren_bot package correctly
COPY pyproject.toml poetry.lock README.md ./
COPY src/ ./src/

RUN poetry build --format wheel

# ------------------------------------------------------------------------------------------
# INSTALLER STAGE — install the wheel into a self-contained virtualenv
# ------------------------------------------------------------------------------------------
FROM ${PYTHON_DEV_IMAGE} AS installer

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/app/.venv/bin:$PATH"

USER root
WORKDIR /app

# Build the venv and install the wheel. pip resolves the wheel's dependencies to current
# wheels for this interpreter (cp313) — poetry's lock resolver backtracks this graph to
# pre-3.13 versions that have no cp313 wheels, so pip's fresh resolution is used here.
# The *.whl glob decouples this stage from the project version (no WARREN_VERSION coupling).
RUN python -m venv --copies .venv
COPY --from=builder /build/dist/*.whl ./
RUN pip install --no-cache-dir ./*.whl \
    && rm ./*.whl \
    && python -c "import warren_bot; print('Warren Bot installed successfully')"

# ------------------------------------------------------------------------------------------
# RUNTIME STAGE — distroless, non-root, no shell. Only COPY + metadata here.
# ------------------------------------------------------------------------------------------
FROM ${PYTHON_RUNTIME_IMAGE} AS runtime

ARG WARREN_VERSION="0.1.0"
ARG BUILD_DATE
ARG VCS_REF

LABEL maintainer="J.A. Simmons V <simmonsj@jasimmonsv.com>" \
      org.opencontainers.image.title="Warren Bot" \
      org.opencontainers.image.description="Secure Discord Investment Club Chatbot" \
      org.opencontainers.image.version="${WARREN_VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="Cypress Investment Club" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.url="https://github.com/CyIC/warren_bot" \
      org.opencontainers.image.documentation="https://github.com/CyIC/warren_bot/blob/main/README.md" \
      org.opencontainers.image.source="https://github.com/CyIC/warren_bot" \
      security.scan.policy="required" \
      security.non-root="true"

WORKDIR /app

# Copy the ready-to-run virtualenv, owned by the nonroot runtime user
COPY --from=installer --chown=nonroot:nonroot /app/.venv /app/.venv

# Minimal runtime environment. No PYTHONPATH: the venv on PATH resolves its own
# site-packages, so this stays correct even if the base Python minor version changes.
# WARREN_DATA_DIR is where the bot writes charts/pickles/reports (a writable mounted volume
# on the read-only root); HOME and MPLCONFIGDIR point at tmpfs so matplotlib/yfinance caches
# don't hit the read-only filesystem.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    HOME="/tmp" \
    MPLCONFIGDIR="/tmp" \
    WARREN_DATA_DIR="/app/data"

# Run as the Chainguard nonroot user (uid 65532; matches docker-compose.secure.yml)
USER nonroot

# Run via the venv interpreter explicitly. The base image's ENTRYPOINT is the system python
# (/usr/bin/python), which lacks the app; resetting ENTRYPOINT to the venv python ensures
# `warren_bot` is importable. Exec form works without a shell in the distroless image.
ENTRYPOINT ["/app/.venv/bin/python"]
CMD ["-m", "warren_bot"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD ["/app/.venv/bin/python", "-c", "import warren_bot, sys; sys.exit(0)"]

STOPSIGNAL SIGTERM
