FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8

# Install system dependencies
RUN apt-get update && apt-get install -y \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Generate locales
RUN sed -i 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory and set permissions
RUN mkdir -p /app/data /app/backups && \
    chmod 755 /app/data /app/backups

# Create non-root user
RUN useradd -m -u 1000 bitaxe && \
    chown -R bitaxe:bitaxe /app

USER bitaxe

# Health check using our comprehensive health checker
HEALTHCHECK --interval=30s --timeout=30s --start-period=15s --retries=3 \
    CMD python health_check.py --exit-code

# Default command
CMD ["python", "monitor.py"]