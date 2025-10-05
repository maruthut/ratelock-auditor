# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV RUN_MODE=container
ENV PORT=8081

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ratesync.py .

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash ratesync && \
    chown -R ratesync:ratesync /app
USER ratesync

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Expose port for FastAPI service
EXPOSE 8081

# Run with uvicorn ASGI server
CMD ["uvicorn", "ratesync:app", "--host", "0.0.0.0", "--port", "8081", "--workers", "1"]

# Labels for metadata
LABEL maintainer="RateLock Team"
LABEL description="RateSync Service - FastAPI-based rate fetching and caching service"
LABEL version="2.0.0"