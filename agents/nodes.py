"""
Simple Graph Nodes
"""
from typing import Dict, Any
from config.configuration import get_validation_llm, get_generation_llm
from config.logging import get_logger
from langsmith import traceable

logger = get_logger(__name__)

@traceable(name="content_validation")
def validate_content(state: Dict[str, Any]) -> Dict[str, Any]:
    """Validate content"""
    content = state.get("content", "")
    standard = state.get("standard", "")
    subject = state.get("subject", "")
    chapter = state.get("chapter", "")
    
    logger.info(f"Starting validation for {standard} {subject} - {chapter}")
    
    # Prepare content
    content_for_validation = content[:1000]
    
    prompt = f"""Analyze this content for {standard} {subject} - {chapter}:

Content: {content_for_validation}

Return valid JSON with this structure:
{{
    "grade_check": "APPROPRIATE/TOO ADVANCED/TOO SIMPLE",
    "safety_check": "APPROPRIATE/INAPPROPRIATE", 
    "relevance_check": "MATCH/PARTIAL_MATCH/NO_MATCH",
    "reason": "Brief explanation of the validation result"
}}"""

    try:
        llm = get_validation_llm()
        response = llm.invoke(prompt)
        result = response.content
        
        # Log token usage for cost tracking
        if hasattr(response, 'usage'):
            usage = response.usage
            logger.info(f"Validation tokens - Input: {usage.prompt_tokens}, Output: {usage.completion_tokens}, Total: {usage.total_tokens}")
        
        # Extract JSON
        start = result.find('{')
        end = result.rfind('}')
        if start != -1 and end != -1:
            json_str = result[start:end+1]
            import json
            validation_json = json.loads(json_str)
            
            # Store validation results
            state["validation_result"] = validation_json
            
            # Check if validation passed
            if (validation_json.get("grade_check") == "APPROPRIATE" and 
                validation_json.get("safety_check") == "APPROPRIATE" and 
                validation_json.get("relevance_check") == "MATCH"):
                state["is_valid"] = True
                logger.info("Validation passed")
            else:
                reason = validation_json.get("reason", "Validation failed")
                state["error"] = f"Content validation failed: {reason}"
                logger.warning(f"Validation failed: {reason}")
        else:
            state["error"] = "Failed to generate valid validation JSON"
            state["validation_result"] = "ERROR"
            
    except Exception as e:
        state["error"] = f"Validation error: {str(e)}"
        state["validation_result"] = "ERROR"
        logger.error(f"Validation error: {str(e)}")
    
    return state

@traceable(name="educational_content_generation")
def generate_content(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate content"""
    # Check if validation passed
    if not state.get("is_valid"):
        logger.warning("Skipping content generation - validation failed")
        return state
    
    content = state.get("content", "")
    standard = state.get("standard", "")
    subject = state.get("subject", "")
    chapter = state.get("chapter", "")
    
    logger.info(f"Starting content generation for {standard} {subject} - {chapter}")
    
    # Prepare content
    content_for_generation = content[:30000]
    
    prompt = f"""Create educational materials for {standard} {subject} - {chapter}.

Content: {content_for_generation}

Return valid JSON with this structure:
{{
    "importantNotes": "Study notes with markdown formatting",
    "fillInTheBlanks": {{
        "questions": {{"1": "Question 1", "2": "Question 2", "3": "Question 3", "4": "Question 4", "5": "Question 5"}},
        "answers": {{"1": "answer1", "2": "answer2", "3": "answer3", "4": "answer4", "5": "answer5"}}
    }},
    "matchTheFollowing": {{
        "column_a": {{"1": "Term 1", "2": "Term 2", "3": "Term 3", "4": "Term 4", "5": "Term 5"}},
        "column_b": {{"A": "Definition A", "B": "Definition B", "C": "Definition C", "D": "Definition D", "E": "Definition E"}},
        "answers": {{"1": "A", "2": "B", "3": "C", "4": "D", "5": "E"}}
    }},
    "questionAnswer": {{
        "questions": {{"Q1": "Question 1?", "Q2": "Question 2?", "Q3": "Question 3?"}},
        "answers": {{"Q1": "Answer 1", "Q2": "Answer 2", "Q3": "Answer 3"}}
    }}
}}"""

    try:
        llm = get_generation_llm()
        response = llm.invoke(prompt)
        result = response.content
        
        # Log token usage for cost tracking
        if hasattr(response, 'usage'):
            usage = response.usage
            logger.info(f"Generation tokens - Input: {usage.prompt_tokens}, Output: {usage.completion_tokens}, Total: {usage.total_tokens}")
        
        # Extract JSON
        start = result.find('{')
        end = result.rfind('}')
        if start != -1 and end != -1:
            json_str = result[start:end+1]
            import json
            generated_json = json.loads(json_str)
            state["generated_content"] = generated_json
            state["success"] = True
            logger.info("Content generation completed successfully")
        else:
            state["error"] = "Failed to generate valid JSON"
            logger.error("Failed to generate valid JSON")
            
    except Exception as e:
        state["error"] = f"Generation error: {str(e)}"
        logger.error(f"Generation error: {str(e)}")
    
    return state 