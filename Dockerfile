# Multi-stage Dockerfile for Chatbot Service with Nginx
# Production-ready for EC2 deployment

# Stage 1: Build Python application
FROM python:3.11-slim as python-app

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/companies data/faqs data/college_docs logs

# Stage 2: Final image with Nginx
FROM python:3.11-slim

# Install nginx and supervisor
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python application from build stage
WORKDIR /app
COPY --from=python-app /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-app /usr/local/bin /usr/local/bin
COPY --from=python-app /app /app

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
# Port 80 for nginx (external)
# Port 5001 for direct Flask access (internal)
EXPOSE 80 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Use supervisor to run both nginx and Flask app
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
