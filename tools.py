import base64
import re
import logging
from config import azure_client, AZURE_DEPLOYMENT_NAME
import os

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
@traceable(name="unified_content_extraction")
def extract_content_with_docling(content_path, content_type="pdf"):
    """Unified content extraction using Docling for both PDFs and images
    
    Cost optimization: Uses free Docling instead of expensive Azure Vision AI
    - PDF processing: ₹0.30 (already optimized)
    - Image processing: ₹10.00 → ₹0.00 (100% cost reduction!)
    """
    try:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        
        if content_type == "pdf":
            # Extract PDF content
            result = converter.convert(content_path)
            content = ""
            for element in result.document.texts:
                if element.text.strip():
                    content += element.text.strip() + "\n\n"
            
            logger.info(f"Successfully extracted PDF content using Docling (FREE)")
            return content.strip() if content.strip() else "ERROR: No text content found in PDF"
            
        elif content_type == "images":
            # Handle both single image and list of images
            image_paths = [content_path] if isinstance(content_path, str) else content_path
            
            combined_text = ""
            successful_extractions = 0
            
            for img_path in image_paths:
                try:
                    # Extract text from image using Docling
                    result = converter.convert(img_path)
                    
                    if result and hasattr(result, 'document') and hasattr(result.document, 'texts'):
                        image_content = ""
                        for element in result.document.texts:
                            if hasattr(element, 'text') and element.text.strip():
                                image_content += element.text.strip() + "\n"
                        
                        if image_content.strip():
                            combined_text += f"--- Content from {os.path.basename(img_path)} ---\n"
                            combined_text += image_content.strip() + "\n\n"
                            successful_extractions += 1
                            logger.info(f"Successfully extracted text from {img_path} using Docling (FREE)")
                        
                except Exception as img_error:
                    logger.warning(f"Failed to extract text from {img_path}: {str(img_error)}")
                    continue
            
            if combined_text.strip():
                logger.info(f"💰 MAJOR COST SAVINGS: Processed {successful_extractions} images using FREE Docling instead of expensive Azure Vision AI")
                logger.info(f"💰 Cost saved: ₹{successful_extractions * 0.59:.2f} per request (₹0.59 per image with Azure Vision)")
                return combined_text.strip()
            else:
                return "ERROR: No text content extracted from any images"
        
        else:
            return f"ERROR: Unsupported content type: {content_type}"
            
    except Exception as e:
        logger.error(f"Docling content extraction failed: {str(e)}")
        return f"ERROR: Content extraction failed - {str(e)}"

@traceable(name="legacy_pdf_extraction")
def extract_pdf_content(pdf_path):
    """Legacy PDF extraction function - now uses unified Docling approach"""
    return extract_content_with_docling(pdf_path, "pdf")

@traceable(name="legacy_image_vision_processing")
def vision_understand_tool(images, standard, subject, chapter):
    """Legacy vision function - now uses cost-optimized Docling approach
    
    DEPRECATED: This function now uses Docling instead of expensive Azure Vision AI
    Saves ₹10+ per request while maintaining functionality
    """
    logger.info("🔄 Using cost-optimized Docling instead of expensive Azure Vision AI")
    
    # Use unified Docling extraction
    content = extract_content_with_docling(images, "images")
    
    if content.startswith("ERROR"):
        return content
    
    # Add educational context using a simple LLM call instead of vision
    context_prompt = f"""The following content was extracted from educational images for {standard} students studying {subject} - {chapter}.

Please organize and present this content in a clear, educational format suitable for the specified grade level and subject:

{content}

Focus on making the content educational and well-structured."""
    
    try:
        organized_content = call_gpt(context_prompt, max_tokens=2000)
        logger.info("💰 Successfully processed images with Docling + minimal LLM context (major cost savings)")
        return organized_content
    except Exception as e:
        logger.warning(f"Failed to add educational context: {str(e)}")
        # Return raw content if context addition fails
        return content

@traceable(name="cost_optimized_image_extraction")
def extract_text_from_images_docling(images):
    """Cost-optimized image text extraction using Docling (FREE!)
    
    UPDATED: Now uses unified extraction approach
    Replaces expensive Azure Vision AI (₹10 for 17 images) with free Docling (₹0).
    Saves ₹10.00 per request!
    """
    return extract_content_with_docling(images, "images")

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

CRITICAL: You must fill in ALL sections completely using ONLY the provided content. Do not generate content for topics not present in the source material."""
    
    result = call_gpt(prompt, text, max_tokens=3000)  # Increased for comprehensive content
    
    # Validate that all sections are present
    required_sections = ["STUDY NOTES:", "FILL-IN-THE-BLANKS:", "MATCH-THE-FOLLOWING EXERCISES:", "SUBJECTIVE QUESTIONS:"]
    missing_sections = [section for section in required_sections if section not in result]
    
    if missing_sections:
        # Log missing sections for debugging
        logger.warning(f"Missing sections in generated content: {missing_sections}")
    
    return result

# Individual content generation functions for streaming
@traceable(name="study_notes_generation")
def generate_study_notes_tool(text, grade_level, subject, chapter):
    """Generate study notes only"""
    prompt = f"""Based on the following educational content, create detailed study notes for {grade_level} students studying {subject} - {chapter}.

