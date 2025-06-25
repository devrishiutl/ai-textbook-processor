from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence, Dict, Optional
from langchain_core.messages import BaseMessage
import operator
import re
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
    print("📄 Step 1: Content Extraction...")
    
    messages = state["messages"]
    content = None
    standard = None
    subject = None
    chapter = None
    
    # Extract parameters from system message
    for message in messages:
        if message.get("role") == "system":
            system_content = message.get("content", "")
            if "specializing in" in system_content and "for" in system_content:
                match = re.search(r'specializing in (.+?) for (.+?) students, focusing on (.+?)\.', system_content)
                if match:
                    subject = match.group(1)
                    standard = match.group(2) 
                    chapter = match.group(3)
        
        # Extract main content
        elif message.get("role") == "user" and message.get("content", "").startswith("Educational content to process:"):
            content = message.get("content", "").replace("Educational content to process:", "").strip()
    
    if not content:
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": "No educational content found to process"
        }
    
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
    print("🎯 Step 2: Grade Level Validation...")
    
    try:
        grade_check = grade_level_check_tool(
            state["content"], 
            state["standard"], 
            state["subject"], 
            state["chapter"]
        )
        print(f"📊 Grade Level Check: {grade_check}")
        
        # Parse the AI response format
        is_failed = False
        
        if grade_check:
            # Check if the AI response indicates failure
            grade_check_upper = grade_check.upper()
            
            # Look for explicit failure indicators
            failure_indicators = ["TOO ADVANCED", "TOO SIMPLE", "INAPPROPRIATE"]
            
            # Check if any failure indicators appear in the response
            for indicator in failure_indicators:
                if indicator in grade_check_upper:
                    # Make sure it's not just part of the template format
                    # Check if it appears as the actual chosen option
                    lines = grade_check.split('\n')
                    first_line = lines[0] if lines else ""
                    
                    print(f"🔍 Debug: Found '{indicator}' in response. First line: '{first_line}'")
                    
                    # Look for patterns like "TOO ADVANCED: Grade" or "TOO SIMPLE: Grade"
                    if f"{indicator}:" in first_line.upper() or f"{indicator}]:" in first_line.upper():
                        is_failed = True
                        print(f"🔍 Debug: Setting failed=True because of '{indicator}' pattern")
                        break
            
            # Additional check: if the response starts with the template format,
            # assume it's appropriate unless explicitly stated otherwise
            if "[APPROPRIATE/TOO ADVANCED/TOO SIMPLE]:" in grade_check:
                print("🔍 Debug: Found template format, assuming appropriate")
                # This means AI didn't choose an option, which usually means it's acceptable
                # but we should still check for explicit failure language
                if not any(f"{indicator}:" in grade_check_upper for indicator in failure_indicators):
                    is_failed = False
                    print("🔍 Debug: No explicit failure indicators, setting failed=False")
        
        print(f"🔍 Debug: Final validation result - is_failed: {is_failed}")
        
        if is_failed:
            print("🔍 Debug: Grade validation FAILED - stopping process")
            return {
                **state,
                "processing_status": "FAILED",
                "validation_results": {"grade_check": grade_check},
                "error_details": f"Content validation failed: {grade_check}"
            }
        
        print("🔍 Debug: Grade validation PASSED - continuing process")
        return {
            **state,
            "processing_status": "CONTINUE",
            "validation_results": {"grade_check": grade_check}
        }
        
    except Exception as e:
        print(f"🔍 Debug: Grade validation ERROR: {e}")
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"Grade validation error: {str(e)}"
        }

def safety_check_router(state):
    """Router function for safety check results"""
    print("🔍 Debug: Safety router - checking state")
    
    validation_results = state.get("validation_results", {})
    safety_check = validation_results.get("safety_check", "")
    processing_status = state.get("processing_status", "UNKNOWN")
    
    print(f"🔍 Debug: Safety router - processing_status: {processing_status}")
    print(f"🔍 Debug: Safety router - safety_check: {safety_check}")
    
    # The safety_check_node already determined if content is safe and set processing_status
    # So we can trust the processing_status instead of re-parsing the safety_check string
    if processing_status == "FAILED":
        print("🔍 Debug: Safety router - FAILED due to processing status")
        return "failed"
    else:
        print("🔍 Debug: Safety router - CONTINUE to relevance check")
        return "continue"

