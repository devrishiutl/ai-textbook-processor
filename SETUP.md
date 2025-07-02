# AI Textbook Processor - Complete Setup Guide

## Overview
The AI Textbook Processor is an advanced educational content processing system that extracts and generates comprehensive study materials from PDF textbooks and images. It uses a smart extraction approach with Tika (fast) and Docling (advanced) as fallback.

## Prerequisites
- Python 3.8+
- Java 8+ (for Tika server)
- Azure OpenAI API access
- Git

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd ai-textbook-processor
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download Tika Server
Download the Tika server JAR file:
```bash
# Option 1: Download from Apache Tika
wget https://archive.apache.org/dist/tika/tika-server-standard-3.2.0.jar

# Option 2: Download from Maven Central
wget https://repo1.maven.org/maven2/org/apache/tika/tika-server-standard/3.2.0/tika-server-standard-3.2.0.jar
```

### 5. Environment Setup
Create a `.env` file in the project root:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_API_BASE=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name

# LangSmith Tracing (Optional)
LANG_SMITH_KEY=your_langsmith_key_here
LANGSMITH_PROJECT=ai-textbook-processor
```

## Running the System

### 1. Start Tika Server
```bash
java -jar tika-server-standard-3.2.0.jar --port 8004
```
Keep this running in a separate terminal. The server will be available at `http://localhost:8004`.

### 2. Start the API Server
```bash
python main.py
```
The API will be available at `http://localhost:8000`.

### 3. Test the System
```bash
# Test Tika extraction
python tika_extractor.py /path/to/your/test.pdf

# Test the full pipeline
curl -X POST "http://localhost:8000/process-json" \
  -F "standard=Class 12" \
  -F "subject=Physics" \
  -F "chapter=Semiconductor Electronics" \
  -F "content_type=pdf" \
  -F "files=@/path/to/your/textbook.pdf"
```

## System Architecture

### Smart PDF Extraction
- **Primary**: Tika (fast, reliable, ~9 seconds for 2.8MB PDF)
- **Fallback**: Docling (advanced features, ~130 seconds for complex PDFs)
- **Automatic**: System chooses the best method based on content quality

### Content Processing Pipeline
1. **Content Extraction** - Smart PDF/image extraction
2. **Validation** - Grade level, safety, and relevance checks
3. **Content Generation** - Study materials creation
4. **Structured Output** - Parsed educational content

### Generated Content
- **Study Notes** - Key concepts and definitions
- **Fill-in-the-Blanks** - 5 exercises with answers
- **Match-the-Following** - 5 pairs testing relationships
- **Subjective Questions** - 3 critical thinking questions with answers

## API Endpoints

### Streaming Endpoint
```bash
POST /process-stream
```
Returns real-time progress updates and structured content.

### JSON Endpoint
```bash
POST /process-json
```
Returns complete structured response in JSON format.

### Parameters
- `standard` - Grade level (e.g., "Class 12")
- `subject` - Subject name (e.g., "Physics")
- `chapter` - Chapter name (e.g., "Semiconductor Electronics")
- `content_type` - "pdf" or "images"
- `files` - Upload file(s)
- `text_content` - Direct text input (optional)

## File Structure
```
ai-textbook-processor/
├── main.py              # FastAPI server and endpoints
├── tools.py             # Core processing functions
├── tika_extractor.py    # Tika PDF extraction module
├── parsers.py           # Content parsing and structuring
├── models.py            # Pydantic data models
├── config.py            # Configuration and Azure setup
├── graph.py             # LangGraph workflow
├── requirements.txt     # Python dependencies
├── SETUP.md            # This file
└── README.md           # Project overview
```

## Dependencies

### Core Dependencies
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `openai` - Azure OpenAI client
- `langchain` - LLM framework
- `langgraph` - Workflow orchestration
- `pillow` - Image processing
- `python-multipart` - File uploads
- `requests` - HTTP client
- `python-dotenv` - Environment management

### PDF Processing
- `docling` - Advanced PDF extraction
- `tika-server` - Fast PDF extraction (Java-based)

### Optional
- `langsmith` - Tracing and monitoring
- `reportlab` - PDF generation

## Troubleshooting

### Tika Server Issues
```bash
# Check if Tika server is running
curl http://localhost:8004/tika

# Restart Tika server
java -jar tika-server-standard-3.2.0.jar --port 8004 --host 0.0.0.0
```

### Memory Issues
```bash
# Increase Java heap size for Tika
java -Xmx2g -jar tika-server-standard-3.2.0.jar --port 8004
```

### Python Environment Issues
```bash
# Reinstall dependencies
pip uninstall -r requirements.txt
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.8+
```

### Azure OpenAI Issues
- Verify API key and endpoint in `.env`
- Check deployment name matches Azure portal
- Ensure API version is correct

## Performance

### Extraction Speed
- **Tika**: ~9 seconds for 2.8MB PDF
- **Docling**: ~130 seconds for complex PDFs
- **Smart Selection**: Automatically chooses fastest method

### Content Quality
- **Tika**: Good text extraction, fast processing
- **Docling**: Advanced layout understanding, comprehensive extraction
- **Fallback**: Ensures content is always extracted

## Development

### Adding New Features
1. Add functions to `tools.py`
2. Update `models.py` for new data structures
3. Modify `parsers.py` for new content types
4. Update API endpoints in `main.py`

### Testing
```bash
# Test individual components
python tika_extractor.py test.pdf
python -c "from tools import extract_pdf_content; print(extract_pdf_content('test.pdf'))"
```

## Support
For issues and questions:
1. Check the troubleshooting section
2. Review logs in the terminal
3. Verify all dependencies are installed
4. Ensure Tika server is running

## License
This project is licensed under the MIT License. 