Use ONLY the content provided below. Write comprehensive bullet-pointed study notes covering all key concepts.

Format:
STUDY NOTES:
- [Key concept 1 from the content]
- [Key concept 2 from the content]
- [Continue with all important points from the content]

Content: {text}"""
    
    return call_gpt(prompt, max_tokens=1000)

@traceable(name="fill_blanks_generation")
def generate_fill_blanks_tool(text, grade_level, subject, chapter):
    """Generate fill-in-the-blanks questions only"""
    prompt = f"""Based on the following educational content, create 5 fill-in-the-blank questions for {grade_level} students.

Use ONLY the content provided below. Create questions that test understanding of key concepts.

Format:
FILL-IN-THE-BLANKS:
1. [Sentence with _______ blank]
2. [Sentence with _______ blank]
3. [Sentence with _______ blank]
4. [Sentence with _______ blank]
5. [Sentence with _______ blank]

ANSWERS:
1. [Missing word for question 1]
2. [Missing word for question 2]
3. [Missing word for question 3]
4. [Missing word for question 4]
5. [Missing word for question 5]

Content: {text}"""
    
    return call_gpt(prompt, max_tokens=800)

@traceable(name="matching_exercises_generation")
def generate_matching_tool(text, grade_level, subject, chapter):
    """Generate match-the-following exercises only"""
    prompt = f"""Based on the following educational content, create match-the-following exercises for {grade_level} students.

Use ONLY the content provided below. Create 5 terms and their matching definitions.

Format:
MATCH-THE-FOLLOWING EXERCISES:
Column A: 1.[Term from content] 2.[Term from content] 3.[Term from content] 4.[Term from content] 5.[Term from content]
Column B: A.[Definition from content] B.[Definition from content] C.[Definition from content] D.[Definition from content] E.[Definition from content]
Answers: 1-[Letter], 2-[Letter], 3-[Letter], 4-[Letter], 5-[Letter]

Content: {text}"""
    
    return call_gpt(prompt, max_tokens=800)

@traceable(name="qna_generation")
def generate_qna_tool(text, grade_level, subject, chapter):
    """Generate Q&A section only"""
    prompt = f"""Based on the following educational content, create 3 subjective questions and their answers for {grade_level} students.

Use ONLY the content provided below. Create thoughtful questions that encourage deeper understanding.

Format:
SUBJECTIVE QUESTIONS:
Q1: [Thoughtful question about the content]
Q2: [Thoughtful question about the content]
Q3: [Thoughtful question about the content]

ANSWERS:
Q1: [Complete answer based on the content]
Q2: [Complete answer based on the content]
Q3: [Complete answer based on the content]

Content: {text}"""
    
    return call_gpt(prompt, max_tokens=1000)

# Streaming content generation function
def generate_content_streaming(text, grade_level, subject, chapter, progress_callback=None):
    """Generate educational content with streaming updates"""
    results = {}
    
    try:
        # Step 1: Generate study notes
        if progress_callback:
            progress_callback("Generating important notes...", 68)
        
        notes = generate_study_notes_tool(text, grade_level, subject, chapter)
        results['notes'] = notes
        
        if progress_callback:
            progress_callback("Study notes generated", 70)
        
        # Step 2: Generate fill-in-the-blanks
        if progress_callback:
            progress_callback("Creating fill-in-the-blank questions...", 71)
        
        blanks = generate_fill_blanks_tool(text, grade_level, subject, chapter)
        results['blanks'] = blanks
        
        if progress_callback:
            progress_callback("Fill-in-blanks created", 72)
        
        # Step 3: Generate matching exercises
        if progress_callback:
            progress_callback("Preparing matching exercises...", 73)
        
        matching = generate_matching_tool(text, grade_level, subject, chapter)
        results['matching'] = matching
        
        if progress_callback:
            progress_callback("Matching exercises prepared", 74)
        
        # Step 4: Generate Q&A
        if progress_callback:
            progress_callback("Formulating Q&A section...", 75)
        
        qna = generate_qna_tool(text, grade_level, subject, chapter)
        results['qna'] = qna
        
        if progress_callback:
            progress_callback("Q&A section completed", 76)
        
        # Combine all results
        combined_content = f"""
{notes}

{blanks}

{matching}

{qna}
        """
        
        return combined_content.strip()
        
    except Exception as e:
        logger.error(f"Streaming content generation error: {str(e)}")
        raise e

# =============================================================================
# 5. MAIN PROCESSING FUNCTION (Entry point from main.py)
# =============================================================================

@traceable(name="full_processing_pipeline")
def process_educational_content_tool(content_source, standard, subject, chapter, content_type="pdf"):
    """Main processing function with unified cost optimization using Docling"""
    
    # 💰 UNIFIED COST OPTIMIZATION: Use free Docling for both PDFs and images
    # This saves significant costs especially for image processing (₹10+ per request)
    
    if content_type == "pdf":
        content = extract_content_with_docling(content_source, "pdf")
    elif content_type == "images":
        content = extract_content_with_docling(content_source, "images")
    else:
        content = content_source  # For text content
    
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
