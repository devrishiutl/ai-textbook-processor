from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence, Dict, Optional
from langchain_core.messages import BaseMessage
import operator
import re
import logging

# Create logger for this module
logger = logging.getLogger(__name__)
from tools import (
    child_filter_tool,
    content_match_tool,
    generate_notes_tool,
    generate_qna_tool,
    generate_blanks_tool,
    generate_match_tool,
    grade_level_check_tool
)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    content: Optional[str]
    standard: Optional[str]
    subject: Optional[str]
    chapter: Optional[str]
    validation_results: Optional[Dict[str, str]]
    generated_content: Optional[Dict[str, str]]
    processing_status: Optional[str]
    error_details: Optional[str]

def content_extraction_node(state):
    """Extract content and parameters from messages"""
    logger.info("📄 Step 1: Content Extraction...")
    
    # Debug logging for input parameters
    logger.info(f"🔍 Input State: standard='{state.get('standard')}', subject='{state.get('subject')}', chapter='{state.get('chapter')}'")
    
    messages = state["messages"]
    content = None
    standard = state.get('standard')  # Use state parameters as priority
    subject = state.get('subject')
    chapter = state.get('chapter')
    
    # Extract parameters from system message only if not already in state
    for message in messages:
        if message.get("role") == "system":
            system_content = message.get("content", "")
            if "specializing in" in system_content and "for" in system_content:
                match = re.search(r'specializing in (.+?) for (.+?) students, focusing on (.+?)\.', system_content)
                if match and not all([subject, standard, chapter]):  # Only extract if missing
                    subject = subject or match.group(1)
                    standard = standard or match.group(2) 
                    chapter = chapter or match.group(3)
        
        # Extract main content
        elif message.get("role") == "user" and message.get("content", "").startswith("Educational content to process:"):
            content = message.get("content", "").replace("Educational content to process:", "").strip()
    
    if not content:
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": "No educational content found to process"
        }
    
    # Debug logging for extracted parameters
    logger.info(f"🔍 Extracted: standard='{standard}', subject='{subject}', chapter='{chapter}'")
    
    return {
        **state,
        "content": content,
        "standard": standard,
        "subject": subject,
        "chapter": chapter,
        "processing_status": "CONTINUE"
    }

