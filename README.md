# AI Textbook Processor

A Docker-based AI application for processing and analyzing textbook content using various LLM providers.

## 🚀 Quick Setup

### Prerequisites
- Docker and Docker Compose installed
- API keys for your chosen LLM provider

### 1. Clone the Repository
```bash
git clone <repository-url>
cd ai-textbook-processor
```

### 2. Create Environment File
Create a `.env` file in the project root:

```bash
# Required
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here

# Optional (with defaults)
OPENAI_MODEL=gpt-4o-mini
LANGSMITH_PROJECT=ai-textbook-processor
LANGSMITH_API_KEY=your_langsmith_key_here
SERPER_API_KEY=your_serper_key_here
MISTRAL_API_KEY=your_mistral_key_here
```

### 3. Run the Application
```bash
docker-compose up -d
```

### 4. Verify Installation
```bash
curl http://localhost:8003/health
```

You should see: `{"status":"healthy","message":"AI Textbook Processor is running","version":"1.0.0"}`

## 📋 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | Yes | `openai` | LLM provider (openai/azure) |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model name |
| `LANGSMITH_PROJECT` | No | `ai-textbook-processor` | LangSmith project name |
| `LANGSMITH_API_KEY` | No | - | LangSmith API key for tracing |
| `SERPER_API_KEY` | No | - | Serper API key for web scraping |
| `MISTRAL_API_KEY` | No | - | Mistral AI API key |

## 🛠️ Management Commands

### Start the application
```bash
docker-compose up -d
```

### Stop the application
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f
```

### Restart the application
```bash
docker-compose restart
```

### Rebuild and restart
```bash
docker-compose up -d --build
```

## 🌐 Access Points

- **Health Check**: http://localhost:8003/health
- **API Endpoints**: http://localhost:8003
- **Logs**: Available in `./logs/` directory
- **Database**: Stored in `./chroma_db/` directory

## 📁 Project Structure

```
ai-textbook-processor/
├── agents/           # AI agent implementations
├── config/           # Configuration files
├── routes/           # API route handlers
├── utils/            # Utility functions
├── logs/             # Application logs
├── chroma_db/        # Vector database
├── docker-compose.yml # Docker Compose configuration
├── Dockerfile        # Docker image definition
└── main.py          # Application entry point
```

## 🔧 Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs

# Rebuild container
docker-compose up -d --build
```

### Health check fails
```bash
# Check if port is available
curl http://localhost:8003/health

# Restart container
docker-compose restart
```

### Environment variables not working
```bash
# Verify .env file exists
ls -la .env

# Check environment variables in container
docker-compose exec ai-textbook-processor env
```

## 📝 License

This project is licensed under the MIT License.
