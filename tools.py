import base64
import re
import logging
from config import azure_client, AZURE_DEPLOYMENT_NAME

# Create logger for this module
logger = logging.getLogger(__name__)

# =============================================================================
# 1. CORE UTILITY FUNCTIONS (Called by others)
# =============================================================================

def call_gpt(prompt, content=""):
    """Simple GPT call function - used by all other tools"""
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": content}
    ]
    
    try:
        result = azure_client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=messages,
            temperature=0.1,
            max_tokens=500  # Reduced from 1000 to save costs
        )
        return result.choices[0].message.content
    except Exception as e:
        return f"ERROR: GPT call failed - {str(e)}"

def encode_image_base64(img_path):
    """Encode image to base64 - used by vision_understand_tool"""
    try:
        with open(img_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception as e:
        return f"ERROR: Failed to encode image - {str(e)}"

# =============================================================================
# 2. CONTENT EXTRACTION FUNCTIONS (Called first in processing)
# =============================================================================

def extract_pdf_content(pdf_path):
    """Simple PDF text extraction using Docling"""
    try:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        
        # Extract all text
        content = ""
        for element in result.document.texts:
            if element.text.strip():
                content += element.text.strip() + "\n\n"
        
        return content
    except Exception as e:
        return f"ERROR: PDF extraction failed - {str(e)}"

def vision_understand_tool(images, standard, subject, chapter):
    """Simple vision understanding tool"""
    try:
        user_content = [
            {"type": "text", "text": f"Extract and analyze educational content from these images for {standard} level {subject}, focusing on {chapter}. Provide detailed text extraction and educational analysis."}
        ]
        
        for img_path in images:
            encoded = encode_image_base64(img_path)
            if encoded.startswith("ERROR"):
                return encoded
            
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}
            })

        messages = [
            {"role": "system", "content": f"You are an educational content analyzer for {standard} level {subject}."},
            {"role": "user", "content": user_content}
        ]
        
        response = azure_client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=messages,
            temperature=0.1,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: Vision processing failed - {str(e)}"

# =============================================================================
# 3. VALIDATION FUNCTIONS (Called by graph nodes)
# =============================================================================

def grade_level_check_tool(content, target_standard, subject, chapter):
    """Simple and strict grade-level validation"""
    
    # Extract grade number
    grade_match = re.search(r'(\d+)', target_standard)
    if not grade_match:
        return "ERROR: Could not extract grade number from standard"
    
    target_grade = int(grade_match.group(1))
    
    # Define forbidden terms for lower grades
    forbidden_terms = {
        1: ["photosynthesis", "electromagnetic", "quantum", "mitochondria", "metabolism", "osmosis", "chromosome", "heredity", "biochemistry", "thermodynamics"],
        2: ["photosynthesis", "electromagnetic", "quantum", "mitochondria", "metabolism", "osmosis", "chromosome", "heredity", "biochemistry", "thermodynamics"],
        3: ["photosynthesis", "electromagnetic", "quantum", "mitochondria", "metabolism", "osmosis", "chromosome", "heredity", "biochemistry", "thermodynamics"],
        4: ["electromagnetic", "quantum", "mitochondria", "metabolism", "osmosis", "chromosome", "heredity", "biochemistry", "thermodynamics"],
        5: ["electromagnetic", "quantum", "mitochondria", "metabolism", "osmosis", "chromosome", "heredity", "biochemistry", "thermodynamics"]
    }
    
    # Check for forbidden terms
    if target_grade <= 5:
        terms = forbidden_terms.get(target_grade, [])
        content_lower = content.lower()
        
        for term in terms:
            if term in content_lower:
                return f"TOO ADVANCED: Grade {target_grade} content - Contains advanced term '{term}' inappropriate for {target_standard}"
    
    # Get age range and max sentence length
    age_ranges = {1: "5-6", 2: "6-7", 3: "7-8", 4: "8-9", 5: "9-10", 6: "10-11", 7: "11-12", 8: "12-13", 9: "13-14", 10: "14-15", 11: "15-16", 12: "16-17"}
    sentence_lengths = {1: 8, 2: 10, 3: 12, 4: 15, 5: 18, 6: 20, 7: 25, 8: 30, 9: 35, 10: 40, 11: 45, 12: 50}
    
    age_range = age_ranges.get(target_grade, f"{target_grade+4}-{target_grade+5}") + " years"
    max_length = sentence_lengths.get(target_grade, 50)
    
    # AI validation with short response
    prompt = f"""Check if this content fits {target_standard} students (age {age_range}).

CONTENT: {content[:300]}...

Respond ONLY with:
- APPROPRIATE: Grade {target_grade} content
- TOO ADVANCED: Grade {target_grade} content  
- TOO SIMPLE: Grade {target_grade} content

No explanation needed."""

    return call_gpt(prompt)

