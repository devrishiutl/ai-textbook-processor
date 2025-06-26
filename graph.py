from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence, Dict, Optional
from langchain_core.messages import BaseMessage
import operator
import re
import logging

# Create logger for this module
logger = logging.getLogger(__name__)
from tools import (
    profanity_filter_tool,
    child_filter_tool,
    content_match_tool,
    generate_notes_tool,
    generate_qna_tool,
    generate_blanks_tool,
    generate_match_tool,
    vision_understand_tool,
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

def grade_validation_node(state):
    """Validate grade-level appropriateness"""
    logger.info("🎯 Step 2: Grade Level Validation...")
    
    # Debug logging for validation parameters
    logger.info(f"🔍 Validation Params: standard='{state.get('standard')}', subject='{state.get('subject')}', chapter='{state.get('chapter')}'")
    
    try:
        grade_check = grade_level_check_tool(
            state["content"], 
            state["standard"], 
            state["subject"], 
            state["chapter"]
        )
        logger.info(f"📊 Grade Level Check: {grade_check}")
        
        # Parse the AI response format
        is_failed = False
        
        if grade_check:
            grade_check_upper = grade_check.upper()
            lines = grade_check.split('\n')
            first_line = lines[0] if lines else ""
            
            # Check if AI returned template format instead of making a choice
            template_format_detected = "[APPROPRIATE/TOO ADVANCED/TOO SIMPLE]:" in first_line
            template_determined_appropriate = False
            
            if template_format_detected:
                logger.debug("🔍 Debug: AI returned template format, analyzing detailed response")
                
                # When AI returns template, use detailed analysis to determine appropriateness
                vocab_appropriate = "vocabulary used is appropriate" in grade_check.lower()
                concepts_suitable = "concepts presented are suitable" in grade_check.lower()
                vocab_violations_zero = "vocabulary violations: 0 detected" in grade_check.lower()
                
                if vocab_appropriate and concepts_suitable and vocab_violations_zero:
                    logger.debug("🔍 Debug: Template format but detailed analysis shows content is appropriate - PASSING")
                    is_failed = False
                    template_determined_appropriate = True
                    
            # Only run additional validation if we haven't already determined appropriateness from template
            if not template_determined_appropriate:
                # Check for explicit APPROPRIATE response first
                if "APPROPRIATE:" in first_line.upper():
                    is_failed = False
                    logger.debug("🔍 Debug: Found APPROPRIATE response - validation PASSED")
                else:
                    # Look for explicit failure indicators in AI response format
                    failure_indicators = ["TOO ADVANCED", "TOO SIMPLE", "INAPPROPRIATE"]
                    
                    # Check traditional format first (e.g., "TOO ADVANCED: Grade X content")
                    for indicator in failure_indicators:
                        if indicator in grade_check_upper:
                            # Look for patterns like "TOO ADVANCED: Grade" or "TOO SIMPLE: Grade"
                            if f"{indicator}:" in first_line.upper() or f"{indicator}]:" in first_line.upper():
                                is_failed = True
                                logger.debug(f"🔍 Debug: Setting failed=True because of '{indicator}' pattern in first line")
                                break
            
            # Check for automated analysis format indicating violations (only if not already determined appropriate)
            if not is_failed and "AUTOMATED ANALYSIS SUMMARY" in grade_check_upper and "APPROPRIATE:" not in first_line.upper():
                logger.debug("🔍 Debug: Found automated analysis format, checking for violations")
                
                # Look for violation indicators in the automated analysis
                violation_indicators = [
                    "VOCABULARY VIOLATIONS:",
                    "SENTENCE COMPLEXITY:",
                    "VIOLATIONS DETECTED",
                    "EXCEEDS GRADE",
                    "TOO COMPLEX",
                    "TOO ADVANCED"
                ]
                
                for violation in violation_indicators:
                    if violation in grade_check_upper:
                        # Check if it indicates actual violations (not zero)
                        if "VOCABULARY VIOLATIONS:" in grade_check_upper:
                            # Look for patterns like "Vocabulary Violations: 2 detected" or "Vocabulary Violations: 0 detected"
                            import re
                            violation_match = re.search(r'VOCABULARY VIOLATIONS:\s*(\d+)\s*DETECTED', grade_check_upper)
                            if violation_match and int(violation_match.group(1)) > 0:
                                is_failed = True
                                logger.debug(f"🔍 Debug: Setting failed=True because of vocabulary violations: {violation_match.group(1)}")
                                break
                        
                        if "SENTENCE COMPLEXITY:" in grade_check_upper and "EXCEEDS" in grade_check_upper:
                            # More nuanced check - don't fail if vocabulary and concepts are appropriate
                            vocab_appropriate = "vocabulary used is appropriate" in grade_check.lower()
                            concepts_suitable = "concepts presented are suitable" in grade_check.lower()
                            
                            if vocab_appropriate and concepts_suitable:
                                logger.debug("🔍 Debug: Sentence complexity issue detected, but vocabulary and concepts are appropriate - allowing with warning")
                                logger.debug(f"🔍 Debug: vocab_appropriate: {vocab_appropriate}, concepts_suitable: {concepts_suitable}")
                                # Don't set is_failed = True for this case
                            else:
                                is_failed = True
                                logger.debug("🔍 Debug: Setting failed=True because of sentence complexity violations")
                                logger.debug(f"🔍 Debug: vocab_appropriate: {vocab_appropriate}, concepts_suitable: {concepts_suitable}")
                                break
            

        
        logger.debug(f"🔍 Debug: Final validation result - is_failed: {is_failed}")
        
        if is_failed:
            logger.debug("🔍 Debug: Grade validation FAILED - stopping process")
            return {
                **state,
                "processing_status": "FAILED",
                "validation_results": {"grade_check": grade_check},
                "error_details": f"Content validation failed: {grade_check}"
            }
        
        logger.debug("🔍 Debug: Grade validation PASSED - continuing process")
        return {
            **state,
            "processing_status": "CONTINUE",
            "validation_results": {"grade_check": grade_check}
        }
        
    except Exception as e:
        logger.error(f"🔍 Debug: Grade validation ERROR: {e}")
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"Grade validation error: {str(e)}"
        }

