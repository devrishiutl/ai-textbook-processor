"""
Simple Agent Helper Functions
"""
from typing import Dict, Any, List, Union
from utils.utility import read_data_from_image #,read_data_from_file
from pdf2image import convert_from_path

from cleantext import clean

def clean_for_llm_prompt(raw_text):
    cleaned = clean(raw_text, no_line_breaks=True, replace_with_punct=" ")
    cleaned = cleaned.replace("\\", "\\\\")  # Escape raw backslashes
    return cleaned

def extract_content_from_files(pdf_path: str = None, image_paths: List[str] = None) -> str:
    """Extract content from files"""
    if pdf_path:
        # Convert PDF to images using pdf2image
        images = convert_from_path(pdf_path, dpi=300)
        return read_data_from_image(images)
    elif image_paths:
        return read_data_from_image(image_paths)
    return "ERROR: No files provided"
# def extract_content_from_files(pdf_path: str = None, image_paths: List[str] = None) -> str:
#     """Extract content from files"""
#     if pdf_path:
#         return read_data_from_file(pdf_path)
#     elif image_paths:
#         return read_data_from_image(image_paths)
#     return "ERROR: No files provided"

def create_initial_state(standard: str, subject: str, chapter: str, content: str) -> Dict[str, Any]:
    """Create initial state"""
    return {
        "standard": standard,
        "subject": subject,
        "chapter": chapter,
        "content": content,
        "is_valid": False,
        "success": False,
        "error": None,
        "generated_content": None,
        "validation_result": None
    }

# def format_response(state: Dict[str, Any]) -> Dict[str, Any]:
#     """Format response"""
#     if state.get("error"):
#         return {
#             "success": False, 
#             "error": state["error"]
#         }
#     return {
#         "success": True,
#         "content": state.get("generated_content", ""),
#         "validation_result": state.get("validation_result"),
#         "metadata": {
#             "standard": state.get("standard"),
#             "subject": state.get("subject"),
#             "chapter": state.get("chapter")
#         }
#     } 

def format_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """Format response"""
    if state.get("error"):
        return {
            "success": False,
            "error": state["error"]
        }
    
    # Escape backslashes in generated content
    result = state.get("generated_content", "")
    if isinstance(result, str):
        result = result.replace("\\", "\\\\")
    
    return {
        "success": True,
        "content": result,
        "validation_result": state.get("validation_result"),
        "metadata": {
            "standard": state.get("standard"),
            "subject": state.get("subject"),
            "chapter": state.get("chapter")
        }
    }
