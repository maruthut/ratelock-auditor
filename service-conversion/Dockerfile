# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=conversionengine.py
ENV PORT=8080

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
COPY conversionengine.py .

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash conversion && \
    chown -R conversion:conversion /app
USER conversion

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose the port the app runs on
EXPOSE 8080

# Set default command
CMD ["python", "conversionengine.py"]

# Alternative command for production with Gunicorn
# CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "30", "conversionengine:app"]

# Labels for metadata
LABEL maintainer="RateLock Team"
LABEL description="ConversionEngine Service - High-speed currency conversion API"
LABEL version="1.0.0"