#!/bin/bash

# AI Textbook Processor Docker Build Script
# This script builds and runs the AI textbook processor with proper configuration

set -e

echo "🚀 Building AI Textbook Processor Docker Image..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found. Please create one with your configuration."
    echo "Required environment variables:"
    echo "  - AZURE_OPENAI_API_BASE"
    echo "  - AZURE_OPENAI_API_KEY" 
    echo "  - AZURE_OPENAI_DEPLOYMENT_NAME"
    echo "  - LANGSMITH_API_KEY (optional)"
    echo "  - SERPER_API_KEY (optional)"
    echo ""
fi

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t ai-textbook-processor .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    
    # Ask user if they want to run the container
    read -p "🤔 Do you want to run the container now? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚀 Starting container..."
        
        # Run with docker-compose if available
        if command -v docker-compose &> /dev/null; then
            echo "📋 Using docker-compose..."
            docker-compose up -d
            echo "✅ Container started! Access at http://localhost:8003"
        else
            echo "📋 Using docker run..."
            docker run -d \
                --name ai-textbook-processor \
                -p 8003:8003 \
                --env-file .env \
                -v $(pwd)/logs:/app/logs \
                -v $(pwd)/chroma_db:/app/chroma_db \
                ai-textbook-processor
            echo "✅ Container started! Access at http://localhost:8003"
        fi
    else
        echo "📋 To run the container manually:"
        echo "   docker-compose up -d"
        echo "   or"
        echo "   docker run -d --name ai-textbook-processor -p 8003:8003 --env-file .env ai-textbook-processor"
    fi
else
    echo "❌ Docker build failed!"
    exit 1
fi

echo ""
echo "🎉 Setup complete! Your AI Textbook Processor is ready."
echo "📚 API endpoints available at http://localhost:8003" 