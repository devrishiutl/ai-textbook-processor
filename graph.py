"""
LangGraph Workflow for Educational Content Processing
"""
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from models.state import ProcessingState

logger = logging.getLogger(__name__)

def extract_content_node(state: ProcessingState) -> ProcessingState:
    """Extract content from files or messages - single source only"""
    try:
        state["processing_steps"].append("extract_content")
        
        # Extract parameters from messages
        messages = state.get("messages", [])
        from core.helpers import extract_content_from_messages
        content, standard, subject, chapter = extract_content_from_messages(messages)
        
        if content:
            # Content from messages
            state["content"] = content
            state["standard"] = standard
            state["subject"] = subject
            state["chapter"] = chapter
        else:
            # Extract from files - single source only
            pdf_path = state.get("pdf_path")
            image_paths = state.get("image_paths", [])
            
            # Validate single source requirement
            has_pdf = pdf_path is not None and pdf_path.strip()
            has_images = image_paths is not None and len(image_paths) > 0
            
            if has_pdf and has_images:
                state["error_message"] = "Only single source type allowed: provide either pdf_path OR image_paths, not both"
                return state
            
            if not has_pdf and not has_images:
                state["error_message"] = "Must provide either pdf_path OR image_paths"
                return state
            
            # Extract content based on source type
            if has_pdf:
                # PDF only
                from core.extractors import extract_content_from_pdf
                extracted_content = extract_content_from_pdf(pdf_path)
            else:
                # Images only - use vision processing
                from core.generators import generate_content_from_vision
                generated_content = generate_content_from_vision(image_paths, standard, subject, chapter)
                
                if not generated_content.get("success"):
                    state["error_message"] = generated_content.get("error", "Failed to process images")
                    return state
                
                # Extract content from vision results
                content_dict = generated_content.get("content", {})
                if isinstance(content_dict, dict):
                    notes = content_dict.get("importantNotes", "")
                    if notes and notes != "No content available to create study notes.":
                        extracted_content = notes
                    else:
                        state["error_message"] = "No meaningful content could be extracted from the images"
                        return state
                else:
                    state["error_message"] = "Invalid content structure from vision processing"
                    return state
            
            if extracted_content.startswith("ERROR"):
                state["error_message"] = extracted_content
                return state
            
            state["content"] = extracted_content
        
        return state
        
    except Exception as e:
        logger.error(f"Error in extract_content_node: {str(e)}")
        state["error_message"] = f"Error extracting content: {str(e)}"
        return state

def validate_content_node(state: ProcessingState) -> ProcessingState:
    """Validate extracted content"""
    try:
        state["processing_steps"].append("validate_content")
        
        content = state.get("content")
        standard = state.get("standard")
        subject = state.get("subject")
        chapter = state.get("chapter")
        
        if not all([content, standard, subject, chapter]):
            state["error_message"] = "Missing required parameters for validation"
            return state
        
        from core.validators import validate_educational_content
        validation_results = validate_educational_content(content, standard, subject, chapter)
        state["validation_results"] = validation_results
        
        return state
        
    except Exception as e:
        logger.error(f"Error in validate_content_node: {str(e)}")
        state["error_message"] = f"Error validating content: {str(e)}"
        return state

def generate_content_node(state: ProcessingState) -> ProcessingState:
    """Generate educational content"""
    try:
        state["processing_steps"].append("generate_content")
        
        content = state.get("content")
        standard = state.get("standard")
        subject = state.get("subject")
        chapter = state.get("chapter")
        
        if not all([content, standard, subject, chapter]):
            state["error_message"] = "Missing required parameters for generation"
            return state
        
        # Check if validation passed
        validation_results = state.get("validation_results", {})
        if validation_results.get("overall_status") != "PASSED":
            state["error_message"] = "Content validation failed"
            return state
        
        from core.generators import generate_educational_content, generate_comprehensive_output
        generated_content = generate_educational_content(content, standard, subject, chapter)
        
        # Generate comprehensive output
        comprehensive_output = generate_comprehensive_output(validation_results, generated_content)
        
        if comprehensive_output.get("success"):
            state["final_response"] = comprehensive_output
        else:
            state["error_message"] = comprehensive_output.get("error") or comprehensive_output.get("message") or "Processing failed"
        
        return state
        
    except Exception as e:
        logger.error(f"Error in generate_content_node: {str(e)}")
        state["error_message"] = f"Error generating content: {str(e)}"
        return state



def should_continue_to_validation(state: ProcessingState) -> str:
    """Determine if we should continue to validation"""
    if state.get("error_message"):
        return "error"
    return "continue"

def should_continue_to_generation(state: ProcessingState) -> str:
    """Determine if we should continue to generation"""
    if state.get("error_message"):
        return "error"
    return "continue"

def create_workflow() -> StateGraph:
    """Create the LangGraph workflow"""
    # Create the workflow
    workflow = StateGraph(ProcessingState)
    
    # Add nodes
    workflow.add_node("extract_content", extract_content_node)
    workflow.add_node("validate_content", validate_content_node)
    workflow.add_node("generate_content", generate_content_node)
    
    # Set entry point
    workflow.set_entry_point("extract_content")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "extract_content",
        should_continue_to_validation,
        {
            "continue": "validate_content",
            "error": END
        }
    )
    
    workflow.add_conditional_edges(
        "validate_content",
        should_continue_to_generation,
        {
            "continue": "generate_content",
            "error": END
        }
    )
    
    workflow.add_edge("generate_content", END)
    
    return workflow

# Create the workflow instance
workflow = create_workflow()
