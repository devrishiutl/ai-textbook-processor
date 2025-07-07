# API Response Structure Documentation

## Centralized Response Structure

All API endpoints return responses with the same structure, defined in `models/schemas.py`.

### Success Response Structure
```json
{
    "success": true,
    "message": "Educational content processed successfully",
    "content": {
        "importantNotes": "Study notes content with markdown formatting...",
        "fillInTheBlanks": {
            "questions": { "1": "Question 1", ... },
            "answers": { "1": "Answer 1", ... }
        },
        "matchTheFollowing": {
            "column_a": { "1": "Term 1", ... },
            "column_b": { "A": "Definition A", ... },
            "answers": { "1": "A", ... }
        },
        "questionAnswer": {
            "questions": { "Q1": "Question 1", ... },
            "answers": { "Q1": "Answer 1", ... }
        }
    },
    "metadata": {
        "standard": "Class 6",
        "subject": "science",
        "chapter": "science world",
        "content_type": "pdf",
        "files_processed": 1,
        "validation_details": {
            "grade_check": "APPROPRIATE",
            "safety_check": "APPROPRIATE",
            "relevance_check": "MATCH",
            "reason": "Validation reason...",
            "overall_status": "PASSED",
            "content_length": 11040,
            "target_standard": "Class 6",
            "subject": "science",
            "chapter": "science world"
        }
    }
}
```

### Failure Response Structure
```json
{
    "success": false,
    "message": "Processing failed",
    "content": {},
    "metadata": {
        "standard": "Class 12",
        "subject": "science",
        "chapter": "science world",
        "content_type": "pdf",
        "files_processed": 1,
        "validation_details": {
            "grade_check": "UNKNOWN",
            "safety_check": "UNKNOWN",
            "relevance_check": "UNKNOWN",
            "reason": "Error message here",
            "overall_status": "FAILED",
            "content_length": 0,
            "target_standard": "Class 12",
            "subject": "science",
            "chapter": "science world"
        }
    }
}
```

## Usage

### Creating Success Responses
```python
from models.schemas import create_success_response

metadata = {
    "standard": "Class 6",
    "subject": "science",
    "chapter": "science world",
    "content_type": "pdf",
    "files_processed": 1,
    "validation_details": {...}
}

response = create_success_response(content_data, metadata)
```

### Creating Failure Responses
```python
from models.schemas import create_failure_response

metadata = {
    "standard": "Class 6",
    "subject": "science",
    "chapter": "science world",
    "content_type": "pdf",
    "files_processed": 1
}

response = create_failure_response("Error message", metadata)
```

## Benefits

✅ **Consistent Structure** - All responses follow the same format  
✅ **Single Source of Truth** - Structure defined in one place  
✅ **Easy Maintenance** - Changes only need to be made in schemas.py  
✅ **Type Safety** - Pydantic models ensure structure compliance  
✅ **Documentation** - Clear structure for frontend developers  

## Field Descriptions

- `success`: Boolean indicating if processing succeeded
- `message`: Human-readable status message
- `content`: Generated educational content (empty dict if failed)
  - `importantNotes`: Study notes with markdown formatting (bold, headings, lists, etc.)
  - `fillInTheBlanks`: Fill-in-the-blank exercises with questions and answers
  - `matchTheFollowing`: Matching exercises with terms and definitions
  - `questionAnswer`: Q&A exercises with questions and detailed answers
- `metadata`: Processing information and validation results
- `validation_details`: Detailed validation results with consistent fields

## Markdown Formatting in Notes

The `importantNotes` field contains study notes with rich markdown formatting:

- **Bold text** (`**text**`) for important terms and key concepts
- **Headings** (`##` and `###`) for organizing topics and subtopics
- **Bullet points** (`-`) for lists and key points
- **Numbered lists** (`1. 2. 3.`) for steps and sequences
- **Italic text** (`*text*`) for emphasis and examples
- **Code blocks** (`` `text` ``) for formulas and technical terms
- **Blockquotes** (`>`) for important notes and warnings 