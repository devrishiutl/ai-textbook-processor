"""
Helper Functions - Utility and helper functions
"""
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def parse_validation_response(response: str) -> Dict[str, Any]:
    """Parse validation response from LLM"""
    result = {
        "grade_check": "UNKNOWN",
        "safety_check": "UNKNOWN", 
        "relevance_check": "UNKNOWN",
        "reason": "Failed to parse response",
        "overall_status": "FAILED"
    }
    
    try:
        lines = response.strip().split('\n')
        for line in lines:
            if line.startswith('GRADE_CHECK:'):
                result["grade_check"] = line.split(':', 1)[1].strip()
            elif line.startswith('SAFETY_CHECK:'):
                result["safety_check"] = line.split(':', 1)[1].strip()
            elif line.startswith('RELEVANCE_CHECK:'):
                result["relevance_check"] = line.split(':', 1)[1].strip()
            elif line.startswith('REASON:'):
                result["reason"] = line.split(':', 1)[1].strip()
        
        # Determine overall status based on actual validation results
        grade_ok = result["grade_check"] == "APPROPRIATE"
        safety_ok = result["safety_check"] == "APPROPRIATE"
        relevance_ok = result["relevance_check"] == "MATCH"  # Only exact MATCH is considered passing
        
        if grade_ok and safety_ok and relevance_ok:
            result["overall_status"] = "PASSED"
        else:
            result["overall_status"] = "FAILED"
            
            # If no specific reason was provided, create one based on the failures
            if result["reason"] == "Failed to parse response" or not result["reason"]:
                failed_checks = []
                if not grade_ok:
                    failed_checks.append("grade level")
                if not safety_ok:
                    failed_checks.append("safety")
                if not relevance_ok:
                    failed_checks.append("relevance")
                
                if failed_checks:
                    result["reason"] = f"Failed: {' and '.join(failed_checks)} checks"
                else:
                    result["reason"] = "Content is appropriate, safe, and relevant."
        
    except Exception as e:
        result["reason"] = f"Error parsing validation response: {str(e)}"
    
    return result

def extract_content_from_messages(messages: list) -> tuple:
    """Extract content and parameters from messages"""
    content = None
    standard = None
    subject = None
    chapter = None
    
    for message in messages:
        if message.get("role") == "system":
            system_content = message.get("content", "")
            if "specializing in" in system_content and "for" in system_content:
                match = re.search(r'specializing in (.+?) for (.+?) students, focusing on (.+?)\.', system_content)
                if match:
                    subject = match.group(1)
                    standard = match.group(2) 
                    chapter = match.group(3)
        
        elif message.get("role") == "user" and message.get("content", "").startswith("Educational content to process:"):
            content = message.get("content", "").replace("Educational content to process:", "").strip()
    
    return content, standard, subject, chapter

def parse_generated_content(content: str) -> Dict[str, str]:
    """Parse the generated content into different sections (fallback for non-JSON responses)"""
    sections = {
        "notes": "Not generated",
        "blanks": "Not generated", 
        "matches": "Not generated",
        "qna": "Not generated"
    }
    
    try:
        # Split content by section headers
        parts = content.split("STUDY NOTES:")
        if len(parts) > 1:
            remaining = parts[1]
            
            # Extract STUDY NOTES
            if "FILL-IN-THE-BLANKS:" in remaining:
                notes_part, remaining = remaining.split("FILL-IN-THE-BLANKS:", 1)
                sections["notes"] = "STUDY NOTES:" + notes_part.strip()
            else:
                sections["notes"] = "STUDY NOTES:" + remaining.strip()
            
            # Extract FILL-IN-THE-BLANKS
            if "MATCH-THE-FOLLOWING EXERCISES:" in remaining:
                blanks_part, remaining = remaining.split("MATCH-THE-FOLLOWING EXERCISES:", 1)
                sections["blanks"] = "FILL-IN-THE-BLANKS:" + blanks_part.strip()
            else:
                sections["blanks"] = "FILL-IN-THE-BLANKS:" + remaining.strip()
            
            # Extract MATCH-THE-FOLLOWING EXERCISES
            if "SUBJECTIVE QUESTIONS:" in remaining:
                matches_part, remaining = remaining.split("SUBJECTIVE QUESTIONS:", 1)
                sections["matches"] = "MATCH-THE-FOLLOWING EXERCISES:" + matches_part.strip()
            else:
                sections["matches"] = "MATCH-THE-FOLLOWING EXERCISES:" + remaining.strip()
            
            # Extract SUBJECTIVE QUESTIONS
            sections["qna"] = "SUBJECTIVE QUESTIONS:" + remaining.strip()
            
    except Exception as e:
        logger.warning(f"Error parsing generated content: {str(e)}")
        # If parsing fails, store the raw content
        sections = {
            "notes": content,
            "blanks": content,
            "matches": content, 
            "qna": content
        }
    
    return sections

 