def safety_check_router(state):
    """Router function for safety check results"""
    logger.debug("🔍 Debug: Safety router - checking state")
    
    validation_results = state.get("validation_results", {})
    safety_check = validation_results.get("safety_check", "")
    processing_status = state.get("processing_status", "UNKNOWN")
    
    logger.debug(f"🔍 Debug: Safety router - processing_status: {processing_status}")
    logger.debug(f"🔍 Debug: Safety router - safety_check: {safety_check}")
    
    # The safety_check_node already determined if content is safe and set processing_status
    # So we can trust the processing_status instead of re-parsing the safety_check string
    if processing_status == "FAILED":
        logger.debug("🔍 Debug: Safety router - FAILED due to processing status")
        return "failed"
    else:
        logger.debug("🔍 Debug: Safety router - CONTINUE to relevance check")
        return "continue"

def relevance_check_router(state):
    """Router function for relevance check results"""
    logger.debug("🔍 Debug: Relevance router - checking state")
    
    validation_results = state.get("validation_results", {})
    relevance_check = validation_results.get("content_match", "")
    processing_status = state.get("processing_status", "UNKNOWN")
    
    logger.debug(f"🔍 Debug: Relevance router - processing_status: {processing_status}")
    logger.debug(f"🔍 Debug: Relevance router - relevance_check: {relevance_check}")
    
    # Check for relevance issues
    if "NO_MATCH" in relevance_check or "MISMATCH" in relevance_check:
        logger.debug("🔍 Debug: Relevance router - FAILED due to no match")
        return "failed"
    elif processing_status == "FAILED":
        logger.debug("🔍 Debug: Relevance router - FAILED due to processing status")
        return "failed"
    else:
        logger.debug("🔍 Debug: Relevance router - CONTINUE to content generation")
        return "continue"

def safety_check_node(state):
    """Check content safety and appropriateness"""
    logger.info("🔍 Step 3: Content Safety Check...")
    
    try:
        profanity_check = profanity_filter_tool(state["content"])
        child_safety_check = child_filter_tool(state["content"])
        
        logger.debug(f"🔍 Debug: Profanity check: {profanity_check}")
        logger.debug(f"🔍 Debug: Child safety check: {child_safety_check}")
        
        safety_result = f"Profanity: {profanity_check} | Child-safe: {child_safety_check}"
        
        # Determine if content is safe
        is_safe = (
            "INAPPROPRIATE" not in profanity_check and 
            "INAPPROPRIATE" not in child_safety_check and
            ("APPROPRIATE" in child_safety_check or "CLEAN" in child_safety_check)
        )
        
        logger.debug(f"🔍 Debug: Safety result - is_safe: {is_safe}")
        
        processing_status = "CONTINUE" if is_safe else "FAILED"
        error_details = None if is_safe else f"Content safety failed: {safety_result}"
        
        # Update validation results
        validation_results = state.get("validation_results", {})
        validation_results["safety_check"] = safety_result
        
        if is_safe:
            logger.debug("🔍 Debug: Safety check PASSED - continuing process")
        else:
            logger.debug("🔍 Debug: Safety check FAILED - stopping process")
        
        return {
            **state,
            "validation_results": validation_results,
            "processing_status": processing_status,
            "error_details": error_details
        }
        
    except Exception as e:
        logger.error(f"🔍 Debug: Safety check ERROR: {e}")
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"Safety check error: {str(e)}"
        }

