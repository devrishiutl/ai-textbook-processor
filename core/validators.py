"""
Validation Functions
"""
import logging
from typing import Dict, Any, List
from core.tools import validate_content_tool
from core.helpers import parse_validation_response

logger = logging.getLogger(__name__)

def validate_educational_content(content: str, target_standard: str, subject: str, chapter: str) -> Dict[str, Any]:
    """Validate educational content using LLM"""
    try:
        # Call LLM for validation
        validation_response = validate_content_tool(content, target_standard, subject, chapter)
        
        # Parse the response
        validation_results = parse_validation_response(validation_response)
        
        # Add metadata
        validation_results.update({
            "content_length": len(content),
            "target_standard": target_standard,
            "subject": subject,
            "chapter": chapter
        })
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Error validating content: {str(e)}")
        return {
            "grade_check": "ERROR",
            "safety_check": "ERROR",
            "relevance_check": "ERROR",
            "reason": f"Validation failed: {str(e)}",
            "overall_status": "ERROR",
            "content_length": len(content),
            "target_standard": target_standard,
            "subject": subject,
            "chapter": chapter
        }

def validate_input_parameters(standard: str, subject: str, chapter: str) -> Dict[str, Any]:
    """Validate input parameters"""
    validation = {
        "is_valid": True,
        "errors": []
    }
    
    # Check for required parameters
    if not standard or not standard.strip():
        validation["is_valid"] = False
        validation["errors"].append("Standard is required")
    
    if not subject or not subject.strip():
        validation["is_valid"] = False
        validation["errors"].append("Subject is required")
    
    if not chapter or not chapter.strip():
        validation["is_valid"] = False
        validation["errors"].append("Chapter is required")
    
    # Validate standard format (e.g., "Class 10", "Grade 5")
    if standard and not any(keyword in standard.lower() for keyword in ["class", "grade", "standard"]):
        validation["is_valid"] = False
        validation["errors"].append("Standard should contain 'Class', 'Grade', or 'Standard'")
    
    return validation

def validate_file_paths(pdf_path: str = None, image_paths: List[str] = None) -> Dict[str, Any]:
    """Validate file paths"""
    validation = {
        "is_valid": True,
        "errors": [],
        "valid_files": []
    }
    
    import os
    
    # Validate PDF path
    if pdf_path:
        if not os.path.exists(pdf_path):
            validation["is_valid"] = False
            validation["errors"].append(f"PDF file not found: {pdf_path}")
        elif not pdf_path.lower().endswith('.pdf'):
            validation["is_valid"] = False
            validation["errors"].append(f"File is not a PDF: {pdf_path}")
        else:
            validation["valid_files"].append(pdf_path)
    
    # Validate image paths
    if image_paths:
        for img_path in image_paths:
            if not os.path.exists(img_path):
                validation["is_valid"] = False
                validation["errors"].append(f"Image file not found: {img_path}")
            elif not img_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                validation["is_valid"] = False
                validation["errors"].append(f"File is not a supported image format: {img_path}")
            else:
                validation["valid_files"].append(img_path)
    
    # Check if at least one valid file is provided
    if not validation["valid_files"]:
        validation["is_valid"] = False
        validation["errors"].append("No valid files provided")
    
    return validation

def validate_generated_content(content: str) -> Dict[str, Any]:
    """Validate generated educational content"""
    validation = {
        "is_valid": True,
        "sections_found": [],
        "errors": []
    }
    
    required_sections = [
        "STUDY NOTES:",
        "FILL-IN-THE-BLANKS:",
        "MATCH-THE-FOLLOWING EXERCISES:",
        "SUBJECTIVE QUESTIONS:"
    ]
    
    for section in required_sections:
        if section in content:
            validation["sections_found"].append(section)
        else:
            validation["is_valid"] = False
            validation["errors"].append(f"Missing required section: {section}")
    
    # Check content length
    if len(content.strip()) < 100:
        validation["is_valid"] = False
        validation["errors"].append("Generated content is too short")
    
    return validation 