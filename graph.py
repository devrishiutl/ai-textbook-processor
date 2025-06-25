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
        
        # Check if content is appropriate
        if grade_check and ("TOO ADVANCED" in grade_check or "TOO SIMPLE" in grade_check or "MISMATCH" in grade_check):
            return {
                **state,
                "processing_status": "FAILED",
                "validation_results": {"grade_check": grade_check},
                "error_details": f"Content validation failed: {grade_check}"
            }
        
        return {
            **state,
            "processing_status": "CONTINUE",
            "validation_results": {"grade_check": grade_check}
        }
        
    except Exception as e:
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"Grade validation error: {str(e)}"
        }

def safety_check_router(state):
    """Router function for safety check results"""
    validation_results = state.get("validation_results", {})
    safety_check = validation_results.get("safety_check", "")
    
    # Check for safety issues
    if "INAPPROPRIATE" in safety_check or "profanity" in safety_check.lower():
        return "failed"
    elif state.get("processing_status") == "FAILED":
        return "failed"
    else:
        return "continue"

def relevance_check_router(state):
    """Router function for relevance check results"""
    validation_results = state.get("validation_results", {})
    relevance_check = validation_results.get("content_match", "")
    
    # Check for relevance issues
    if "NO_MATCH" in relevance_check or "MISMATCH" in relevance_check:
        return "failed"
    elif state.get("processing_status") == "FAILED":
        return "failed"
    else:
        return "continue"

def safety_check_node(state):
    """Check content safety and appropriateness"""
    print("🔍 Step 3: Content Safety Check...")
    
    try:
        profanity_check = profanity_filter_tool(state["content"])
        child_safety_check = child_filter_tool(state["content"])
        
        safety_result = f"Profanity: {profanity_check} | Child-safe: {child_safety_check}"
        
        # Determine if content is safe
        is_safe = (
            "INAPPROPRIATE" not in profanity_check and 
            "INAPPROPRIATE" not in child_safety_check and
            "Yes" in child_safety_check
        )
        
        processing_status = "CONTINUE" if is_safe else "FAILED"
        error_details = None if is_safe else f"Content safety failed: {safety_result}"
        
        # Update validation results
        validation_results = state.get("validation_results", {})
        validation_results["safety_check"] = safety_result
        
        return {
            **state,
            "validation_results": validation_results,
            "processing_status": processing_status,
            "error_details": error_details
        }
        
    except Exception as e:
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
        
        # Determine if content is relevant
        is_relevant = (
            "MATCH" in relevance_check or 
            "PARTIAL_MATCH" in relevance_check
        )
        
        processing_status = "CONTINUE" if is_relevant else "FAILED"
        error_details = None if is_relevant else f"Content relevance failed: {relevance_check}"
        
        # Update validation results
        validation_results = state.get("validation_results", {})
        validation_results["content_match"] = relevance_check
        
        return {
            **state,
            "validation_results": validation_results,
            "processing_status": processing_status,
            "error_details": error_details
        }
        
    except Exception as e:
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
        
        generated_content = state.get("generated_content", {})
        generated_content["notes"] = notes
        
        return {
            **state,
            "generated_content": generated_content
        }
        
    except Exception as e:
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
        
        generated_content = state.get("generated_content", {})
        generated_content["blanks"] = blanks
        
        return {
            **state,
            "generated_content": generated_content
        }
        
    except Exception as e:
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
        
        generated_content = state.get("generated_content", {})
        generated_content["matches"] = matches
        
        return {
            **state,
            "generated_content": generated_content
        }
        
    except Exception as e:
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
        
        generated_content = state.get("generated_content", {})
        generated_content["qna"] = qna
        
        return {
            **state,
            "generated_content": generated_content
        }
        
    except Exception as e:
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
        
        return {
            **state,
            "messages": state["messages"] + [{"role": "assistant", "content": comprehensive_response}]
        }
        
    except Exception as e:
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
