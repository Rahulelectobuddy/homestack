FROM python:3.11-slim

# Prevent Python from writing pyc files and buffer stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Kolkata

# Install system dependencies required for Playwright & Firefox
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    procps \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 \
    libx11-xcb1 \
    libasound2 \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install shared Python library
COPY libs/common-python /libs/common-python
RUN pip install --no-cache-dir /libs/common-python

# Install Python dependencies
COPY services/apps/bus-scraper/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Firefox browser & system dependencies
RUN playwright install firefox --with-deps

# Copy application source files
COPY services/apps/bus-scraper/src/ .
RUN chmod +x entrypoint.sh

# Create exports and debug directory mounts
RUN mkdir -p /app/exports /app/debug_snapshots

# Volume mount point for exports
VOLUME ["/app/exports"]

ENTRYPOINT ["/app/entrypoint.sh"]

