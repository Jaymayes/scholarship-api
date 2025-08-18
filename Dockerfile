# Multi-stage Dockerfile for production deployment
# Builder stage: install dependencies and compile wheels
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install uv for faster package management
RUN pip install uv

# Install dependencies and create wheels
RUN uv pip install --system --no-cache-dir -r uv.lock

# Runtime stage: minimal production image
FROM python:3.11-slim as runtime

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# QA-008 fix: Copy only necessary application files (not entire context)
# Copy application source directories explicitly (leveraging .dockerignore)
COPY config/ ./config/
COPY database/ ./database/
COPY middleware/ ./middleware/
COPY models/ ./models/
COPY routers/ ./routers/
COPY schemas/ ./schemas/
COPY services/ ./services/
COPY utils/ ./utils/
COPY observability/ ./observability/
COPY static/ ./static/
COPY main.py ./
COPY gunicorn_conf.py ./

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/tmp \
    && chown -R appuser:appuser /app

# Copy startup scripts
COPY scripts/prestart.sh scripts/start.sh ./
RUN chmod +x prestart.sh start.sh \
    && chown appuser:appuser prestart.sh start.sh

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/healthz || exit 1

# Expose port (configurable via environment)
EXPOSE ${PORT:-8000}

# Default startup command
CMD ["./start.sh"]