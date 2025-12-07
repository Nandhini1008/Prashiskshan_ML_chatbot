# Multi-stage Dockerfile for Chatbot Service with Nginx
# Production-ready for EC2 deployment - Optimized for smaller image size

# Stage 1: Build Python application
FROM python:3.11-slim as python-app

# Set working directory
WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with optimizations
# Use --no-deps where possible and avoid CUDA dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge && \
    rm -rf /root/.cache/pip /tmp/* /var/tmp/*

# Copy application code (only what's needed)
COPY . .

# Create necessary directories
RUN mkdir -p data/companies data/faqs data/college_docs logs

# Stage 2: Final image with Nginx (minimal)
FROM python:3.11-slim

# Install nginx and supervisor (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# Copy Python application from build stage
WORKDIR /app
COPY --from=python-app /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-app /usr/local/bin /usr/local/bin
COPY --from=python-app /app /app

# Remove unnecessary files to reduce image size
RUN find /usr/local/lib/python3.11/site-packages -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.11/site-packages -type f -name "*.pyc" -delete && \
    find /usr/local/lib/python3.11/site-packages -type f -name "*.pyo" -delete && \
    rm -rf /usr/local/lib/python3.11/site-packages/*/tests 2>/dev/null || true && \
    rm -rf /usr/local/lib/python3.11/site-packages/*/test 2>/dev/null || true

# Copy nginx configuration
COPY nginx.conf /etc/nginx/sites-available/chatbot
RUN ln -sf /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/ && \
    rm -f /etc/nginx/sites-enabled/default

# Create supervisor configuration
RUN mkdir -p /etc/supervisor/conf.d
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create nginx directories and set permissions
RUN mkdir -p /var/log/nginx /var/cache/nginx /var/run && \
    chown -R www-data:www-data /var/log/nginx /var/cache/nginx && \
    chmod -R 755 /var/log/nginx /var/cache/nginx

# Set environment variables
ENV CHATBOT_SERVICE_PORT=5001
ENV CHATBOT_SERVICE_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose ports
EXPOSE 80 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Use supervisor to run both nginx and Flask app
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
