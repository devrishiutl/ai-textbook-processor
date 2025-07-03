from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence, Dict, Optional
from langchain_core.messages import BaseMessage
import operator
import re
import logging

# Create logger for this module
logger = logging.getLogger(__name__)
from tools import (
    combined_validation_tool,
    generate_all_content_tool
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
    """Extract content and parameters"""
    messages = state["messages"]
    content = None
    standard = state.get('standard')
    subject = state.get('subject')
    chapter = state.get('chapter')
    
    for message in messages:
        if message.get("role") == "system":
            system_content = message.get("content", "")
            if "specializing in" in system_content and "for" in system_content:
                match = re.search(r'specializing in (.+?) for (.+?) students, focusing on (.+?)\.', system_content)
                if match and not all([subject, standard, chapter]):
                    subject = subject or match.group(1)
                    standard = standard or match.group(2) 
                    chapter = chapter or match.group(3)
        
        elif message.get("role") == "user" and message.get("content", "").startswith("Educational content to process:"):
            content = message.get("content", "").replace("Educational content to process:", "").strip()
    
    if not content:
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": "No educational content found"
        }
    
    return {
        **state,
        "content": content,
        "standard": standard,
        "subject": subject,
        "chapter": chapter,
        "processing_status": "CONTINUE"
    }

def comprehensive_validation_node(state):
    """Combined validation checks (grade, safety, relevance) in one LLM call"""
    try:
        validation_result = combined_validation_tool(
            state["content"], 
            state["standard"], 
            state["subject"], 
            state["chapter"]
        )
        
        # Handle error case
        if "error" in validation_result:
            return {
                **state,
                "processing_status": "FAILED",
                "validation_results": {
                    "grade_check": "ERROR",
                    "safety_check": "ERROR",
                    "relevance_check": "ERROR",
                    "status": "FAILED",
                    "reason": validation_result["error"]
                },
                "error_details": f"Validation error: {validation_result['error']}"
            }
        
        # Check overall status
        if validation_result["overall_status"] == "FAILED":
            return {
                **state,
                "processing_status": "FAILED",
                "validation_results": {
                    "grade_check": validation_result["grade_check"],
                    "safety_check": validation_result["safety_check"],
                    "relevance_check": validation_result["relevance_check"],
                    "status": "FAILED",
                    "reason": validation_result["reason"]
                },
                "error_details": f"Validation failed: {validation_result['reason']}"
            }
        
        # All validations passed
        return {
            **state,
            "processing_status": "CONTINUE",
            "validation_results": {
                "grade_check": validation_result["grade_check"],
                "safety_check": validation_result["safety_check"],
                "relevance_check": validation_result["relevance_check"],
                "status": "PASSED",
                "reason": "All validations passed"
            }
        }
        
    except Exception as e:
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"Validation error: {str(e)}"
        }

def validation_router(state):
    """Router for validation results"""
    processing_status = state.get("processing_status", "UNKNOWN")
    return "failed" if processing_status == "FAILED" else "continue"

# def content_normalization_node(state):
#     """Pass-through node"""
#     return {**state, "original_content": state["content"]}

def generate_all_content_node(state):
    """Generate all educational content in one LLM call"""
    try:
        # Generate all content at once
        all_content = generate_all_content_tool(
            state["content"], 
            state["standard"], 
            state["subject"], 
            state["chapter"]
        )
        
        # Store the raw content directly - let the formatter handle parsing
        generated_content = {
            "notes": all_content,  # Store raw content
            "blanks": all_content,  # Store raw content
            "matches": all_content,  # Store raw content
            "qna": all_content  # Store raw content
        }
        
        return {
            **state, 
            "generated_content": generated_content,
            "processing_status": "CONTINUE"
        }
        
    except Exception as e:
        return {
            **state,
            "processing_status": "FAILED",
            "error_details": f"Content generation error: {str(e)}"
        }

def output_formatter_node(state):
    """Format final output"""
    try:
        validation_results = state.get("validation_results", {})
        generated_content = state.get("generated_content", {})
        
        # Use the raw generated content directly
        raw_content = generated_content.get('notes', 'Not generated')
        
        comprehensive_response = f"""
COMPREHENSIVE VALIDATION RESULTS:
Grade Check: {validation_results.get('grade_check', 'Not performed')}
Safety Check: {validation_results.get('safety_check', 'Not performed')}
Relevance Check: {validation_results.get('relevance_check', 'Not performed')}
Overall Status: {validation_results.get('status', 'Unknown')}

{raw_content}
        """
        
        return {
            **state,
            "messages": state["messages"] + [{"role": "assistant", "content": comprehensive_response}]
        }
        
    except Exception as e:
        error_response = f"Output formatting failed: {str(e)}"
        return {
            **state,
            "messages": state["messages"] + [{"role": "assistant", "content": error_response}]
        }

def build_graph():
    """Build processing graph"""
    graph = StateGraph(AgentState)
    
    # Add nodes - removed content_extraction_node as it's unnecessary
    graph.add_node("comprehensive_validation", comprehensive_validation_node)
    # graph.add_node("normalize_content", content_normalization_node)
    graph.add_node("generate_all_content", generate_all_content_node)
    graph.add_node("format_output", output_formatter_node)
    
    # Define flow - start directly with validation
    graph.set_entry_point("comprehensive_validation")

    graph.add_conditional_edges(
        "comprehensive_validation",
        validation_router,
        {
            "continue": "generate_all_content",
            "failed": END
        }
    )    
    # graph.add_conditional_edges(
    #     "comprehensive_validation",
    #     validation_router,
    #     {
    #         "continue": "normalize_content",
    #         "failed": END
    #     }
    # )
    
    # graph.add_edge("normalize_content", "generate_all_content")
    graph.add_edge("generate_all_content", "format_output")
    graph.add_edge("format_output", END)
    
    return graph.compile()