def comprehensive_validation_node(state):
    """Single node for all validation checks (grade, safety, relevance)"""
    logger.info("🎯 Step 2: Comprehensive Validation (Grade + Safety + Relevance)...")
    
    # Debug logging for validation parameters
    logger.info(f"🔍 Validation Params: standard='{state.get('standard')}', subject='{state.get('subject')}', chapter='{state.get('chapter')}'")
    
    try:
        # Use the strict grade validation with forbidden terms checking
        grade_validation_result = grade_level_check_tool(
            state["content"], 
            state["standard"], 
            state["subject"], 
            state["chapter"]
        )
        
        logger.info(f"📊 Grade Validation Result: {grade_validation_result[:100]}...")
        
        # Check if grade validation failed
        if "TOO ADVANCED" in grade_validation_result or "TOO SIMPLE" in grade_validation_result:
            logger.info(f"❌ Grade validation FAILED: {grade_validation_result}")
            return {
                **state,
                "processing_status": "FAILED",
                "validation_results": {
                    "grade_check": "FAIL",
                    "safety_check": "NOT_CHECKED",
                    "relevance_check": "NOT_CHECKED",
                    "status": "FAILED",
                    "reason": grade_validation_result
                },
                "error_details": f"Grade validation failed: {grade_validation_result}"
            }
        
        # If grade validation passes, do quick safety and relevance checks
        safety_result = child_filter_tool(state["content"])
        relevance_result = content_match_tool(state["content"], state["subject"], state["chapter"])
        
        # Check safety
        if "INAPPROPRIATE" in safety_result:
            logger.info(f"❌ Safety validation FAILED: {safety_result}")
            return {
                **state,
                "processing_status": "FAILED",
                "validation_results": {
                    "grade_check": "PASS",
                    "safety_check": "FAIL",
                    "relevance_check": "NOT_CHECKED",
                    "status": "FAILED",
                    "reason": safety_result
                },
                "error_details": f"Safety validation failed: {safety_result}"
            }
        
        # Check relevance
        if "NO_MATCH" in relevance_result:
            logger.info(f"❌ Relevance validation FAILED: {relevance_result}")
            return {
                **state,
                "processing_status": "FAILED",
                "validation_results": {
                    "grade_check": "PASS",
                    "safety_check": "PASS",
                    "relevance_check": "FAIL",
                    "status": "FAILED",
                    "reason": relevance_result
                },
                "error_details": f"Relevance validation failed: {relevance_result}"
            }
        
        # All validations passed
        logger.info("✅ All validations PASSED - continuing to content generation")
        return {
            **state,
            "processing_status": "CONTINUE",
            "validation_results": {
                "grade_check": "PASS",
                "safety_check": "PASS",
                "relevance_check": "PASS",
                "status": "PASS",
                "reason": "All validations passed"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Comprehensive validation ERROR: {e}")
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"Validation error: {str(e)}"
        }

def validation_router(state):
    """Router function for validation results"""
    logger.debug("🔍 Debug: Validation router - checking state")
    
    processing_status = state.get("processing_status", "UNKNOWN")
    logger.debug(f"🔍 Debug: Validation router - processing_status: {processing_status}")
    
    if processing_status == "FAILED":
        logger.debug("🔍 Debug: Validation router - FAILED")
        return "failed"
    else:
        logger.debug("🔍 Debug: Validation router - CONTINUE to normalization")
        return "continue"

# Removed old validation nodes - now using single comprehensive validation

def content_normalization_node(state):
    """Pass-through node - content is already validated and ready for processing"""
    logger.info("🔧 Step 5: Content Ready for Processing...")
    
    # Simply pass through the validated content
    return {
        **state,
        "original_content": state["content"]
    }

def generate_notes_node(state):
    """Generate study notes"""
    logger.info("📝 Step 6: Generating Study Notes...")
    
    try:
        notes = generate_notes_tool(
            state["content"], 
            state["standard"], 
            state["subject"], 
            state["chapter"]
        )
        
        logger.debug(f"🔍 Debug: Generated notes - {len(notes)} characters")
        
        generated_content = state.get("generated_content", {})
        generated_content["notes"] = notes
        
        logger.debug("🔍 Debug: Notes generation COMPLETED - continuing to blanks")
        
        return {
            **state,
            "generated_content": generated_content
        }
        
    except Exception as e:
        logger.error(f"🔍 Debug: Notes generation ERROR: {e}")
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"Notes generation error: {str(e)}"
        }

def generate_blanks_node(state):
    """Generate fill-in-the-blanks"""
    logger.info("📋 Step 7: Creating Fill-in-Blanks...")
    
    try:
        blanks = generate_blanks_tool(
            state["content"], 
            state["standard"], 
            state["subject"], 
            state["chapter"]
        )
        
        logger.debug(f"🔍 Debug: Generated blanks - {len(blanks)} characters")
        
        generated_content = state.get("generated_content", {})
        generated_content["blanks"] = blanks
        
        logger.debug("🔍 Debug: Blanks generation COMPLETED - continuing to matches")
        
        return {
            **state,
            "generated_content": generated_content
        }
        
    except Exception as e:
        logger.error(f"🔍 Debug: Blanks generation ERROR: {e}")
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"Blanks generation error: {str(e)}"
        }

def generate_matches_node(state):
    """Generate match-the-following"""
    logger.info("🔗 Step 8: Designing Match-the-Following...")
    
    try:
        matches = generate_match_tool(
            state["content"], 
            state["standard"], 
            state["subject"], 
            state["chapter"]
        )
        
        logger.debug(f"🔍 Debug: Generated matches - {len(matches)} characters")
        
        generated_content = state.get("generated_content", {})
        generated_content["matches"] = matches
        
        logger.debug("🔍 Debug: Matches generation COMPLETED - continuing to Q&A")
        
        return {
            **state,
            "generated_content": generated_content
        }
        
    except Exception as e:
        logger.error(f"🔍 Debug: Matches generation ERROR: {e}")
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"Matches generation error: {str(e)}"
        }

def generate_qna_node(state):
    """Generate subjective questions with drawing capabilities"""
    logger.info("❓ Step 9: Formulating Questions...")
    
    try:
        qna = generate_qna_tool(
            state["content"], 
            state["standard"], 
            state["subject"], 
            state["chapter"]
        )
        
        logger.debug(f"🔍 Debug: Generated Q&A - {len(qna)} characters")
        
        generated_content = state.get("generated_content", {})
        generated_content["qna"] = qna
        
        logger.debug("🔍 Debug: Q&A generation COMPLETED - continuing to output formatting")
        
        return {
            **state,
            "generated_content": generated_content
        }
        
    except Exception as e:
        logger.error(f"🔍 Debug: Q&A generation ERROR: {e}")
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"QNA generation error: {str(e)}"
        }

