# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openjdk-11-jre-headless \
    curl \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set Java environment
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$PATH:$JAVA_HOME/bin

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download and setup Apache Tika
RUN wget https://archive.apache.org/dist/tika/tika-server-2.8.0.jar -O /app/tika-server.jar

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose ports
EXPOSE 8003 8004

# Create startup script
RUN echo '#!/bin/bash\n\
# Start Tika server in background\n\
java -jar /app/tika-server.jar --host 0.0.0.0 --port 8004 &\n\
\n\
# Wait for Tika to start\n\
echo "Waiting for Tika server to start..."\n\
while ! curl -s http://localhost:8004/tika > /dev/null; do\n\
    sleep 1\n\
done\n\
echo "Tika server is ready!"\n\
\n\
# Start the FastAPI application\n\
python main.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# Set the default command
CMD ["/app/start.sh"] 