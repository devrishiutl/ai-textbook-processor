# AI Textbook Processor

A modular, AI-powered educational content processing system that extracts, validates, and generates educational materials from PDFs and images.

## 🏗️ Architecture

The project follows a clean, modular architecture with clear separation of concerns:

```
ai-textbook-processor/
├── agent/                    # LangGraph Studio integration
│   ├── app.py               # Studio entry point
│   ├── graph.py             # Pure LangGraph workflow
│   └── langgraph.json       # Studio configuration
├── core/                    # Core business logic
│   ├── tools.py             # LLM functions only
│   ├── helpers.py           # Utility functions
│   ├── extractors.py        # Content extraction
│   ├── validators.py        # Validation functions
│   └── generators.py        # Content generation
├── models/                  # Data models
│   ├── schemas.py           # Pydantic models
│   └── state.py             # LangGraph state
├── services/                # Business services
│   ├── pdf_service.py       # PDF processing
│   ├── image_service.py     # Image processing
│   └── content_service.py   # Main processing service
├── api/                     # API layer
│   ├── routes.py            # FastAPI routes
│   └── server.py            # Minimal server
├── config/                  # Configuration
│   ├── settings.py          # App settings
│   └── logging.py           # Logging config
├── utils/                   # Utilities
│   ├── parsers.py           # Content parsing
│   └── formatters.py        # Output formatting
├── graph.py                 # Clean LangGraph workflow
└── main.py                  # Minimal entry point
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd ai-textbook-processor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file:

```env
AZURE_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_API_KEY=your-api-key
AZURE_DEPLOYMENT_NAME=gpt-4
LOG_LEVEL=INFO
```

### 3. Run the Application

#### Option A: Direct Processing
```bash
python main.py
```

#### Option B: API Server
```bash
uvicorn api.server:app --host 0.0.0.0 --port 8000
```

#### Option C: LangGraph Studio
```bash
cd agent
langgraph dev
```

## 📋 Features

### ✅ Content Processing
- **PDF Text Extraction**: Extract text from PDF files using Tika
- **Image Processing**: Process images with vision AI
- **Single Source Only**: Process either images OR PDF (not mixed sources)

### ✅ Content Validation
- **Grade Level Check**: Ensure content is appropriate for target grade
- **Safety Analysis**: Verify content is safe for students
- **Relevance Check**: Confirm content matches subject/chapter

### ✅ Educational Content Generation
- **Study Notes**: Comprehensive study materials
- **Fill-in-the-Blanks**: Interactive exercises
- **Match-the-Following**: Matching exercises
- **Subjective Q&A**: Thought-provoking questions

### ✅ API Endpoints
- `POST /api/v1/process`: Process files (PDF/images)
- `POST /api/v1/process-text`: Process text content
- `GET /api/v1/health`: Health check

## 🔧 Usage Examples

### Direct API Call
```python
from services.content_service import ContentProcessingService

service = ContentProcessingService()

# Process PDF only
result = service.process_content(
    standard="Class 10",
    subject="Mathematics",
    chapter="Algebra",
    pdf_path="math_chapter.pdf"
)

# OR process images only
result = service.process_content(
    standard="Class 10",
    subject="Mathematics",
    chapter="Algebra",
    image_paths=["image1.jpg", "image2.png"]
)
```

### API Endpoint
```bash
# Process PDF only
curl -X POST "http://localhost:8000/api/v1/process" \
  -F "standard=Class 10" \
  -F "subject=Mathematics" \
  -F "chapter=Algebra" \
  -F "pdf_file=@math_chapter.pdf"

# OR process images only
curl -X POST "http://localhost:8000/api/v1/process" \
  -F "standard=Class 10" \
  -F "subject=Mathematics" \
  -F "chapter=Algebra" \
  -F "image_files=@image1.jpg" \
  -F "image_files=@image2.png"
```

### LangGraph Workflow
```python
from graph import workflow

# Create initial state
state = {
    "messages": [
        {"role": "system", "content": "You are an educational content processor..."},
        {"role": "user", "content": "Educational content to process: ..."}
    ],
    "processing_steps": []
}

# Run workflow
result = workflow.invoke(state)
```

## 🏛️ Architecture Principles

### 1. **Single Responsibility**
- Each file has one clear purpose
- `tools.py` contains only LLM functions
- `helpers.py` contains only utility functions
- `graph.py` contains only LangGraph workflow

### 2. **Separation of Concerns**
- **Core**: Business logic and LLM interactions
- **Services**: File processing and content management
- **API**: HTTP interface and request handling
- **Models**: Data validation and state management

### 3. **Modularity**
- Easy to test individual components
- Simple to extend with new features
- Clear dependencies between modules

### 4. **Clean Code**
- Minimal `main.py` - just entry point
- Descriptive function names
- Comprehensive error handling
- Proper logging throughout

## 🧪 Testing

```bash
# Run tests
pytest

# Format code
black .

# Lint code
flake8 .
```

## 📊 Monitoring

The application includes comprehensive logging:
- Token usage tracking for cost monitoring
- Processing step tracking
- Error logging with context
- Performance metrics

## 🔒 Security

- Input validation on all endpoints
- File type validation
- Size limits on uploads
- Secure environment variable handling

## 🚀 Deployment

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
- `AZURE_ENDPOINT`: Azure OpenAI endpoint
- `AZURE_API_KEY`: Azure OpenAI API key
- `AZURE_DEPLOYMENT_NAME`: Model deployment name
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

## 🤝 Contributing

1. Follow the modular architecture
2. Add tests for new features
3. Update documentation
4. Use proper logging
5. Follow PEP 8 style guidelines

## 📄 License

This project is licensed under the MIT License.