def output_formatter_node(state):
    """Format final output"""
    logger.info("📋 Step 10: Formatting Output...")
    
    try:
        validation_results = state.get("validation_results", {})
        generated_content = state.get("generated_content", {})
        
        logger.debug(f"🔍 Debug: Validation results keys: {list(validation_results.keys())}")
        logger.debug(f"🔍 Debug: Generated content keys: {list(generated_content.keys())}")
        
        # Create comprehensive response with new validation structure
        comprehensive_response = f"""
COMPREHENSIVE VALIDATION RESULTS:
Grade Check: {validation_results.get('grade_check', 'Not performed')}
Safety Check: {validation_results.get('safety_check', 'Not performed')}
Relevance Check: {validation_results.get('relevance_check', 'Not performed')}
Overall Status: {validation_results.get('status', 'Unknown')}

COMPREHENSIVE STUDY NOTES:
{generated_content.get('notes', 'Not generated')}

FILL-IN-THE-BLANKS EXERCISES:
{generated_content.get('blanks', 'Not generated')}

MATCH-THE-FOLLOWING EXERCISES:
{generated_content.get('matches', 'Not generated')}

SUBJECTIVE QUESTIONS:
{generated_content.get('qna', 'Not generated')}
        """
        
        logger.debug(f"🔍 Debug: Created comprehensive response - {len(comprehensive_response)} characters")
        logger.debug("🔍 Debug: Output formatting COMPLETED - adding assistant message")
        
        return {
            **state,
            "messages": state["messages"] + [{"role": "assistant", "content": comprehensive_response}]
        }
        
    except Exception as e:
        logger.error(f"🔍 Debug: Output formatting ERROR: {e}")
        error_response = f"❌ Output formatting failed: {str(e)}"
        return {
            **state,
            "messages": state["messages"] + [{"role": "assistant", "content": error_response}]
        }

def build_graph():
    """Build comprehensive multi-node educational processing graph with proper conditional validation"""
    
    graph = StateGraph(AgentState)
    
    # Add all nodes
    graph.add_node("extract_content", content_extraction_node)
    graph.add_node("comprehensive_validation", comprehensive_validation_node)
    graph.add_node("normalize_content", content_normalization_node)
    graph.add_node("generate_notes", generate_notes_node)
    graph.add_node("generate_blanks", generate_blanks_node)
    graph.add_node("generate_matches", generate_matches_node)
    graph.add_node("generate_qna", generate_qna_node)
    graph.add_node("format_output", output_formatter_node)
    
    # Define flow with single comprehensive validation
    graph.set_entry_point("extract_content")
    
    # Step 1: Extract content
    graph.add_edge("extract_content", "comprehensive_validation")
    
    # Step 2: CONDITIONAL - Single comprehensive validation (grade + safety + relevance)
    graph.add_conditional_edges(
        "comprehensive_validation",
        validation_router,
        {
            "continue": "normalize_content",  # If ALL validations pass
            "failed": END                     # If ANY validation fails → STOP
        }
    )
    
    # Step 3: Normalize content for processing (after validation passes)
    graph.add_edge("normalize_content", "generate_notes")
    
    # Step 4-7: Content generation pipeline (only if validation passes)
    graph.add_edge("generate_notes", "generate_blanks")
    graph.add_edge("generate_blanks", "generate_matches")
    graph.add_edge("generate_matches", "generate_qna")
    
    # Step 8: Format and end
    graph.add_edge("generate_qna", "format_output")

# # After normalization, run all generators in parallel
#     graph.add_edge("normalize_content", "generate_notes")
#     graph.add_edge("normalize_content", "generate_blanks")
#     graph.add_edge("normalize_content", "generate_matches")
#     graph.add_edge("normalize_content", "generate_qna")
#     # After all are done, join into formatter
#     graph.add_edge("generate_notes", "format_output")
#     graph.add_edge("generate_blanks", "format_output")
#     graph.add_edge("generate_matches", "format_output")
#     graph.add_edge("generate_qna", "format_output")


    graph.add_edge("format_output", END)
    
    return graph.compile()
