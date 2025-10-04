# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV RUN_MODE=container

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
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
    CMD python -c "import requests; requests.get('https://api.frankfurter.app/latest', timeout=5)" || exit 1

# Expose port (if needed for health checks or monitoring)
EXPOSE 8080

# Set default command
CMD ["python", "ratesync.py"]

# Labels for metadata
LABEL maintainer="RateLock Team"
LABEL description="RateSync Service - Fetches and caches exchange rates"
LABEL version="1.0.0"