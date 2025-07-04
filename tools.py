import base64
import re
import logging
from config import azure_client, AZURE_DEPLOYMENT_NAME
from PIL import Image
import io

try:
    from langsmith.run_helpers import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    # Create a dummy decorator if LangSmith is not available
    def traceable(name=None):
        def decorator(func):
            return func
        return decorator
    LANGSMITH_AVAILABLE = False

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



# =============================================================================
# 2. CONTENT EXTRACTION FUNCTIONS (Called first in processing)
# =============================================================================
@traceable(name="pdf_content_extraction")
def extract_pdf_content(pdf_path):
    """Extract PDF text using Tika first, Docling as fallback"""
    try:
        # Try Tika first (fast and reliable)
        logger.info(f"Trying Tika extraction first for: {pdf_path}")
        tika_result = extract_pdf_content_tika_fallback(pdf_path)
        
        # If Tika succeeds and extracts good content, use it
        if not tika_result.startswith("ERROR") and len(tika_result.strip()) > 1000:
            logger.info(f"Tika extraction successful: {len(tika_result)} characters")
            return tika_result
        
        # If Tika fails or extracts insufficient content, try Docling
        logger.warning("Tika failed or extracted insufficient content, trying Docling")
        return extract_pdf_content_docling(pdf_path)
        
    except Exception as e:
        logger.warning(f"Tika extraction failed: {str(e)}, trying Docling fallback")
        return extract_pdf_content_docling(pdf_path)

def extract_pdf_content_tika_fallback(pdf_path: str) -> str:
    """Primary PDF extraction using Tika (fast and reliable)"""
    try:
        # Try to import and use Tika
        from tika_extractor import extract_pdf_content_tika, is_tika_available
        
        if not is_tika_available():
            return "ERROR: Tika extraction failed. Tika server not available."
        
        logger.info(f"Extracting text from PDF using Tika: {pdf_path}")
        result = extract_pdf_content_tika(pdf_path)
        
        if result.startswith("ERROR"):
            return f"ERROR: Tika extraction failed: {result}"
        
        logger.info(f"Tika extraction successful: {len(result)} characters")
        return result
        
    except ImportError:
        return "ERROR: Tika extraction failed. Tika module not available."
    except Exception as e:
        return f"ERROR: Tika extraction failed: {str(e)}"

def extract_pdf_content_docling(pdf_path):
    """Fallback PDF extraction using Docling (for complex cases)"""
    try:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        
        content = ""
        for element in result.document.texts:
            if element.text.strip():
                content += element.text.strip() + "\n\n"
        
        if not content or len(content.strip()) < 50:
            return "ERROR: Docling extracted insufficient content"
        
        logger.info(f"Docling extraction successful: {len(content)} characters")
        return content
        
    except Exception as e:
        logger.error(f"Docling extraction failed: {str(e)}")
        return f"ERROR: Docling extraction failed - {str(e)}"

def preprocess_image(image_path: str, target_size=(800, 800), quality=85) -> str:
    """
    Preprocess image before sending to LLM:
    1. Resize while maintaining aspect ratio
    2. Optimize quality
    3. Convert to base64
    
    Args:
        image_path: Path to image file
        target_size: Maximum dimensions (width, height)
        quality: JPEG quality (0-100)
    
    Returns:
        Base64 encoded optimized image or error message
    """
    try:
        # Open image with PIL
        img = Image.open(image_path)
        
        # Calculate aspect ratio preserving resize dimensions
        aspect_ratio = img.width / img.height
        if aspect_ratio > 1:
            # Width is larger
            new_width = min(img.width, target_size[0])
            new_height = int(new_width / aspect_ratio)
        else:
            # Height is larger
            new_height = min(img.height, target_size[1])
            new_width = int(new_height * aspect_ratio)
            
        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Save to bytes with quality optimization
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return encoded
    except Exception as e:
        return f"ERROR: Image preprocessing failed - {str(e)}"

