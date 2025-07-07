"""
Main Content Processing Service
"""
import logging
from typing import Dict, Any, List, Optional
from core.extractors import extract_content_from_mixed_sources
from core.validators import validate_educational_content, validate_input_parameters, validate_file_paths
from core.generators import generate_educational_content, generate_content_from_vision, generate_comprehensive_output
from core.helpers import extract_content_from_messages
from models.schemas import create_success_response, create_failure_response

logger = logging.getLogger(__name__)

class ContentProcessingService:
    """Main service for processing educational content"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_content(self, 
                       standard: str, 
                       subject: str, 
                       chapter: str,
                       pdf_path: Optional[str] = None,
                       image_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Main method to process educational content - single source only"""
        try:
            # Step 1: Validate input parameters
            param_validation = validate_input_parameters(standard, subject, chapter)
            if not param_validation["is_valid"]:
                metadata = {
                    "standard": standard,
                    "subject": subject,
                    "chapter": chapter,
                    "content_type": "unknown",
                    "files_processed": 0
                }
                return create_failure_response(f"Invalid parameters: {', '.join(param_validation['errors'])}", metadata)
            
            # Step 2: Determine content type and validate
            content_type = None
            files_processed = 0
            
            if image_paths and not pdf_path:
                # Images only
                content_type = "images"
                files_processed = len(image_paths)
                file_validation = validate_file_paths(None, image_paths)
            elif pdf_path and not image_paths:
                # PDF only
                content_type = "pdf"
                files_processed = 1
                file_validation = validate_file_paths(pdf_path, None)
            else:
                # Invalid - mixed sources not allowed
                metadata = {
                    "standard": standard,
                    "subject": subject,
                    "chapter": chapter,
                    "content_type": "unknown",
                    "files_processed": 0
                }
                return create_failure_response("Only single source type allowed: images OR PDF, not both", metadata)
            
            if not file_validation["is_valid"]:
                metadata = {
                    "standard": standard,
                    "subject": subject,
                    "chapter": chapter,
                    "content_type": content_type,
                    "files_processed": files_processed
                }
                return create_failure_response(f"File validation failed: {', '.join(file_validation['errors'])}", metadata)
            
            # Step 3: Process based on content type
            if content_type == "images":
                # Handle images with vision AI
                generated_content = generate_content_from_vision(image_paths, standard, subject, chapter)
                
                if not generated_content.get("success"):
                    metadata = {
                        "standard": standard,
                        "subject": subject,
                        "chapter": chapter,
                        "content_type": "images",
                        "files_processed": files_processed
                    }
                    return create_failure_response(generated_content.get("error", "Failed to process images"), metadata)
                
                # Extract the vision content for validation
                vision_content = generated_content.get("raw_content", "")
                if not vision_content:
                    # Try to get content from the generated content
                    content_dict = generated_content.get("content", {})
                    if isinstance(content_dict, dict):
                        notes = content_dict.get("importantNotes", "")
                        if notes and notes != "No content available to create study notes.":
                            vision_content = notes
                
                # Perform proper validation on the vision content
                if vision_content and len(vision_content.strip()) > 50:
                    validation_results = validate_educational_content(vision_content, standard, subject, chapter)
                else:
                    # If no meaningful content was extracted, create a validation failure
                    validation_results = {
                        "grade_check": "NOT_PERFORMED",
                        "safety_check": "NOT_PERFORMED", 
                        "relevance_check": "NOT_PERFORMED",
                        "reason": "No meaningful content could be extracted from the images for validation",
                        "overall_status": "FAILED",
                        "content_length": len(vision_content) if vision_content else 0,
                        "target_standard": standard,
                        "subject": subject,
                        "chapter": chapter
                    }
                
                # Step 6: Generate comprehensive output for vision processing
                comprehensive_output = generate_comprehensive_output(validation_results, generated_content)
                return comprehensive_output
                
            elif content_type == "pdf":
                # Handle PDF with traditional extraction
                extracted_content = extract_content_from_mixed_sources(pdf_path, None)
                if extracted_content.startswith("ERROR"):
                    metadata = {
                        "standard": standard,
                        "subject": subject,
                        "chapter": chapter,
                        "content_type": "pdf",
                        "files_processed": files_processed
                    }
                    return create_failure_response(extracted_content, metadata)
                
                # Step 4: Validate educational content
                validation_results = validate_educational_content(extracted_content, standard, subject, chapter)
            
                # Step 5: Generate educational content
                if validation_results.get("overall_status") == "PASSED":
                    generated_content = generate_educational_content(extracted_content, standard, subject, chapter)
                else:
                    # If validation failed, create a failure response with actual validation details
                    metadata = {
                        "standard": standard,
                        "subject": subject,
                        "chapter": chapter,
                        "content_type": "pdf",
                        "files_processed": files_processed
                    }
                    return create_failure_response("Content validation failed", metadata, validation_results)
                
                # Step 6: Generate comprehensive output
                comprehensive_output = generate_comprehensive_output(validation_results, generated_content)
                
                return comprehensive_output
            
        except Exception as e:
            self.logger.error(f"Error in content processing: {str(e)}")
            metadata = {
                "standard": standard,
                "subject": subject,
                "chapter": chapter,
                "content_type": "unknown",
                "files_processed": (1 if pdf_path else 0) + (len(image_paths) if image_paths else 0)
            }
            return create_failure_response(f"Processing error: {str(e)}", metadata)
    
    def process_from_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process content from chat messages"""
        try:
            # Extract content and parameters from messages
            content, standard, subject, chapter = extract_content_from_messages(messages)
            
            if not content:
                metadata = {
                    "standard": standard,
                    "subject": subject,
                    "chapter": chapter,
                    "content_type": "text",
                    "files_processed": 0
                }
                return create_failure_response("No content found in messages", metadata)
            
            if not all([standard, subject, chapter]):
                metadata = {
                    "standard": standard,
                    "subject": subject,
                    "chapter": chapter,
                    "content_type": "text",
                    "files_processed": 0
                }
                return create_failure_response("Missing required parameters (standard, subject, chapter)", metadata)
            
            # Validate educational content
            validation_results = validate_educational_content(content, standard, subject, chapter)
            
            # Generate educational content
            if validation_results.get("overall_status") == "PASSED":
                generated_content = generate_educational_content(content, standard, subject, chapter)
            else:
                # If validation failed, create a failure response with actual validation details
                metadata = {
                    "standard": standard,
                    "subject": subject,
                    "chapter": chapter,
                    "content_type": "text",
                    "files_processed": 0
                }
                return create_failure_response("Content validation failed", metadata, validation_results)
            
            # Generate comprehensive output
            comprehensive_output = generate_comprehensive_output(validation_results, generated_content)
            
            return comprehensive_output
            
        except Exception as e:
            self.logger.error(f"Error processing messages: {str(e)}")
            metadata = {
                "standard": standard,
                "subject": subject,
                "chapter": chapter,
                "content_type": "text",
                "files_processed": 0
            }
            return create_failure_response(f"Processing error: {str(e)}", metadata) 