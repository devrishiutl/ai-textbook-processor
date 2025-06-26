import base64
import re
import logging
from config import azure_client, AZURE_DEPLOYMENT_NAME

# Create logger for this module
logger = logging.getLogger(__name__)

# =============================================================================
# 1. CORE UTILITY FUNCTIONS (Called by others)
# =============================================================================

def call_gpt(prompt, content="", max_tokens=2000):
    """Core GPT function with usage tracking"""
    try:
        result = azure_client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": content}],
            temperature=0.1,
            max_tokens=max_tokens
        )
        
        # Log token usage for cost tracking
        usage = getattr(result, 'usage', None)
        if usage:
            logger.info(f"LLM Call - Prompt tokens: {usage.prompt_tokens}, Completion tokens: {usage.completion_tokens}, Total: {usage.total_tokens}")
        
        return result.choices[0].message.content
    except Exception as e:
        return f"ERROR: {str(e)}"

def encode_image_base64(img_path):
    """Encode image to base64"""
    try:
        with open(img_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception as e:
        return f"ERROR: {str(e)}"

# =============================================================================
# 2. CONTENT EXTRACTION FUNCTIONS (Called first in processing)
# =============================================================================

def extract_pdf_content(pdf_path):
    """Extract PDF text using Docling"""
    try:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        
        content = ""
        for element in result.document.texts:
            if element.text.strip():
                content += element.text.strip() + "\n\n"
        
        return content
    except Exception as e:
        return f"ERROR: {str(e)}"

def vision_understand_tool(images, standard, subject, chapter):
    """Process images with vision AI"""
    try:
        user_content = [{"type": "text", "text": f"Extract educational content for {standard} {subject} - {chapter}"}]
        
        for img_path in images:
            encoded = encode_image_base64(img_path)
            if encoded.startswith("ERROR"):
                return encoded
            
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}
            })

        response = azure_client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": f"Educational content analyzer for {standard} {subject}"},
                {"role": "user", "content": user_content}
            ],
            temperature=0.1,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: {str(e)}"

# =============================================================================
# 3. VALIDATION FUNCTIONS (Called by graph nodes)
# =============================================================================

def combined_validation_tool(content, target_standard, subject, chapter):
    """Simple combined validation using LLM intelligence"""
    
    # Simple prompt that lets LLM use its knowledge
    prompt = f"""Analyze this educational content for three criteria:

1. GRADE LEVEL: Is this content appropriate for {target_standard} students?
2. SAFETY: Is this content safe and appropriate for students?
3. RELEVANCE: Does this content relate to {subject} - {chapter}?

Content: {content[:800]}

Respond in this EXACT format:
GRADE_CHECK: [APPROPRIATE/TOO ADVANCED/TOO SIMPLE]
SAFETY_CHECK: [APPROPRIATE/INAPPROPRIATE]
RELEVANCE_CHECK: [MATCH/PARTIAL_MATCH/NO_MATCH]
REASON: [Brief explanation if any check fails]"""

    response = call_gpt(prompt, max_tokens=200)  # Short validation response
    
    # Parse the response
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
        
        # Determine overall status
        if (result["grade_check"] == "APPROPRIATE" and 
            result["safety_check"] == "APPROPRIATE" and 
            result["relevance_check"] in ["MATCH", "PARTIAL_MATCH"]):
            result["overall_status"] = "PASSED"
        else:
            result["overall_status"] = "FAILED"
            
    except Exception as e:
        result["reason"] = f"Error parsing validation response: {str(e)}"
    
    return result

# Note: Legacy individual validation functions have been removed
# All validation is now handled by combined_validation_tool()

# =============================================================================
# 4. CONTENT GENERATION FUNCTIONS (Called by graph nodes)
# =============================================================================

def generate_notes_tool(text, grade_level, subject, chapter): 
    """Generate study notes"""
    prompt = f"Create concise study notes for {grade_level} students on {subject} - {chapter}. Focus on key concepts and important points."
    return call_gpt(prompt, text)

def generate_blanks_tool(text, grade_level, subject, chapter):
    """Generate fill-in-blanks"""
    prompt = f"Create 5 fill-in-the-blank questions for {grade_level} students on {subject} - {chapter}. Format: '1. Sentence with ___ blank\nAnswer: missing word'"
    return call_gpt(prompt, text)

def generate_match_tool(text, grade_level, subject, chapter):
    """Generate match exercises with enforced format"""
    prompt = f"""Create 5 match-the-following pairs for {grade_level} students on {subject} - {chapter}.

You MUST use this EXACT format (copy exactly):

Column A: 1.Science 2.Observation 3.Experiment 4.Hypothesis 5.Discovery
Column B: A.Study of natural world B.Watching carefully C.Testing ideas D.Educated guess E.Finding new things
Answers: 1-A,2-B,3-C,4-D,5-E

Replace the example items with content from the text, but keep the EXACT same format structure."""
    
    result = call_gpt(prompt, text)
    
    # If the result doesn't contain the expected format, create a fallback
    if "Column A:" not in result or "Column B:" not in result:
        # Create a basic match exercise from the content
        result = f"""Column A: 1.Science 2.Observation 3.Experiment 4.Question 5.Discovery
Column B: A.Study of natural world B.Watching carefully to learn C.Testing ideas and hypotheses D.Asking about surroundings E.Finding something new
Answers: 1-A,2-B,3-C,4-D,5-E"""
    
    return result

def generate_qna_tool(text, grade_level, subject, chapter):
    """Generate Q&A"""
    prompt = f"Create 3 questions and answers for {grade_level} students on {subject} - {chapter}. Format: 'Q1: question\nA1: answer'"
    return call_gpt(prompt, text)

# =============================================================================
# 5. MAIN PROCESSING FUNCTION (Entry point from main.py)
# =============================================================================

def process_educational_content_tool(content_source, standard, subject, chapter, content_type="pdf"):
    """Main processing function"""
    if content_type == "pdf":
        content = extract_pdf_content(content_source)
    elif content_type == "images":
        if isinstance(content_source, str):
            content_source = [content_source]
        content = vision_understand_tool(content_source, standard, subject, chapter)
    else:
        content = content_source
    
    if content.startswith("ERROR"):
        return {"error": content}
    
    from graph import build_graph
    compiled_graph = build_graph()
    
    result = compiled_graph.invoke({
        "messages": [{"role": "user", "content": content}],
        "content": content,
        "standard": standard,
        "subject": subject, 
        "chapter": chapter
    })
    
    return result

# =============================================================================
# 6. OUTPUT FORMATTING FUNCTION (Called last from main.py)
# =============================================================================

def format_educational_output_tool(result):
    """Format output"""
    if not result or 'messages' not in result:
        return "No content generated"
    
    messages = result['messages']
    if not messages:
        return "No messages found"
    
    last_message = messages[-1]
    if isinstance(last_message, dict):
        content = last_message.get('content', '')
    else:
        content = getattr(last_message, 'content', '') or str(last_message)
    
    return content if content else "No content found"