@traceable(name="image_vision_processing")
def vision_understand_tool(images, standard, subject, chapter):
    """Process images with vision AI"""
    try:
        # Fixed prompt: Extract ACTUAL content from images, not generate based on subject/chapter
        user_content = [{"type": "text", "text": "Extract all educational content from these images. Describe exactly what you see - text, diagrams, concepts, topics, etc. Do not generate new content, only describe what is actually present in the images."}]
        
        for img_path in images:
            # Preprocess image before encoding
            encoded = preprocess_image(
                img_path,
                target_size=(800, 800),  # Max dimensions while maintaining aspect ratio
                quality=85  # Good balance between quality and size
            )
            
            if encoded.startswith("ERROR"):
                return encoded
            
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}
            })

        response = azure_client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are an educational content extractor. Extract and describe only the actual content present in the images."},
                {"role": "user", "content": user_content}
            ],
            temperature=0.1,
            max_tokens=3000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: {str(e)}"

# =============================================================================
# 3. VALIDATION FUNCTIONS (Called by graph nodes)
# =============================================================================

@traceable(name="content_validation")
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

@traceable(name="educational_content_generation")
def generate_all_content_tool(text, grade_level, subject, chapter):
    """Generate all educational content in one LLM call"""
    prompt = f"""Based on the following educational content, create comprehensive study materials for {grade_level} students.

Use ONLY the content provided below. Do not add information that is not present in the source material.

You MUST generate ALL four sections below. DO NOT skip any section. Each section must be complete with actual content.

STUDY NOTES:
[Write detailed study notes with bullet points covering key concepts from the provided content]

FILL-IN-THE-BLANKS:
1. [Create a sentence with _______ blank from the provided content]
2. [Create a sentence with _______ blank from the provided content]
3. [Create a sentence with _______ blank from the provided content]
4. [Create a sentence with _______ blank from the provided content]
5. [Create a sentence with _______ blank from the provided content]

ANSWERS:
1. [Provide the missing word for question 1]
2. [Provide the missing word for question 2]
3. [Provide the missing word for question 3]
4. [Provide the missing word for question 4]
5. [Provide the missing word for question 5]

MATCH-THE-FOLLOWING EXERCISES:
Column A: 1.[Term from content] 2.[Term from content] 3.[Term from content] 4.[Term from content] 5.[Term from content]
Column B: A.[Definition from content] B.[Definition from content] C.[Definition from content] D.[Definition from content] E.[Definition from content]
Answers: 1-[Letter], 2-[Letter], 3-[Letter], 4-[Letter], 5-[Letter]

SUBJECTIVE QUESTIONS:
Q1: [Write a thoughtful question about the provided content]
Q2: [Write a thoughtful question about the provided content]
Q3: [Write a thoughtful question about the provided content]

ANSWERS:
Q1: [Write a complete answer to question 1 based on the content]
Q2: [Write a complete answer to question 2 based on the content]
Q3: [Write a complete answer to question 3 based on the content]

CRITICAL: You must fill in ALL sections completely using ONLY the provided content. Do not generate content for {subject} - {chapter} if it's not present in the source material.

IMPORTANT: Make sure to include the exact section headers as shown above (STUDY NOTES:, FILL-IN-THE-BLANKS:, etc.)"""
    
    result = call_gpt(prompt, text, max_tokens=3000)  # Increased for comprehensive content
    
    # Debug: Log the generated content
    logger.info(f"Generated content length: {len(result)}")
    logger.info(f"Generated content preview: {result[:500]}...")
    
    # Validate that all sections are present
    required_sections = ["STUDY NOTES:", "FILL-IN-THE-BLANKS:", "MATCH-THE-FOLLOWING EXERCISES:", "SUBJECTIVE QUESTIONS:"]
    missing_sections = [section for section in required_sections if section not in result]
    
    if missing_sections:
        # Log missing sections for debugging
        logger.warning(f"Missing sections in generated content: {missing_sections}")
    
    return result

# =============================================================================
# 5. MAIN PROCESSING FUNCTION (Entry point from main.py)
# =============================================================================

@traceable(name="full_processing_pipeline")
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