def child_filter_tool(text): 
    """Verify content is child-appropriate"""
    return call_gpt("Is this content safe for students? Respond ONLY: 'APPROPRIATE' or 'INAPPROPRIATE'", text)

def content_match_tool(text, subject, chapter): 
    """Verify content matches specified subject and lesson"""
    prompt = f"Does this content match '{subject}' - '{chapter}'? Respond ONLY: 'MATCH', 'PARTIAL_MATCH', or 'NO_MATCH'"
    return call_gpt(prompt, text)

# =============================================================================
# 4. CONTENT GENERATION FUNCTIONS (Called by graph nodes)
# =============================================================================

def generate_notes_tool(text, grade_level, subject, chapter): 
    """Generate grade-appropriate study notes"""
    prompt = f"Create study notes for {grade_level} students: {subject} - {chapter}. Use simple {grade_level} vocabulary."
    return call_gpt(prompt, text)

def generate_blanks_tool(text, grade_level, subject, chapter):
    """Generate fill-in-the-blank exercises"""
    prompt = f"""Create 5 fill-in-blanks for {grade_level}: {subject} - {chapter}

FORMAT:
1. Sentence with ________ blank
   Answer: word

2. Sentence with ________ blank  
   Answer: word

(Continue for 5 total)"""
    
    return call_gpt(prompt, text)

def generate_match_tool(text, grade_level, subject, chapter):
    """Generate match-the-following exercises"""
    prompt = f"""Create 5 match pairs for {grade_level}: {subject} - {chapter}

Column A: 1. Item1  2. Item2  3. Item3  4. Item4  5. Item5
Column B: A. Match1  B. Match2  C. Match3  D. Match4  E. Match5
Answers: 1-A, 2-B, 3-C, 4-D, 5-E"""
    
    return call_gpt(prompt, text)

def generate_qna_tool(text, grade_level, subject, chapter):
    """Generate grade-appropriate questions"""
    prompt = f"""Create 3 questions for {grade_level}: {subject} - {chapter}

Q1: [question]
A1: [answer]

Q2: [question] 
A2: [answer]

Q3: [question]
A3: [answer]"""
    
    return call_gpt(prompt, text)

# =============================================================================
# 5. MAIN PROCESSING FUNCTION (Entry point from main.py)
# =============================================================================

def process_educational_content_tool(content_source, standard, subject, chapter, content_type="pdf"):
    """Main educational content processing tool"""
    
    # Extract content based on type
    if content_type == "pdf":
        content = extract_pdf_content(content_source)
    elif content_type == "images":
        if isinstance(content_source, str):
            content_source = [content_source]
        content = vision_understand_tool(content_source, standard, subject, chapter)
    else:  # text
        content = content_source
    
    if content.startswith("ERROR"):
        return {"error": content}
    
    # Import here to avoid circular imports
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
    """Simple output formatting"""
    if not result or 'messages' not in result:
        return "No educational content generated."
    
    messages = result['messages']
    if not messages:
        return "No messages found."
    
    # Get the last message (assistant response)
    last_message = messages[-1]
    if isinstance(last_message, dict):
        content = last_message.get('content', '')
    else:
        content = getattr(last_message, 'content', '') or str(last_message)
    
    return content if content else "No content found in response."
