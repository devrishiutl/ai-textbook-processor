"""
Content Generation Functions
"""
import logging
from typing import Dict, Any
from core.tools import generate_content_tool, vision_understand_tool
from core.helpers import parse_generated_content

logger = logging.getLogger(__name__)

def generate_educational_content(content: str, grade_level: str, subject: str, chapter: str) -> Dict[str, Any]:
    """Generate educational content from extracted text"""
    try:
        # Generate content using LLM
        generated_content = generate_content_tool(content, grade_level, subject, chapter)
        
        # Try to parse as JSON
        import json
        try:
            # Clean the response and parse JSON
            cleaned_content = generated_content.strip()
            if cleaned_content.startswith('```json'):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.endswith('```'):
                cleaned_content = cleaned_content[:-3]
            
            parsed_content = json.loads(cleaned_content.strip())
            
            return {
                "success": True,
                "content": parsed_content,
                "metadata": {
                    "grade_level": grade_level,
                    "subject": subject,
                    "chapter": chapter,
                    "source_content_length": len(content)
                }
            }
            
        except json.JSONDecodeError as json_error:
            logger.error(f"Failed to parse JSON response: {str(json_error)}")
            logger.error(f"Raw response: {generated_content}")
            
            # Fallback to old parsing method
            parsed_content = parse_generated_content(generated_content)
            
            return {
                "success": True,
                "content": parsed_content,
                "metadata": {
                    "grade_level": grade_level,
                    "subject": subject,
                    "chapter": chapter,
                    "source_content_length": len(content)
                }
            }
        
    except Exception as e:
        logger.error(f"Error generating educational content: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "content": {},
            "metadata": {
                "grade_level": grade_level,
                "subject": subject,
                "chapter": chapter,
                "source_content_length": len(content)
            }
        }

def generate_content_from_vision(images: list, standard: str, subject: str, chapter: str) -> Dict[str, Any]:
    """Generate content from images using vision AI"""
    try:
        # Process images with vision AI
        vision_content = vision_understand_tool(images, standard, subject, chapter)
        
        if vision_content.startswith("ERROR"):
            return {
                "success": False,
                "error": vision_content,
                "raw_content": "",
                "parsed_content": {},
                "metadata": {
                    "standard": standard,
                    "subject": subject,
                    "chapter": chapter,
                    "image_count": len(images)
                }
            }
        
        # Generate educational content from vision output
        generated_result = generate_educational_content(vision_content, standard, subject, chapter)
        
        # Add the raw vision content to the result for validation
        if generated_result.get("success"):
            generated_result["raw_content"] = vision_content
        
        return generated_result
        
    except Exception as e:
        logger.error(f"Error generating content from vision: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "raw_content": "",
            "parsed_content": {},
            "metadata": {
                "standard": standard,
                "subject": subject,
                "chapter": chapter,
                "image_count": len(images)
            }
        }

def generate_comprehensive_output(validation_results: Dict, generated_content: Dict) -> Dict[str, Any]:
    """Generate comprehensive output combining validation and generation results"""
    try:
        # Check if validation passed
        if validation_results.get("overall_status") != "PASSED":
            # Create a more descriptive failure message based on validation results
            failed_checks = []
            not_performed_checks = []
            
            # Check for actual failures
            if validation_results.get("grade_check") in ["FAILED", "ERROR", "INAPPROPRIATE"]:
                failed_checks.append("grade level")
            elif validation_results.get("grade_check") == "NOT_PERFORMED":
                not_performed_checks.append("grade level")
                
            if validation_results.get("safety_check") in ["FAILED", "ERROR", "UNSAFE"]:
                failed_checks.append("safety")
            elif validation_results.get("safety_check") == "NOT_PERFORMED":
                not_performed_checks.append("safety")
                
            if validation_results.get("relevance_check") in ["FAILED", "ERROR", "NO_MATCH"]:
                failed_checks.append("relevance")
            elif validation_results.get("relevance_check") == "NOT_PERFORMED":
                not_performed_checks.append("relevance")
            
            # Create appropriate failure message
            if failed_checks:
                failure_reason = f"Content validation failed: {' and '.join(failed_checks)} checks did not pass"
            elif not_performed_checks:
                failure_reason = f"Content validation could not be performed: {' and '.join(not_performed_checks)} checks were not completed"
            else:
                failure_reason = "Content validation failed for unknown reasons"
            
            return {
                "success": False,
                "message": failure_reason,
                "error": validation_results.get("reason", "Validation did not pass"),
                "metadata": {
                    "validation_details": validation_results,
                    "content_generated": False
                }
            }
        
        # Return the structured content directly
        return {
            "success": True,
            "message": "Educational content processed successfully",
            "content": generated_content.get("content", {}),
            "metadata": {
                "validation_details": validation_results,
                "content_generated": generated_content.get("success", False)
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating comprehensive output: {str(e)}")
        return {
            "success": False,
            "message": "Error processing content",
            "error": str(e),
            "metadata": {
                "validation_details": validation_results,
                "content_generated": False
            }
        } 