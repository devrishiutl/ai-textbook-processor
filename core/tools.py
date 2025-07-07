"""
Core LLM Tools - Only LLM-related functions with enhanced cost tracking
"""
import logging
import os
from config.settings import AZURE_ENDPOINT, AZURE_API_KEY, AZURE_DEPLOYMENT_NAME, AZURE_API_VERSION
from config.logging import log_cost_tracking

try:
    from langsmith.run_helpers import traceable
    from langchain_openai import AzureChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGSMITH_AVAILABLE = True
except ImportError:
    def traceable(name=None):
        def decorator(func):
            return func
        return decorator
    LANGSMITH_AVAILABLE = False

logger = logging.getLogger(__name__)

# Initialize LangChain client for proper LangSmith integration
if LANGSMITH_AVAILABLE:
    try:
        llm = AzureChatOpenAI(
            azure_deployment=AZURE_DEPLOYMENT_NAME,
            openai_api_version=AZURE_API_VERSION,
            azure_endpoint=AZURE_ENDPOINT,
            api_key=AZURE_API_KEY,
            temperature=0.1,
            max_tokens=2000
        )
        logger.info("LangChain Azure OpenAI client initialized for LangSmith integration")
    except Exception as e:
        logger.error(f"Failed to initialize LangChain client: {str(e)}")
        llm = None
else:
    llm = None

def call_gpt_with_langchain(prompt, content="", max_tokens=2000):
    """Core GPT function using LangChain for proper LangSmith integration"""
    if not llm:
        logger.error("LangChain client not available")
        return f"ERROR: LangChain client not available"
    
    try:
        # Create messages for LangChain
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=content)
        ]
        
        # Call LLM through LangChain (this will automatically be traced by LangSmith)
        response = llm.invoke(messages)
        
        # Log the response for debugging
        logger.info(f"LangChain LLM call completed successfully")
        
        return response.content
    except Exception as e:
        logger.error(f"LangChain LLM call failed: {str(e)}")
        return f"ERROR: {str(e)}"

def call_gpt_fallback(prompt, content="", max_tokens=2000):
    """Fallback GPT function using direct Azure OpenAI (for when LangChain is not available)"""
    try:
        from openai import AzureOpenAI
        azure_client = AzureOpenAI(
            azure_endpoint=AZURE_ENDPOINT,
            api_key=AZURE_API_KEY,
            api_version=AZURE_API_VERSION
        )
        
        result = azure_client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": content}],
            temperature=0.1,
            max_tokens=max_tokens
        )
        
        # Enhanced token usage logging for cost tracking
        usage = getattr(result, 'usage', None)
        if usage:
            total_tokens = usage.total_tokens
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            
            # Log detailed token usage
            logger.info(f"LLM Call - Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens}, Total: {total_tokens}")
            
            # Estimate cost (approximate - adjust based on your Azure pricing)
            # GPT-4 pricing is roughly $0.03 per 1K input tokens and $0.06 per 1K output tokens
            estimated_cost = (prompt_tokens * 0.00003) + (completion_tokens * 0.00006)
            log_cost_tracking("LLM_CALL", total_tokens, estimated_cost)
        
        return result.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM call failed: {str(e)}")
        return f"ERROR: {str(e)}"

def call_gpt(prompt, content="", max_tokens=2000):
    """Core GPT function with LangSmith integration"""
    if LANGSMITH_AVAILABLE and llm:
        return call_gpt_with_langchain(prompt, content, max_tokens)
    else:
        return call_gpt_fallback(prompt, content, max_tokens)

@traceable(name="content_validation")
def validate_content_tool(content, target_standard, subject, chapter):
    """Validate educational content using LLM with cost tracking"""
    logger.info(f"Starting content validation for {target_standard} {subject} - {chapter}")
    
    prompt = f"""Analyze this educational content for three criteria:

1. GRADE LEVEL: Is this content appropriate for {target_standard} students?
2. SAFETY: Is this content safe and appropriate for students?
3. RELEVANCE: Does this content relate to {subject} - {chapter}?

Content: {content[:800]}

Respond in this EXACT format:
GRADE_CHECK: [APPROPRIATE/TOO ADVANCED/TOO SIMPLE]
SAFETY_CHECK: [APPROPRIATE/INAPPROPRIATE]
RELEVANCE_CHECK: [MATCH/PARTIAL_MATCH/NO_MATCH]
REASON: [Brief reason - max 50 words. If all pass: 'Content is appropriate, safe, and relevant.' If any fail: 'Brief specific reason for failure.']"""

    result = call_gpt(prompt, max_tokens=150)
    logger.info("Content validation completed")
    return result

