# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Set environment variables with defaults from configuration.py and settings.py
ENV LLM_PROVIDER=openai
ENV LANGSMITH_PROJECT=ai-textbook-processor
ENV LANGSMITH_ENDPOINT=https://api.smith.langchain.com
ENV AZURE_OPENAI_API_VERSION=2024-02-15-preview
ENV OPENAI_MODEL=gpt-4o-mini
ENV VALIDATION_TEMPERATURE=0.05
ENV VALIDATION_MAX_TOKENS=200
ENV GENERATION_TEMPERATURE=0.2
ENV GENERATION_MAX_TOKENS=4000
ENV LOG_LEVEL=INFO
ENV IMAGE_TARGET_WIDTH=800
ENV IMAGE_TARGET_HEIGHT=800
ENV IMAGE_QUALITY=85
ENV IMAGE_MAX_TOKENS=3000
ENV IMAGE_TEMPERATURE=0.1
ENV VALIDATION_MAX_CONTENT_LENGTH=1000
ENV GENERATION_MAX_CONTENT_LENGTH=3000
ENV VALIDATION_GRADE_CHECK=APPROPRIATE
ENV VALIDATION_SAFETY_CHECK=APPROPRIATE
ENV VALIDATION_RELEVANCE_CHECK=MATCH

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run the application
CMD ["python", "main.py"] 