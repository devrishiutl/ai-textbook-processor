# Advanced Textbook AI Agent - Docling Edition

## Prerequisites
- Python 3.8+
- Azure OpenAI API access

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Setup
Create a `.env` file in the project root with your Azure OpenAI credentials:

```env
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_API_BASE=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
```

## Usage

### Process PDF Textbooks (Recommended)
```bash
python main_docling.py --content textbook.pdf --standard "Class 10" --subject "Science" --chapter "Plant Kingdom"
```

### Process Single Image
```bash
python main_docling.py --content diagram.jpg --standard "5th Grade" --subject "Biology" --chapter "Types of Plants" --type images
```

### Process Multiple Images
```bash  
python main_docling.py --content "image1.jpg,image2.png,image3.jpg" --standard "Class 8" --subject "Mathematics" --chapter "Geometry" --type images
```

### Process Text Content
```bash
python main_docling.py --content "Your text content here" --standard "Class 9" --subject "English" --chapter "Grammar" --type text
```

## Why Docling?

### Advanced Document Intelligence
- 🧠 **AI-powered layout understanding** - Recognizes textbook structure
- 📊 **Table extraction with structure** - Preserves relationships
- 🖼️ **Figure-caption relationships** - Maintains context
- 📝 **Educational content categorization** - Identifies key concepts
- 🎯 **Context-aware processing** - Understands learning flow

### Educational Benefits
1. **Better content extraction** from complex textbook layouts
2. **Preserved relationships** between text, images, and captions  
3. **Structured learning materials** that maintain educational context
4. **Higher accuracy** in identifying key concepts and definitions

## What It Generates

The system creates comprehensive educational materials:
1. **Content Safety Analysis** - Appropriateness verification
2. **Study Notes** - Key concepts and definitions highlighted
3. **Fill-in-the-Blanks** - 5 exercises with answers
4. **Match-the-Following** - 5 pairs testing relationships
5. **Subjective Questions** - 3 critical thinking questions with answers

## File Structure
- `main_docling.py` - **Primary script** with Docling intelligence
- `graph.py` - LangGraph educational workflow
- `tools.py` - AI content generation tools  
- `config.py` - Azure OpenAI configuration
- `requirements.txt` - Clean dependency list

## Advanced Features
- ✅ **Semantic document understanding** 
- ✅ **Educational layout recognition**
- ✅ **Multi-modal content processing**
- ✅ **Context-preserved extraction**
- ✅ **Structured educational output** 