# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# No Tika server needed - using Docling for text extraction

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose ports
# EXPOSE 8003 8004
EXPOSE 8003

# Create startup script
RUN echo '#!/bin/bash\n\
# Start the FastAPI application\n\
python main.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# Set the default command
CMD ["/app/start.sh"] 