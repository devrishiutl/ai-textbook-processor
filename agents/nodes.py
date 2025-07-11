"""
Simple Graph Nodes
"""
from typing import Dict, Any
from config.configuration import get_validation_llm, get_generation_llm
from config.logging import get_logger
from langsmith import traceable
import re
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
        print(1)
        # Log token usage for cost tracking
        if hasattr(response, 'usage'):
            usage = response.usage
            logger.info(f"Validation tokens - Input: {usage.prompt_tokens}, Output: {usage.completion_tokens}, Total: {usage.total_tokens}")
        
        # Extract JSON
        start = result.find('{')
        end = result.rfind('}')
        if start != -1 and end != -1:
            json_str = result[start:end+1]
            json_str = re.sub(r'\\(?=\(|\))', r'\\\\', json_str)
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
        import traceback
        error_details = f"Validation error: {str(e)}\nFull traceback:\n{traceback.format_exc()}"
        state["error"] = f"Validation error: {str(e)}"
        state["validation_result"] = "ERROR"
        logger.error(error_details)
    
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
    
    # Create JSON template as a separate string to avoid escape issues
    json_template = '''{
    "importantNotes": "Study notes with markdown formatting",
    "criticalWords": {
        "flashcards": {
            "1": {
                "term": "Key Term 1",
                "definition": "Clear and concise definition of the term",
                "example": "Example or usage of the term"
            },
            "2": {
                "term": "Key Term 2", 
                "definition": "Clear and concise definition of the term",
                "example": "Example or usage of the term"
            },
            "3": {
                "term": "Key Term 3",
                "definition": "Clear and concise definition of the term", 
                "example": "Example or usage of the term"
            },
            "4": {
                "term": "Key Term 4",
                "definition": "Clear and concise definition of the term",
                "example": "Example or usage of the term"
            },
            "5": {
                "term": "Key Term 5",
                "definition": "Clear and concise definition of the term",
                "example": "Example or usage of the term"
            }
        }
    },
    "mcq": {
        "questions": {
            "1": {
                "question": "What is the main topic of this chapter?",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "A",
                "explanation": "Brief explanation of why this is correct"
            },
            "2": {
                "question": "Which of the following is correct?",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "B",
                "explanation": "Brief explanation of why this is correct"
            },
            "3": {
                "question": "Identify the correct statement:",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "C",
                "explanation": "Brief explanation of why this is correct"
            },
            "4": {
                "question": "Choose the best answer:",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "D",
                "explanation": "Brief explanation of why this is correct"
            },
            "5": {
                "question": "Select the correct option:",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "A",
                "explanation": "Brief explanation of why this is correct"
            }
        }
    },
    "fillInTheBlanks": {
        "questions": {"1": "Question 1", "2": "Question 2", "3": "Question 3", "4": "Question 4", "5": "Question 5"},
        "answers": {"1": "answer1", "2": "answer2", "3": "answer3", "4": "answer4", "5": "answer5"}
    },
    "matchTheFollowing": {
        "column_a": {"1": "Term 1", "2": "Term 2", "3": "Term 3", "4": "Term 4", "5": "Term 5"},
        "column_b": {"A": "Definition A", "B": "Definition B", "C": "Definition C", "D": "Definition D", "E": "Definition E"},
        "answers": {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E"}
    },
    "questionAnswer": {
        "questions": {"Q1": "Question 1?", "Q2": "Question 2?", "Q3": "Question 3?"},
        "answers": {"Q1": "Answer 1", "Q2": "Answer 2", "Q3": "Answer 3"}
    }
}'''
    
    prompt = f"""Create educational materials for {standard} {subject} - {chapter}.

Content: {content_for_generation}

Return valid JSON **only**, wrapped inside a Markdown JSON code block like this:

```json
{json_template}"""

    try:
        llm = get_generation_llm()
        print(2)
        response = llm.invoke(prompt)
        result = response.content
        print(3)
        # Log token usage for cost tracking
        if hasattr(response, 'usage'):
            usage = response.usage
            logger.info(f"Generation tokens - Input: {usage.prompt_tokens}, Output: {usage.completion_tokens}, Total: {usage.total_tokens}")
        print(4)
        # Extract JSON
        start = result.find('{')
        end = result.rfind('}')
        if start != -1 and end != -1:
            json_str = result[start:end+1]
            
            # 🛠 Fix LaTeX and invalid backslashes
            json_str = json_str.replace('\\', '\\\\')
            
            import json
            generated_json = json.loads(json_str)
            
            state["generated_content"] = generated_json
            state["success"] = True
            logger.info("Content generation completed successfully")
            print(6)
        else:
            state["error"] = "Failed to generate valid JSON"
            logger.error("Failed to generate valid JSON")
            print(7)
    except Exception as e:
        import traceback
        error_details = f"Generation error: {str(e)}\nFull traceback:\n{traceback.format_exc()}"
        state["error"] = f"Generation error: {str(e)}"
        logger.error(error_details)
        logger.error(f"Prompt that caused error: {prompt[:500]}...")  # Log first 500 chars of prompt
        print(8)
    return state 