def relevance_check_router(state):
    """Router function for relevance check results"""
    print("🔍 Debug: Relevance router - checking state")
    
    validation_results = state.get("validation_results", {})
    relevance_check = validation_results.get("content_match", "")
    processing_status = state.get("processing_status", "UNKNOWN")
    
    print(f"🔍 Debug: Relevance router - processing_status: {processing_status}")
    print(f"🔍 Debug: Relevance router - relevance_check: {relevance_check}")
    
    # Check for relevance issues
    if "NO_MATCH" in relevance_check or "MISMATCH" in relevance_check:
        print("🔍 Debug: Relevance router - FAILED due to no match")
        return "failed"
    elif processing_status == "FAILED":
        print("🔍 Debug: Relevance router - FAILED due to processing status")
        return "failed"
    else:
        print("🔍 Debug: Relevance router - CONTINUE to content generation")
        return "continue"

def safety_check_node(state):
    """Check content safety and appropriateness"""
    print("🔍 Step 3: Content Safety Check...")
    
    try:
        profanity_check = profanity_filter_tool(state["content"])
        child_safety_check = child_filter_tool(state["content"])
        
        print(f"🔍 Debug: Profanity check: {profanity_check}")
        print(f"🔍 Debug: Child safety check: {child_safety_check}")
        
        safety_result = f"Profanity: {profanity_check} | Child-safe: {child_safety_check}"
        
        # Determine if content is safe
        is_safe = (
            "INAPPROPRIATE" not in profanity_check and 
            "INAPPROPRIATE" not in child_safety_check and
            ("APPROPRIATE" in child_safety_check or "CLEAN" in child_safety_check)
        )
        
        print(f"🔍 Debug: Safety result - is_safe: {is_safe}")
        
        processing_status = "CONTINUE" if is_safe else "FAILED"
        error_details = None if is_safe else f"Content safety failed: {safety_result}"
        
        # Update validation results
        validation_results = state.get("validation_results", {})
        validation_results["safety_check"] = safety_result
        
        if is_safe:
            print("🔍 Debug: Safety check PASSED - continuing process")
        else:
            print("🔍 Debug: Safety check FAILED - stopping process")
        
        return {
            **state,
            "validation_results": validation_results,
            "processing_status": processing_status,
            "error_details": error_details
        }
        
    except Exception as e:
        print(f"🔍 Debug: Safety check ERROR: {e}")
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"Safety check error: {str(e)}"
        }

def content_relevance_node(state):
    """Verify subject and chapter relevance"""
    print("🎯 Step 4: Subject/Chapter Relevance Check...")
    
    try:
        relevance_check = content_match_tool(
            state["content"], 
            state["subject"], 
            state["chapter"]
        )
        
        print(f"🔍 Debug: Relevance check result: {relevance_check}")
        
        # Determine if content is relevant
        is_relevant = (
            "MATCH" in relevance_check or 
            "PARTIAL_MATCH" in relevance_check
        )
        
        print(f"🔍 Debug: Relevance result - is_relevant: {is_relevant}")
        
        processing_status = "CONTINUE" if is_relevant else "FAILED"
        error_details = None if is_relevant else f"Content relevance failed: {relevance_check}"
        
        # Update validation results
        validation_results = state.get("validation_results", {})
        validation_results["content_match"] = relevance_check
        
        if is_relevant:
            print("🔍 Debug: Relevance check PASSED - continuing process")
        else:
            print("🔍 Debug: Relevance check FAILED - stopping process")
        
        return {
            **state,
            "validation_results": validation_results,
            "processing_status": processing_status,
            "error_details": error_details
        }
        
    except Exception as e:
        print(f"🔍 Debug: Relevance check ERROR: {e}")
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"Relevance check error: {str(e)}"
        }

