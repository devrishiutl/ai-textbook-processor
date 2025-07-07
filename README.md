# Simple Educational Content Processor

A clean, simple AI-powered educational content processing system.

## 📁 File Structure

```
ai-textbook-processor/
├── main.py                    # uvicorn api start
├── agents/
│   ├── graph.py              # contains functions which returns graph
│   ├── nodes.py              # contains all graph nodes and tools for graph
│   └── helper.py             # contains all agent specific non tool function
├── routes/
│   └── route.py              # contains all api routes
├── utils/
│   └── utility.py            # contains all non intelligent functions
├── logs/                     # contains logs
├── config/
│   └── configuration.py      # singleton design pattern, config variables, LLM connections
└── requirements.txt
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create `.env` file:
```env
AZURE_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_API_KEY=your-api-key
AZURE_DEPLOYMENT_NAME=gpt-4
```

### 3. Run Application
```bash
python main.py
```

## 🔄 Simple Flow

1. **Get files/data** → Upload PDF or images with standard, subject, chapter
2. **Extract content** → `read_data_from_file()` or `read_data_from_image()`
3. **Invoke graph** → 2 nodes: validate_content → generate_content
4. **Return response** → JSON with generated educational content

## 📋 API Usage

### Process Content
```bash
curl -X POST "http://localhost:8000/process" \
  -F "standard=10th" \
  -F "subject=Mathematics" \
  -F "chapter=Algebra" \
  -F "pdf_file=@document.pdf"
```

### Response Format
```json
{
  "success": true,
  "content": "Generated educational content...",
  "metadata": {
    "standard": "10th",
    "subject": "Mathematics", 
    "chapter": "Algebra"
  }
}
```

## 🏗️ Architecture

### **2 Simple Nodes:**
- **validate_content**: Check content validity
- **generate_content**: Create educational materials

### **Simple Functions:**
- `read_data_from_file(pdf)` → string
- `read_data_from_image(list[image])` → string

### **Clean Flow:**
1. Extract content from files
2. Validate content
3. Generate educational content
4. Return response

## ✅ Features

- ✅ **Simple & Clean**: Minimal code, clear structure
- ✅ **Single Source**: PDF OR Images (no mixing)
- ✅ **2 Nodes Only**: validate_content → generate_content
- ✅ **Fast Processing**: Direct file reading
- ✅ **Error Handling**: Simple error responses
- ✅ **Singleton Config**: Efficient LLM management

## 🔧 Configuration

The `config/configuration.py` uses singleton pattern to:
- Load environment variables
- Initialize LLM connections once
- Manage configuration globally

## 📊 Logging

Logs are stored in the `logs/` directory for monitoring and debugging.
