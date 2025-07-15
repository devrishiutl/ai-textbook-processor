#!/bin/bash

# AI Textbook Processor Docker Build Script
# This script builds and runs the AI textbook processor with proper configuration

set -e

echo "🚀 Building AI Textbook Processor Docker Image..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found. Please create one with your configuration."
    echo "Required environment variables:"
    echo "  # LLM Provider Configuration"
    echo "  - LLM_PROVIDER (azure or openai)"
    echo "  - OPENAI_API_KEY"
    echo "  - OPENAI_MODEL (optional, defaults to gpt-4o-mini)"
    echo "  - LANGSMITH_PROJECT (optional, defaults to ai-textbook-processor)"
    echo "  - LANGSMITH_API_KEY (optional)"
    echo "  - SERPER_API_KEY (optional)"
    echo "  - MISTRAL_API_KEY (optional)"
    echo ""
    echo "Example .env file:"
    echo "  LLM_PROVIDER=openai"
    echo "  OPENAI_API_KEY=your_openai_api_key"
    echo "  OPENAI_MODEL=gpt-4o-mini"
    echo "  LANGSMITH_PROJECT=ai-textbook-processor"
    echo "  LANGSMITH_API_KEY=your_langsmith_key"
    echo "  SERPER_API_KEY=your_serper_key"
    echo "  MISTRAL_API_KEY=your_mistral_key"
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