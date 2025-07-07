"""
Simple Agent Helper Functions
"""
from typing import Dict, Any, List, Union
from utils.utility import read_data_from_file, read_data_from_image

def extract_content_from_files(pdf_path: str = None, image_paths: List[str] = None) -> str:
    """Extract content from files"""
    if pdf_path:
        return read_data_from_file(pdf_path)
    elif image_paths:
        return read_data_from_image(image_paths)
    return "ERROR: No files provided"

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

def format_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """Format response"""
    if state.get("error"):
        return {
            "success": False, 
            "error": state["error"]
        }
    return {
        "success": True,
        "content": state.get("generated_content", ""),
        "validation_result": state.get("validation_result"),
        "metadata": {
            "standard": state.get("standard"),
            "subject": state.get("subject"),
            "chapter": state.get("chapter")
        }
    } 