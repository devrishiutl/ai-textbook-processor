"""
Pydantic Models for Data Validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ProcessingRequest(BaseModel):
    """Request model for content processing"""
    standard: str = Field(..., description="Target educational standard (e.g., 'Class 10')")
    subject: str = Field(..., description="Subject name (e.g., 'Mathematics')")
    chapter: str = Field(..., description="Chapter name (e.g., 'Algebra')")
    pdf_path: Optional[str] = Field(None, description="Path to PDF file")
    image_paths: Optional[List[str]] = Field(None, description="List of image file paths")

class ValidationDetails(BaseModel):
    """Validation details structure"""
    grade_check: str = Field(..., description="Grade level appropriateness check result")
    safety_check: str = Field(..., description="Safety check result")
    relevance_check: str = Field(..., description="Relevance check result")
    reason: str = Field(..., description="Reason for validation result")
    overall_status: str = Field(..., description="Overall validation status")
    content_length: int = Field(..., description="Length of processed content")
    target_standard: str = Field(..., description="Target educational standard")
    subject: str = Field(..., description="Subject name")
    chapter: str = Field(..., description="Chapter name")

class GeneratedContent(BaseModel):
    """Generated educational content structure"""
    importantNotes: str = Field(..., description="Important study notes")
    fillInTheBlanks: Dict[str, Any] = Field(..., description="Fill-in-the-blanks exercises")
    matchTheFollowing: Dict[str, Any] = Field(..., description="Match-the-following exercises")
    questionAnswer: Dict[str, Any] = Field(..., description="Question and answer exercises")

class ProcessingMetadata(BaseModel):
    """Processing metadata structure"""
    standard: str = Field(..., description="Target educational standard")
    subject: str = Field(..., description="Subject name")
    chapter: str = Field(..., description="Chapter name")
    content_type: str = Field(..., description="Type of content processed")
    files_processed: int = Field(..., description="Number of files processed")
    validation_details: ValidationDetails = Field(..., description="Validation results")

class ProcessingResponse(BaseModel):
    """Response model for content processing - CENTRALIZED STRUCTURE"""
    success: bool = Field(..., description="Whether processing was successful")
    message: str = Field(..., description="Processing result message")
    content: Dict[str, Any] = Field(..., description="Generated educational content (empty dict if failed)")
    metadata: ProcessingMetadata = Field(..., description="Processing metadata")

# Response structure constants for consistent usage
SUCCESS_RESPONSE_STRUCTURE = {
    "success": True,
    "message": "Educational content processed successfully",
    "content": {
        "importantNotes": "",
        "fillInTheBlanks": {},
        "matchTheFollowing": {},
        "questionAnswer": {}
    },
    "metadata": {
        "standard": "",
        "subject": "",
        "chapter": "",
        "content_type": "",
        "files_processed": 0,
        "validation_details": {
            "grade_check": "",
            "safety_check": "",
            "relevance_check": "",
            "reason": "",
            "overall_status": "",
            "content_length": 0,
            "target_standard": "",
            "subject": "",
            "chapter": ""
        }
    }
}

FAILURE_RESPONSE_STRUCTURE = {
    "success": False,
    "message": "Processing failed",
    "content": {},
    "metadata": {
        "standard": "",
        "subject": "",
        "chapter": "",
        "content_type": "",
        "files_processed": 0,
        "validation_details": {
            "grade_check": "NOT_PERFORMED",
            "safety_check": "NOT_PERFORMED",
            "relevance_check": "NOT_PERFORMED",
            "reason": "Validation could not be performed",
            "overall_status": "FAILED",
            "content_length": 0,
            "target_standard": "",
            "subject": "",
            "chapter": ""
        }
    }
}

def create_success_response(content: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Create a consistent success response"""
    return {
        "success": True,
        "message": "Educational content processed successfully",
        "content": content,
        "metadata": metadata
    }

def create_failure_response(error_message: str, metadata: Dict[str, Any], validation_details: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create a consistent failure response"""
    # Use provided validation details or create default ones
    if validation_details:
        # If we have actual validation details, use them as-is
        final_validation_details = validation_details
    else:
        # When we don't have actual validation results, be honest about it
        final_validation_details = {
            "grade_check": "NOT_PERFORMED",
            "safety_check": "NOT_PERFORMED", 
            "relevance_check": "NOT_PERFORMED",
            "reason": f"Validation could not be performed: {error_message}",
            "overall_status": "FAILED",
            "content_length": 0,
            "target_standard": metadata.get("standard", ""),
            "subject": metadata.get("subject", ""),
            "chapter": metadata.get("chapter", "")
        }
    
    return {
        "success": False,
        "message": "Processing failed",
        "content": {},
        "metadata": {
            **metadata,
            "validation_details": final_validation_details
        }
    }

class FileValidationResult(BaseModel):
    """File validation result model"""
    is_valid: bool = Field(..., description="Whether files are valid")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    valid_files: List[str] = Field(default_factory=list, description="List of valid files")

class ContentExtractionResult(BaseModel):
    """Content extraction result model"""
    success: bool = Field(..., description="Whether extraction was successful")
    content: str = Field(..., description="Extracted content")
    source_type: str = Field(..., description="Type of source (PDF, Image, Mixed)")
    error_message: Optional[str] = Field(None, description="Error message if extraction failed") 