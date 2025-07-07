"""
PDF Processing Service
"""
import logging
import os
from typing import Optional
from services.tika_extractor import extract_text_from_pdf

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using Tika"""
    try:
        if not os.path.exists(pdf_path):
            return f"ERROR: PDF file not found: {pdf_path}"
        
        if not pdf_path.lower().endswith('.pdf'):
            return f"ERROR: File is not a PDF: {pdf_path}"
        
        # Use the existing tika_extractor
        from services.tika_extractor import extract_text_from_pdf as tika_extract
        text = tika_extract(pdf_path)
        
        if text and len(text.strip()) > 50:
            return text.strip()
        else:
            return "ERROR: No meaningful text extracted from PDF"
            
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
        return f"ERROR: Failed to extract text from PDF - {str(e)}"

def validate_pdf_file(pdf_path: str) -> dict:
    """Validate PDF file"""
    validation = {
        "is_valid": False,
        "file_size": 0,
        "error_message": ""
    }
    
    try:
        if not os.path.exists(pdf_path):
            validation["error_message"] = f"PDF file not found: {pdf_path}"
            return validation
        
        if not pdf_path.lower().endswith('.pdf'):
            validation["error_message"] = f"File is not a PDF: {pdf_path}"
            return validation
        
        file_size = os.path.getsize(pdf_path)
        validation["file_size"] = file_size
        
        # Check if file is not empty
        if file_size == 0:
            validation["error_message"] = "PDF file is empty"
            return validation
        
        # Check if file is not too large (100MB limit)
        if file_size > 100 * 1024 * 1024:
            validation["error_message"] = "PDF file is too large (max 100MB)"
            return validation
        
        validation["is_valid"] = True
        
    except Exception as e:
        validation["error_message"] = f"Error validating PDF: {str(e)}"
    
    return validation 