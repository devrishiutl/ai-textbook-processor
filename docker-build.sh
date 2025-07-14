#!/bin/bash

# AI Textbook Processor Docker Build Script

echo "🚀 Building AI Textbook Processor Docker Image..."

# Build the Docker image
docker build -t ai-textbook-processor .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    echo ""
    echo "📋 Available commands:"
    echo "   Run with Docker Compose (recommended):"
    echo "   docker-compose up -d"
    echo ""
    echo "   Run directly with Docker:"
    echo "   docker run -p 8003:8003 ai-textbook-processor"
    echo ""
    echo "   Stop the application:"
    echo "   docker-compose down"
    echo ""
    echo "   View logs:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🌐 Application will be available at:"
    echo "   - FastAPI: http://localhost:8003"
    echo "   - API Docs: http://localhost:8003/docs"
#    echo "   - Tika Server: http://localhost:8004"
    echo ""
    echo "⚠️  Remember to set your environment variables in docker-compose.yml"
else
    echo "❌ Docker build failed!"
    exit 1
fi 