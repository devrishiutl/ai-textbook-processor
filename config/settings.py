"""
Application Settings - Only includes settings actually used in the codebase
"""
import os
from dotenv import load_dotenv
from typing import Tuple, Dict

load_dotenv()

# ===== CORE APPLICATION SETTINGS =====

# Logging Configuration (used in config/logging.py)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# File Validation Settings (used in routes/route.py)
SUPPORTED_PDF_EXTENSION = ".pdf"  # Used in route.py for PDF validation

# ===== IMAGE PROCESSING SETTINGS =====
# Used in utils/utility.py

IMAGE_TARGET_SIZE: Tuple[int, int] = (
    int(os.getenv("IMAGE_TARGET_WIDTH", "800")),
    int(os.getenv("IMAGE_TARGET_HEIGHT", "800"))
)
IMAGE_QUALITY = int(os.getenv("IMAGE_QUALITY", "85"))
IMAGE_MAX_TOKENS = int(os.getenv("IMAGE_MAX_TOKENS", "3000"))
IMAGE_TEMPERATURE = float(os.getenv("IMAGE_TEMPERATURE", "0.1"))

# ===== VISION AI PROMPTS =====
# Used in utils/utility.py

VISION_SYSTEM_PROMPT = os.getenv("VISION_SYSTEM_PROMPT", (
    "You are a text transcription tool. Your job is to extract and transcribe "
    "ONLY the actual text and content visible in the images. Do not interpret, "
    "explain, or add any generated content. Simply transcribe what you can clearly see and read."
))

VISION_USER_PROMPT = os.getenv("VISION_USER_PROMPT", (
    "Extract ONLY the actual text and content that is visible in these images. "
    "Do not interpret, explain, or generate any content. Simply transcribe what "
    "you can read and see. Include: text, numbers, equations, table data, headings, "
    "captions - but only if they are actually present in the images. If you cannot "
    "clearly read something, do not guess or fill in gaps."
))

# ===== NODE PROCESSING SETTINGS =====
# Used in agents/nodes.py

# Content Length Limits
VALIDATION_MAX_CONTENT_LENGTH = int(os.getenv("VALIDATION_MAX_CONTENT_LENGTH", "1000"))
GENERATION_MAX_CONTENT_LENGTH = int(os.getenv("GENERATION_MAX_CONTENT_LENGTH", "30000"))

# Validation Criteria
VALIDATION_CRITERIA: Dict[str, str] = {
    "grade_check": os.getenv("VALIDATION_GRADE_CHECK", "APPROPRIATE"),
    "safety_check": os.getenv("VALIDATION_SAFETY_CHECK", "APPROPRIATE"),
    "relevance_check": os.getenv("VALIDATION_RELEVANCE_CHECK", "MATCH")
}

# Template Path
NODE_TEMPLATE_PATH = os.getenv("NODE_TEMPLATE_PATH", None)

# ===== NODE PROMPTS =====
# Used in agents/nodes.py

VALIDATION_PROMPT_TEMPLATE = os.getenv("VALIDATION_PROMPT_TEMPLATE", (
    "Analyze this content for {standard} {subject} - {chapter}:\n\n"
    "Content: {content}\n\n"
    "When evaluating grade level, be flexible: content may be appropriate for multiple grades. "
    "Only mark as 'TOO ADVANCED' or 'TOO SIMPLE' if the content is clearly and significantly outside the expected range for the specified standard. "
    "Otherwise, mark as 'APPROPRIATE'.\n\n"
    "Return valid JSON with this structure:\n"
    "{{\n"
    '    "grade_check": "APPROPRIATE/TOO ADVANCED/TOO SIMPLE",\n'
    '    "safety_check": "APPROPRIATE/INAPPROPRIATE", \n'
    '    "relevance_check": "MATCH/PARTIAL_MATCH/NO_MATCH",\n'
    '    "reason": "Brief explanation of the validation result"\n'
    "}}"
))

GENERATION_PROMPT_TEMPLATE = os.getenv("GENERATION_PROMPT_TEMPLATE", (
    "Create educational materials for {standard} {subject} - {chapter}.\n\n"
    "Content: {content}\n\n"
    "Return valid JSON **only**, wrapped inside a Markdown JSON code block like this:\n\n"
    "```json\n"
    "{template}\n"
    "```"
))

# ===== JSON TEMPLATES =====
# Used in agents/nodes.py

GENERATION_JSON_TEMPLATE = os.getenv("GENERATION_JSON_TEMPLATE", '''{
    "importantNotes": "Study notes with markdown formatting",
    "criticalWords": {
        "flashcards": {
            "1": {
                "term": "Key Term 1",
                "definition": "Clear and concise definition of the term",
                "example": "Example or usage of the term"
            },
            "2": {
                "term": "Key Term 2", 
                "definition": "Clear and concise definition of the term",
                "example": "Example or usage of the term"
            },
            "3": {
                "term": "Key Term 3",
                "definition": "Clear and concise definition of the term", 
                "example": "Example or usage of the term"
            },
            "4": {
                "term": "Key Term 4",
                "definition": "Clear and concise definition of the term",
                "example": "Example or usage of the term"
            },
            "5": {
                "term": "Key Term 5",
                "definition": "Clear and concise definition of the term",
                "example": "Example or usage of the term"
            }
        }
    },
    "mcq": {
        "questions": {
            "1": {
                "question": "What is the main topic of this chapter?",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "A",
                "explanation": "Brief explanation of why this is correct"
            },
            "2": {
                "question": "Which of the following is correct?",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "B",
                "explanation": "Brief explanation of why this is correct"
            },
            "3": {
                "question": "Identify the correct statement:",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "C",
                "explanation": "Brief explanation of why this is correct"
            },
            "4": {
                "question": "Choose the best answer:",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "D",
                "explanation": "Brief explanation of why this is correct"
            },
            "5": {
                "question": "Select the correct option:",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "A",
                "explanation": "Brief explanation of why this is correct"
            }
        }
    },
    "fillInTheBlanks": {
        "questions": {"1": "Question 1", "2": "Question 2", "3": "Question 3", "4": "Question 4", "5": "Question 5"},
        "answers": {"1": "answer1", "2": "answer2", "3": "answer3", "4": "answer4", "5": "answer5"}
    },
    "matchTheFollowing": {
        "column_a": {"1": "Term 1", "2": "Term 2", "3": "Term 3", "4": "Term 4", "5": "Term 5"},
        "column_b": {"A": "Definition A", "B": "Definition B", "C": "Definition C", "D": "Definition D", "E": "Definition E"},
        "answers": {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E"}
    },
    "questionAnswer": {
        "questions": {"Q1": "Question 1?", "Q2": "Question 2?", "Q3": "Question 3?"},
        "answers": {"Q1": "Answer 1", "Q2": "Answer 2", "Q3": "Answer 3"}
    }
}''') 