@traceable(name="educational_content_generation")
def generate_content_tool(text, grade_level, subject, chapter):
    """Generate educational content using LLM and return structured JSON with cost tracking"""
    logger.info(f"Starting content generation for {grade_level} {subject} - {chapter}")
    
    prompt = f"""Based on the following educational content, create comprehensive study materials for {grade_level} students.

Use ONLY the content provided below. Do not add information that is not present in the source material.

You MUST generate ALL four sections below. DO NOT skip any section. Each section must be complete with actual content.

Return your response as a valid JSON object with the following structure:

{{
    "importantNotes": "[Write detailed study notes with markdown formatting covering key concepts from the provided content. Use: **Bold** for important terms, ## Headings for main topics, ### Subheadings for subtopics, - Bullet points for lists, *Italic* for emphasis, and numbered lists for steps or sequences]",
    "fillInTheBlanks": {{
        "questions": {{
            "1": "[Create a sentence with _______ blank from the provided content]",
            "2": "[Create a sentence with _______ blank from the provided content]",
            "3": "[Create a sentence with _______ blank from the provided content]",
            "4": "[Create a sentence with _______ blank from the provided content]",
            "5": "[Create a sentence with _______ blank from the provided content]"
        }},
        "answers": {{
            "1": "[Provide the missing word for question 1]",
            "2": "[Provide the missing word for question 2]",
            "3": "[Provide the missing word for question 3]",
            "4": "[Provide the missing word for question 4]",
            "5": "[Provide the missing word for question 5]"
        }}
    }},
    "matchTheFollowing": {{
        "column_a": {{
            "1": "[Term from content]",
            "2": "[Term from content]",
            "3": "[Term from content]",
            "4": "[Term from content]",
            "5": "[Term from content]"
        }},
        "column_b": {{
            "A": "[Definition from content]",
            "B": "[Definition from content]",
            "C": "[Definition from content]",
            "D": "[Definition from content]",
            "E": "[Definition from content]"
        }},
        "answers": {{
            "1": "[Letter]",
            "2": "[Letter]",
            "3": "[Letter]",
            "4": "[Letter]",
            "5": "[Letter]"
        }}
    }},
    "questionAnswer": {{
        "questions": {{
            "Q1": "[Write a thoughtful question about the provided content]",
            "Q2": "[Write a thoughtful question about the provided content]",
            "Q3": "[Write a thoughtful question about the provided content]"
        }},
        "answers": {{
            "Q1": "[Write a complete answer to question 1 based on the content]",
            "Q2": "[Write a complete answer to question 2 based on the content]",
            "Q3": "[Write a complete answer to question 3 based on the content]"
        }}
    }}
}}

MARKDOWN FORMATTING GUIDELINES for importantNotes:
- Use **Bold** for important terms, definitions, and key concepts
- Use ## for main topic headings
- Use ### for subtopic headings  
- Use - for bullet points
- Use *Italic* for emphasis and examples
- Use numbered lists (1. 2. 3.) for steps, sequences, or ordered concepts
- Use `code` for formulas, equations, or technical terms
- Use > for important notes or warnings

CRITICAL: You must fill in ALL sections completely using ONLY the provided content. Do not generate content for {subject} - {chapter} if it's not present in the source material.

IMPORTANT: Return ONLY valid JSON. Do not include any text before or after the JSON object."""
    
    result = call_gpt(prompt, text, max_tokens=3000)
    logger.info("Content generation completed")
    return result

@traceable(name="image_vision_processing")
def vision_understand_tool(images, standard, subject, chapter):
    """Process images with vision AI and cost tracking"""
    logger.info(f"Starting vision processing for {standard} {subject} - {chapter}")
    
    try:
        user_content = [{"type": "text", "text": "Extract all educational content from these images. Describe exactly what you see - text, diagrams, concepts, topics, etc. Do not generate new content, only describe what is actually present in the images."}]
        
        for img_path in images:
            from services.image_service import preprocess_image
            encoded = preprocess_image(img_path)
            
            if encoded.startswith("ERROR"):
                logger.error(f"Image preprocessing failed: {encoded}")
                return encoded
            
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}
            })

        # For vision processing, we'll use the direct Azure client since LangChain vision support might be limited
        from openai import AzureOpenAI
        azure_client = AzureOpenAI(
            azure_endpoint=AZURE_ENDPOINT,
            api_key=AZURE_API_KEY,
            api_version=AZURE_API_VERSION
        )

        response = azure_client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are an educational content extractor. Extract and describe only the actual content present in the images."},
                {"role": "user", "content": user_content}
            ],
            temperature=0.1,
            max_tokens=3000
        )
        
        # Log vision processing costs
        usage = getattr(response, 'usage', None)
        if usage:
            total_tokens = usage.total_tokens
            estimated_cost = total_tokens * 0.00003  # Vision models may have different pricing
            log_cost_tracking("VISION_PROCESSING", total_tokens, estimated_cost)
        
        logger.info("Vision processing completed")
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Vision processing failed: {str(e)}")
        return f"ERROR: {str(e)}" 