def content_relevance_node(state):
    """Verify subject and chapter relevance"""
    logger.info("🎯 Step 4: Subject/Chapter Relevance Check...")
    
    try:
        relevance_check = content_match_tool(
            state["content"], 
            state["subject"], 
            state["chapter"]
        )
        
        logger.debug(f"🔍 Debug: Relevance check result: {relevance_check}")
        
        # Determine if content is relevant
        is_relevant = (
            "MATCH" in relevance_check or 
            "PARTIAL_MATCH" in relevance_check
        )
        
        logger.debug(f"🔍 Debug: Relevance result - is_relevant: {is_relevant}")
        
        processing_status = "CONTINUE" if is_relevant else "FAILED"
        error_details = None if is_relevant else f"Content relevance failed: {relevance_check}"
        
        # Update validation results
        validation_results = state.get("validation_results", {})
        validation_results["content_match"] = relevance_check
        
        if is_relevant:
            logger.debug("🔍 Debug: Relevance check PASSED - continuing process")
        else:
            logger.debug("🔍 Debug: Relevance check FAILED - stopping process")
        
        return {
            **state,
            "validation_results": validation_results,
            "processing_status": processing_status,
            "error_details": error_details
        }
        
    except Exception as e:
        logger.error(f"🔍 Debug: Relevance check ERROR: {e}")
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"Relevance check error: {str(e)}"
        }

def content_normalization_node(state):
    """Normalize content for processing after validation passes"""
    logger.info("🔧 Step 5: Normalizing Content for Processing...")
    
    try:
        # Import here to avoid circular imports
        from tools import normalize_content_for_validation
        
        # Only normalize PDF content (images are already AI-processed and appropriate)
        # Check if this came from PDF processing by looking at sentence complexity
        original_content = state["content"]
        validation_results = state.get("validation_results", {})
        grade_check = validation_results.get("grade_check", "")
        
        # Check if normalization is needed (long sentences detected)
        needs_normalization = (
            "Maximum sentence length" in grade_check and 
            "exceeds grade level" in grade_check
        )
        
        if needs_normalization:
            logger.info("🔧 Applying content normalization for processing...")
            normalized_content = normalize_content_for_validation(original_content, state["standard"])
            
            return {
                **state,
                "content": normalized_content,  # Use normalized content for generation
                "original_content": original_content  # Keep original for reference
            }
        else:
            logger.info("🔧 Content normalization not needed - using original content")
            return {
                **state,
                "original_content": original_content  # Keep original for reference
            }
            
    except Exception as e:
        logger.error(f"🔧 Content normalization ERROR: {e}")
        # Continue with original content if normalization fails
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
        
        # Create comprehensive response
        comprehensive_response = f"""
GRADE LEVEL VALIDATION:
{validation_results.get('grade_check', 'Not performed')}

CONTENT SAFETY ANALYSIS:
{validation_results.get('safety_check', 'Not performed')}

CONTENT RELEVANCE CHECK:
{validation_results.get('content_match', 'Not performed')}

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

def grade_validation_router(state):
    """Router function for grade validation results"""
    status = state.get("processing_status", "UNKNOWN")
    
    if status == "FAILED":
        return "failed"
    elif status == "CONTINUE":
        return "continue"
    else:
        return "failed"  # Default to failed for safety

def build_graph():
    """Build comprehensive multi-node educational processing graph with proper conditional validation"""
    
    graph = StateGraph(AgentState)
    
    # Add all nodes
    graph.add_node("extract_content", content_extraction_node)
    graph.add_node("validate_grade", grade_validation_node)
    graph.add_node("check_safety", safety_check_node)
    graph.add_node("verify_relevance", content_relevance_node)
    graph.add_node("normalize_content", content_normalization_node)
    graph.add_node("generate_notes", generate_notes_node)
    graph.add_node("generate_blanks", generate_blanks_node)
    graph.add_node("generate_matches", generate_matches_node)
    graph.add_node("generate_qna", generate_qna_node)
    graph.add_node("format_output", output_formatter_node)
    
    # Define flow with ALL conditional validations
    graph.set_entry_point("extract_content")
    
    # Step 1: Extract content
    graph.add_edge("extract_content", "validate_grade")
    
    # Step 2: CONDITIONAL - Grade validation
    graph.add_conditional_edges(
        "validate_grade",
        grade_validation_router,
        {
            "continue": "check_safety",  # If grade validation passes
            "failed": END                # If grade validation fails → STOP
        }
    )
    
    # Step 3: CONDITIONAL - Safety check
    graph.add_conditional_edges(
        "check_safety",
        safety_check_router,
        {
            "continue": "verify_relevance",  # If safety check passes
            "failed": END                    # If content is unsafe → STOP
        }
    )
    
    # Step 4: CONDITIONAL - Relevance check
    graph.add_conditional_edges(
        "verify_relevance",
        relevance_check_router,
        {
            "continue": "normalize_content",  # If relevance check passes → normalize content
            "failed": END                     # If content is irrelevant → STOP
        }
    )
    
    # Step 5: Normalize content for processing (after validation passes)
    graph.add_edge("normalize_content", "generate_notes")
    
    # Step 6-9: Content generation pipeline (only if ALL validations pass)
    graph.add_edge("generate_notes", "generate_blanks")
    graph.add_edge("generate_blanks", "generate_matches")
    graph.add_edge("generate_matches", "generate_qna")
    
    # Step 10: Format and end
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
