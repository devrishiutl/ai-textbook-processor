# AI Textbook Processor

An AI-powered system that extracts text from PDFs and images, then generates educational content like study notes, fill-in-the-blanks, and Q&A sections.

## Features

- 📄 **PDF Processing**: Extract text using Apache Tika
- 🖼️ **Image Processing**: Extract text using Azure Vision AI
- ✅ **Content Validation**: Check appropriateness and relevance
- 📚 **Educational Content**: Generate study materials
- 🔍 **Token Tracking**: Monitor API usage and costs
- 🐳 **Docker Support**: Easy deployment

## Getting Started

### Step 1: Setup Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your Azure OpenAI credentials
 
      # Add your Azure OpenAI environment variables here or in .env file
      # AZURE_OPENAI_API_KEY=your_api_key
      # AZURE_OPENAI_ENDPOINT=your_endpoint
      # AZURE_DEPLOYMENT_NAME=your_deployment_name
      # LANGSMITH_API_KEY=your_langsmith_key
      # LANGSMITH_PROJECT=your_project_name

      # AZURE_OPENAI_API_KEY=
      # AZURE_OPENAI_API_BASE=
      # AZURE_OPENAI_API_VERSION=
      # AZURE_OPENAI_DEPLOYMENT_NAME=
      # LANG_SMITH_KEY=
      # LANGSMITH_API_KEY=
```

### Step 2: Start Services
```bash
# Option A: Local setup
# Download and start Tika server (in separate terminal)
wget https://dlcdn.apache.org/tika/3.2.0/tika-server-standard-3.2.0.jar
java -jar tika-server-standard-3.2.0.jar --host 0.0.0.0 --port 8004

# Start application
python main.py

# Option B: Docker setup (recommended)
docker-compose up --build
```

### Step 3: Access API
- **API Docs**: http://localhost:8003/docs

## API Usage

### Process PDF
```bash
curl -X POST "http://localhost:8003/api/process-json" \
  -F "standard=Class 12" \
  -F "subject=Physics" \
  -F "chapter=Semiconductor" \
  -F "content_type=pdf" \
  -F "pdf_file=@document.pdf"
```

### Process Images
```bash
curl -X POST "http://localhost:8003/api/process-json" \
  -F "standard=Class 12" \
  -F "subject=Physics" \
  -F "chapter=Semiconductor" \
  -F "content_type=images" \
  -F "files=@image1.png" \
  -F "files=@image2.png"
```

## Response Format

```json
{
  "success": true,
  "content": {
    "importantNotes": "# Study Notes\n\nComprehensive notes...",
    "fillInTheBlanks": {
      "questions": {"1": "Question 1", "2": "Question 2"},
      "answers": {"1": "answer1", "2": "answer2"}
    },
    "matchTheFollowing": {
      "column_a": {"1": "Term 1", "2": "Term 2"},
      "column_b": {"A": "Definition A", "B": "Definition B"},
      "answers": {"1": "A", "2": "B"}
    },
    "questionAnswer": {
      "questions": {"Q1": "Question 1?", "Q2": "Question 2?"},
      "answers": {"Q1": "Answer 1", "Q2": "Answer 2"}
    }
  },
  "validation_result": {
    "grade_check": "APPROPRIATE",
    "safety_check": "APPROPRIATE",
    "relevance_check": "MATCH"
  }
}
```

## Configuration

### Environment Variables
| Variable | Description |
|----------|-------------|
| `AZURE_ENDPOINT` | Azure OpenAI endpoint URL |
| `AZURE_API_KEY` | Azure OpenAI API key |
| `AZURE_DEPLOYMENT_NAME` | Model deployment name |

### Optional
| Variable | Description |
|----------|-------------|
| `LANGSMITH_API_KEY` | LangSmith API key |
| `LANGSMITH_PROJECT` | LangSmith project name |

## Access Points

- **API Documentation**: http://localhost:8003/docs
- **API Endpoint**: http://localhost:8003/api/process-json
- **Health Check**: http://localhost:8003/docs

## Token Tracking

The application logs token usage for cost monitoring:
```
Vision processing tokens - Input: 433653, Output: 1324, Total: 434977
Total tokens generated for 17 images: 434977
```

## Project Structure

```
ai-textbook-processor/
├── main.py                    # FastAPI application
├── agents/                    # LangGraph workflow
├── routes/                    # API routes
├── utils/                     # File processing
├── config/                    # Configuration
├── logs/                      # Application logs
├── docker-compose.yml         # Docker setup
└── requirements.txt           # Dependencies
```

## Support

- Check logs in `logs/` directory
- Review API docs at `http://localhost:8003/docs`
- Monitor LangSmith traces for debugging
