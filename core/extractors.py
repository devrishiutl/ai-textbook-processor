"""
Content Extraction Functions
"""
import logging
from typing import List, Dict, Any
from services.pdf_service import extract_text_from_pdf
from services.image_service import extract_text_from_images

logger = logging.getLogger(__name__)

def extract_content_from_pdf(pdf_path: str) -> str:
    """Extract text content from PDF"""
    try:
        text = extract_text_from_pdf(pdf_path)
        if text and len(text.strip()) > 50:
            return text.strip()
        else:
            return "ERROR: No meaningful text extracted from PDF"
    except Exception as e:
        logger.error(f"Error extracting content from PDF {pdf_path}: {str(e)}")
        return f"ERROR: Failed to extract content from PDF - {str(e)}"

def extract_content_from_images(image_paths: List[str]) -> str:
    """Extract text content from images"""
    try:
        if not image_paths:
            return "ERROR: No image paths provided"
        
        extracted_texts = []
        for img_path in image_paths:
            try:
                text = extract_text_from_images([img_path])
                if text and not text.startswith("ERROR"):
                    extracted_texts.append(text)
            except Exception as e:
                logger.warning(f"Failed to extract text from image {img_path}: {str(e)}")
        
        if extracted_texts:
            return "\n\n".join(extracted_texts)
        else:
            return "ERROR: No text could be extracted from any images"
            
    except Exception as e:
        logger.error(f"Error extracting content from images: {str(e)}")
        return f"ERROR: Failed to extract content from images - {str(e)}"

def extract_content_from_mixed_sources(pdf_path: str = None, image_paths: List[str] = None) -> str:
    """Extract content from both PDF and images"""
    content_parts = []
    
    # Extract from PDF if provided
    if pdf_path:
        pdf_content = extract_content_from_pdf(pdf_path)
        if not pdf_content.startswith("ERROR"):
            content_parts.append(f"PDF Content:\n{pdf_content}")
        else:
            logger.warning(f"PDF extraction failed: {pdf_content}")
    
    # Extract from images if provided
    if image_paths:
        image_content = extract_content_from_images(image_paths)
        if not image_content.startswith("ERROR"):
            content_parts.append(f"Image Content:\n{image_content}")
        else:
            logger.warning(f"Image extraction failed: {image_content}")
    
    if content_parts:
        return "\n\n---\n\n".join(content_parts)
    else:
        return "ERROR: No content could be extracted from any source"

def validate_extracted_content(content: str) -> Dict[str, Any]:
    """Validate extracted content quality"""
    validation = {
        "is_valid": False,
        "content_length": 0,
        "has_meaningful_text": False,
        "error_message": ""
    }
    
    try:
        if not content or content.startswith("ERROR"):
            validation["error_message"] = content if content else "No content provided"
            return validation
        
        validation["content_length"] = len(content)
        validation["has_meaningful_text"] = len(content.strip()) > 50
        
        # Check for meaningful content (not just whitespace or error messages)
        meaningful_chars = len([c for c in content if c.isalnum()])
        validation["is_valid"] = meaningful_chars > 20
        
        if not validation["is_valid"]:
            validation["error_message"] = "Extracted content is too short or contains no meaningful text"
            
    except Exception as e:
        validation["error_message"] = f"Error validating content: {str(e)}"
    
    return validation 