def generate_notes_node(state):
    """Generate study notes"""
    print("📝 Step 5: Generating Study Notes...")
    
    try:
        notes = generate_notes_tool(
            state["content"], 
            state["standard"], 
            state["subject"], 
            state["chapter"]
        )
        
        print(f"🔍 Debug: Generated notes - {len(notes)} characters")
        
        generated_content = state.get("generated_content", {})
        generated_content["notes"] = notes
        
        print("🔍 Debug: Notes generation COMPLETED - continuing to blanks")
        
        return {
            **state,
            "generated_content": generated_content
        }
        
    except Exception as e:
        print(f"🔍 Debug: Notes generation ERROR: {e}")
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"Notes generation error: {str(e)}"
        }

def generate_blanks_node(state):
    """Generate fill-in-the-blanks"""
    print("📋 Step 6: Creating Fill-in-Blanks...")
    
    try:
        blanks = generate_blanks_tool(
            state["content"], 
            state["standard"], 
            state["subject"], 
            state["chapter"]
        )
        
        print(f"🔍 Debug: Generated blanks - {len(blanks)} characters")
        
        generated_content = state.get("generated_content", {})
        generated_content["blanks"] = blanks
        
        print("🔍 Debug: Blanks generation COMPLETED - continuing to matches")
        
        return {
            **state,
            "generated_content": generated_content
        }
        
    except Exception as e:
        print(f"🔍 Debug: Blanks generation ERROR: {e}")
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"Blanks generation error: {str(e)}"
        }

def generate_matches_node(state):
    """Generate match-the-following"""
    print("🔗 Step 7: Designing Match-the-Following...")
    
    try:
        matches = generate_match_tool(
            state["content"], 
            state["standard"], 
            state["subject"], 
            state["chapter"]
        )
        
        print(f"🔍 Debug: Generated matches - {len(matches)} characters")
        
        generated_content = state.get("generated_content", {})
        generated_content["matches"] = matches
        
        print("🔍 Debug: Matches generation COMPLETED - continuing to Q&A")
        
        return {
            **state,
            "generated_content": generated_content
        }
        
    except Exception as e:
        print(f"🔍 Debug: Matches generation ERROR: {e}")
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"Matches generation error: {str(e)}"
        }

def generate_qna_node(state):
    """Generate subjective questions with drawing capabilities"""
    print("❓ Step 8: Formulating Questions...")
    
    try:
        qna = generate_qna_tool(
            state["content"], 
            state["standard"], 
            state["subject"], 
            state["chapter"]
        )
        
        print(f"🔍 Debug: Generated Q&A - {len(qna)} characters")
        
        generated_content = state.get("generated_content", {})
        generated_content["qna"] = qna
        
        print("🔍 Debug: Q&A generation COMPLETED - continuing to output formatting")
        
        return {
            **state,
            "generated_content": generated_content
        }
        
    except Exception as e:
        print(f"🔍 Debug: Q&A generation ERROR: {e}")
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"QNA generation error: {str(e)}"
        }

def output_formatter_node(state):
    """Format final output"""
    print("📋 Step 9: Formatting Output...")
    
    try:
        validation_results = state.get("validation_results", {})
        generated_content = state.get("generated_content", {})
        
        print(f"🔍 Debug: Validation results keys: {list(validation_results.keys())}")
        print(f"🔍 Debug: Generated content keys: {list(generated_content.keys())}")
        
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
        
        print(f"🔍 Debug: Created comprehensive response - {len(comprehensive_response)} characters")
        print("🔍 Debug: Output formatting COMPLETED - adding assistant message")
        
        return {
            **state,
            "messages": state["messages"] + [{"role": "assistant", "content": comprehensive_response}]
        }
        
    except Exception as e:
        print(f"🔍 Debug: Output formatting ERROR: {e}")
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
            "continue": "generate_notes",  # If relevance check passes
            "failed": END                  # If content is irrelevant → STOP
        }
    )
    
    # Step 5-8: Content generation pipeline (only if ALL validations pass)
    graph.add_edge("generate_notes", "generate_blanks")
    graph.add_edge("generate_blanks", "generate_matches")
    graph.add_edge("generate_matches", "generate_qna")
    
    # Step 9: Format and end
    graph.add_edge("generate_qna", "format_output")
    graph.add_edge("format_output", END)
    
    return graph.compile()
