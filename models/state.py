"""
LangGraph State Definitions
"""
from typing import TypedDict, List, Dict, Any, Optional

class ProcessingState(TypedDict):
    """State for the educational content processing workflow"""
    messages: List[Dict[str, Any]]
    content: Optional[str]
    standard: Optional[str]
    subject: Optional[str]
    chapter: Optional[str]
    pdf_path: Optional[str]
    image_paths: Optional[List[str]]
    validation_results: Optional[Dict[str, Any]]
    generated_content: Optional[Dict[str, Any]]
    final_response: Optional[str]
    error_message: Optional[str]
    processing_steps: List[str]

def should_continue_to_validation(state: ProcessingState) -> str:
    """Determine if we should continue to validation"""
    if state.get("error_message"):
        return "error"
    return "continue"

def should_continue_to_generation(state: ProcessingState) -> str:
    """Determine if we should continue to generation"""
    if state.get("error_message"):
        return "error"
    return "continue" 