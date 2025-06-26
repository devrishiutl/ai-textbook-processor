import base64
import re
import logging
from PIL import Image
from config import azure_client, AZURE_DEPLOYMENT_NAME
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

# Create logger for this module
logger = logging.getLogger(__name__)

@dataclass
class GradeStandards:
    """Data class for grade-level educational standards"""
    grade: int
    age_range: str
    vocabulary_level: str
    sentence_length: str
    concept_complexity: str
    cognitive_level: str
    sample_content: str

class EducationalGradeValidator:
    """Comprehensive educational grade-level validation system"""
    
    def __init__(self):
        self.standards = self._initialize_grade_standards()
        self.vocabulary_database = self._initialize_vocabulary_database()
    
    def _initialize_grade_standards(self) -> Dict[int, GradeStandards]:
        """Initialize comprehensive grade standards for all levels"""
        return {
            # PRIMARY LEVEL (Ages 6-11)
            1: GradeStandards(
                grade=1, age_range="6-7 years",
                vocabulary_level="Basic sight words, 1-2 syllables, simple nouns/verbs",
                sentence_length="3-6 words maximum",
                concept_complexity="Concrete objects, immediate environment, simple facts",
                cognitive_level="Pre-operational to concrete operational",
                sample_content="The dog runs. I see a cat. The ball is red."
            ),
            2: GradeStandards(
                grade=2, age_range="7-8 years",
                vocabulary_level="Simple words, basic descriptive terms, 1-2 syllables",
                sentence_length="4-8 words, simple sentence structure",
                concept_complexity="Familiar objects, basic relationships, simple processes",
                cognitive_level="Early concrete operational",
                sample_content="The big cat sleeps. Birds fly in the blue sky."
            ),
            3: GradeStandards(
                grade=3, age_range="8-9 years",
                vocabulary_level="Elementary academic terms, 1-3 syllables, basic concepts",
                sentence_length="6-10 words, compound sentences allowed",
                concept_complexity="Observable phenomena, simple cause-effect, basic classification",
                cognitive_level="Concrete operational established",
                sample_content="Plants need water and sunlight to grow healthy and strong."
            ),
            4: GradeStandards(
                grade=4, age_range="9-10 years",
                vocabulary_level="Moderate complexity, 2-3 syllables, introductory technical terms",
                sentence_length="8-12 words, complex sentences with conjunctions",
                concept_complexity="Simple systems, basic scientific processes, some abstract ideas",
                cognitive_level="Advanced concrete operational",
                sample_content="Plant roots absorb water and nutrients from the soil to help growth."
            ),
            5: GradeStandards(
                grade=5, age_range="10-11 years",
                vocabulary_level="Complex vocabulary, 2-4 syllables, moderate technical terms",
                sentence_length="10-15 words, multiple clauses acceptable",
                concept_complexity="Complex systems, detailed processes, transitional abstract reasoning",
                cognitive_level="Transitioning to formal operational",
                sample_content="Photosynthesis helps plants convert sunlight, water, and carbon dioxide into food and oxygen."
            ),
            
            # MIDDLE SCHOOL (Ages 11-14)
            6: GradeStandards(
                grade=6, age_range="11-12 years",
                vocabulary_level="Advanced vocabulary, 3-5 syllables, scientific terminology",
                sentence_length="12-18 words, complex sentence structures",
                concept_complexity="Abstract scientific concepts, detailed analysis, complex relationships",
                cognitive_level="Early formal operational",
                sample_content="Cellular respiration and photosynthesis are complementary processes that maintain ecosystem balance through energy transformation."
            ),
            7: GradeStandards(
                grade=7, age_range="12-13 years",
                vocabulary_level="Complex academic language, specialized terminology",
                sentence_length="15-20 words, sophisticated sentence structure",
                concept_complexity="Advanced abstract thinking, hypothesis formation, complex systems analysis",
                cognitive_level="Developing formal operational",
                sample_content="Mitochondrial organelles facilitate cellular energy production through aerobic respiration, converting glucose into ATP molecules."
            ),
            8: GradeStandards(
                grade=8, age_range="13-14 years",
                vocabulary_level="Sophisticated academic vocabulary, technical terminology",
                sentence_length="18-25 words, complex grammatical structures",
                concept_complexity="Theoretical concepts, analytical reasoning, advanced problem-solving",
                cognitive_level="Established formal operational",
                sample_content="Electromagnetic radiation demonstrates wave-particle duality properties, exhibiting quantum mechanical principles in various experimental observations."
            ),
            
            # HIGH SCHOOL (Ages 14-18)
            9: GradeStandards(
                grade=9, age_range="14-15 years",
                vocabulary_level="Advanced academic vocabulary, discipline-specific terminology",
                sentence_length="20-30 words, complex dependent clauses",
                concept_complexity="Theoretical frameworks, multi-variable analysis, interdisciplinary connections",
                cognitive_level="Advanced formal operational",
                sample_content="Homeostatic regulatory mechanisms maintain physiological equilibrium through complex negative feedback loops involving multiple organ systems."
            ),
            10: GradeStandards(
                grade=10, age_range="15-16 years",
                vocabulary_level="Sophisticated academic language, specialized professional terms",
                sentence_length="25-35 words, advanced syntactic complexity",
                concept_complexity="Advanced theoretical models, research-level analysis, synthesis thinking",
                cognitive_level="Mature formal operational",
                sample_content="Thermodynamic principles governing energy transformations in biological systems demonstrate conservation laws through metabolic pathway analysis."
            ),
            11: GradeStandards(
                grade=11, age_range="16-17 years",
                vocabulary_level="College-preparatory vocabulary, professional terminology",
                sentence_length="30-40 words, graduate-level sentence complexity",
                concept_complexity="Research-level concepts, independent analysis, advanced synthesis",
                cognitive_level="College-preparatory analytical thinking",
                sample_content="Quantum mechanical orbital models describe electron probability distributions using wave function mathematics to predict chemical bonding behavior."
            ),
            12: GradeStandards(
                grade=12, age_range="17-18 years",
                vocabulary_level="College-level academic vocabulary, specialized research terminology",
                sentence_length="35+ words, professional academic writing style",
                concept_complexity="Graduate-level concepts, independent research capability, critical analysis",
                cognitive_level="College-level analytical and critical thinking",
                sample_content="Epigenetic modifications regulate gene expression patterns without altering underlying DNA sequences through methylation and histone modification mechanisms."
            )
        }
    
    def _initialize_vocabulary_database(self) -> Dict[str, List[str]]:
        """Initialize comprehensive vocabulary database by complexity level"""
        return {
            "grade_1_2": [
                "cat", "dog", "run", "big", "small", "red", "blue", "mom", "dad", 
                "play", "eat", "see", "go", "come", "like", "love", "happy", "sad"
            ],
            "grade_3_4": [
                "animal", "plant", "water", "food", "grow", "live", "family", "friend",
                "school", "learn", "study", "read", "write", "think", "know", "understand"
            ],
            "grade_5_6": [
                "environment", "habitat", "organism", "adaptation", "ecosystem", "community",
                "population", "predator", "prey", "photosynthesis", "respiration", "nutrition"
            ],
            "grade_7_8": [
                "mitochondria", "metabolism", "osmosis", "diffusion", "chromosome", "heredity",
                "genetic", "cellular", "molecular", "biochemical", "physiological", "anatomical"
            ],
            "grade_9_10": [
                "biochemistry", "thermodynamics", "electromagnetic", "quantum", "synthesis",
                "catalyst", "equilibrium", "homeostasis", "evolution", "natural selection"
            ],
            "grade_11_12": [
                "epigenetic", "stoichiometry", "electromagnetism", "quantum mechanics",
                "thermodynamic", "electrochemical", "spectroscopy", "chromatography"
            ]
        }
    
    def analyze_vocabulary_complexity(self, content: str, target_grade: int) -> Tuple[List[str], Dict[str, int]]:
        """Analyze vocabulary complexity against grade-level standards"""
        content_lower = content.lower()
        violations = []
        complexity_counts = {level: 0 for level in self.vocabulary_database.keys()}
        
        # Count vocabulary by complexity level
        for level, words in self.vocabulary_database.items():
            for word in words:
                if word in content_lower:
                    complexity_counts[level] += 1
        
        # Define grade-appropriate vocabulary levels
        grade_vocabulary_map = {
            1: ["grade_1_2"], 2: ["grade_1_2"],
            3: ["grade_1_2", "grade_3_4"], 4: ["grade_1_2", "grade_3_4"],
            5: ["grade_1_2", "grade_3_4", "grade_5_6"], 6: ["grade_1_2", "grade_3_4", "grade_5_6"],
            7: ["grade_3_4", "grade_5_6", "grade_7_8"], 8: ["grade_3_4", "grade_5_6", "grade_7_8"],
            9: ["grade_5_6", "grade_7_8", "grade_9_10"], 10: ["grade_5_6", "grade_7_8", "grade_9_10"],
            11: ["grade_7_8", "grade_9_10", "grade_11_12"], 12: ["grade_7_8", "grade_9_10", "grade_11_12"]
        }
        
        allowed_levels = grade_vocabulary_map.get(target_grade, [])
        
        # Check for vocabulary violations
        for level, count in complexity_counts.items():
            if count > 0 and level not in allowed_levels:
                grade_level = level.split('_')[-1]  # Extract grade number
                violations.append(f"{count} terms from Grade {grade_level} level ({level})")
        
        return violations, complexity_counts
    
    def analyze_sentence_complexity(self, content: str, target_grade: int) -> Dict[str, any]:
        """Analyze sentence complexity against grade standards"""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return {"average_length": 0, "max_length": 0, "complexity_violations": []}
        
        word_counts = [len(sentence.split()) for sentence in sentences]
        average_length = sum(word_counts) / len(word_counts)
        max_length = max(word_counts)
        
        # Get grade-appropriate sentence length limits
        standards = self.standards[target_grade]
        expected_range = standards.sentence_length
        
        # Extract expected maximum from sentence_length description
        grade_limits = {
            1: 6, 2: 8, 3: 10, 4: 12, 5: 15,
            6: 18, 7: 20, 8: 25, 9: 30, 10: 35, 11: 40, 12: 50
        }
        
        max_allowed = grade_limits.get(target_grade, 50)
        violations = []
        
        if average_length > max_allowed:
            violations.append(f"Average sentence length ({average_length:.1f}) exceeds Grade {target_grade} limit ({max_allowed})")
        
        if max_length > max_allowed * 1.5:  # Allow some flexibility
            violations.append(f"Maximum sentence length ({max_length}) significantly exceeds grade level")
        
        return {
            "average_length": round(average_length, 1),
            "max_length": max_length,
            "total_sentences": len(sentences),
            "complexity_violations": violations,
            "expected_range": expected_range
        }
    
    def validate_grade_level(self, content: str, target_standard: str, subject: str, chapter: str) -> str:
        """Comprehensive grade-level validation"""
        
        # Extract grade number
        grade_match = re.search(r'(\d+)', target_standard)
        if not grade_match:
            return "ERROR: Could not extract grade number from standard"
        
        target_grade = int(grade_match.group(1))
        
        # Debug logging to track grade extraction
        logger.info(f"🔍 Grade Extraction Debug: target_standard='{target_standard}' → extracted_grade={target_grade}")
        
        if target_grade not in self.standards:
            return f"ERROR: Grade {target_grade} not supported (supported: 1-12)"
        
        # Get grade standards
        standards = self.standards[target_grade]
        
        # Perform comprehensive analysis
        vocab_violations, vocab_counts = self.analyze_vocabulary_complexity(content, target_grade)
        sentence_analysis = self.analyze_sentence_complexity(content, target_grade)
        
        # Build comprehensive assessment prompt
        assessment_prompt = f"""COMPREHENSIVE GRADE LEVEL VALIDATION

TARGET: {target_standard} (Age {standards.age_range})
SUBJECT: {subject} | CHAPTER: {chapter}

GRADE {target_grade} STANDARDS:
• Vocabulary: {standards.vocabulary_level}
• Sentences: {standards.sentence_length}
• Concepts: {standards.concept_complexity}
• Cognitive Level: {standards.cognitive_level}
• Expected Content: {standards.sample_content}

AUTOMATED ANALYSIS RESULTS:
• Vocabulary Violations: {vocab_violations if vocab_violations else 'None detected'}
• Vocabulary Distribution: {vocab_counts}
• Sentence Analysis: Average {sentence_analysis['average_length']} words, Max {sentence_analysis['max_length']} words
• Sentence Violations: {sentence_analysis['complexity_violations'] if sentence_analysis['complexity_violations'] else 'None detected'}

CONTENT TO VALIDATE:
{content}

ASSESSMENT PROTOCOL:
1. Evaluate OVERALL vocabulary level - is it mostly appropriate with some challenging terms?
2. Check AVERAGE sentence complexity - occasional long sentences are acceptable
3. Assess concept difficulty - can {standards.age_range} students understand with teacher guidance?
4. Consider if this seems like legitimate {subject} content for {target_grade}
5. Ask: "Would this appear in a real {target_grade} textbook?" (imperfections included)

RESPONSE REQUIRED:
You must start your response with EXACTLY ONE of these three options:
• APPROPRIATE: Grade {target_grade} content
• TOO ADVANCED: Grade {target_grade} content  
• TOO SIMPLE: Grade {target_grade} content

Then provide the following analysis:
CONFIDENCE: [High/Medium/Low]
VOCABULARY: [Assessment of word complexity]
SENTENCES: [Assessment of sentence structure]
CONCEPTS: [Assessment of idea complexity]
RECOMMENDATION: [Specific action if content inappropriate]

EXAMPLES:
✓ Correct: "APPROPRIATE: Grade 6 content"
✓ Correct: "TOO ADVANCED: Grade 6 content"
✗ Wrong: "[APPROPRIATE/TOO ADVANCED/TOO SIMPLE]: Grade 6 content"

VALIDATION GUIDELINES:
• APPROPRIATE: Overall content suits {target_grade}, minor issues acceptable
• TOO ADVANCED: Content clearly designed for higher grades (2+ grades above)
• TOO SIMPLE: Content clearly designed for lower grades (2+ grades below)

NUANCED ASSESSMENT RULES:
1. Focus on OVERALL appropriateness, not individual worst sentences
2. Consider that real textbooks may have some imperfect sentences
3. If average sentence length is appropriate, don't reject for occasional long sentences
4. If vocabulary is mostly grade-level with some challenging terms (explained), that's NORMAL
5. Educational content can stretch students slightly - that's good pedagogy
6. Only mark TOO ADVANCED if content is clearly meant for much higher grades

CRITICAL: Be realistic about real-world educational content quality. Perfect textbooks don't exist."""

        # Get AI assessment with comprehensive context
        ai_result = call_gpt(assessment_prompt, "")
        
        # Add automated analysis summary
        analysis_summary = f"""

AUTOMATED ANALYSIS SUMMARY:
• Vocabulary Violations: {len(vocab_violations)} detected
• Sentence Complexity: {sentence_analysis['complexity_violations'] if sentence_analysis['complexity_violations'] else 'Within acceptable range'}
• Grade {target_grade} Expectations: {standards.sentence_length}, {standards.vocabulary_level}
"""
        
        return ai_result + analysis_summary

# Initialize global validator instance
grade_validator = EducationalGradeValidator()

def call_gpt(prompt, content, chat_history=[]):
    """Enhanced GPT call function"""
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": content}
    ]
    
    try:
        result = azure_client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=messages,
            temperature=0.1,  # Lower temperature for more consistent validation
            max_tokens=1000
        )
        return result.choices[0].message.content
    except Exception as e:
        return f"ERROR: GPT call failed - {str(e)}"

def encode_image_base64(img_path):
    """Encode image to base64"""
    try:
        with open(img_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception as e:
        return f"ERROR: Failed to encode image - {str(e)}"

def vision_understand_tool(images, standard, subject, lesson, chat_history=[]):
    """Enhanced vision understanding tool"""
    try:
        # Prepare content array for the user message
        user_content = [
            {"type": "text", "text": f"Extract and analyze all educational content from these images for {standard} level {subject}, focusing on {lesson}. Provide detailed text extraction, concept identification, and educational analysis suitable for the grade level."}
        ]
        
        # Add each image to the content
        for img_path in images:
            encoded = encode_image_base64(img_path)
            if encoded.startswith("ERROR"):
                return encoded
            
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}
            })

        messages = [
            {"role": "system", "content": f"You are an expert educational content analyzer for {standard} level {subject}, specializing in {lesson}. Extract ALL text, analyze visual content, identify key concepts, and provide comprehensive educational analysis."},
            {"role": "user", "content": user_content}
        ]
        
        response = azure_client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=messages,
            temperature=0.1,  # Low temperature for consistent content extraction
            max_tokens=2000  # Increase for detailed analysis
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: Vision processing failed - {str(e)}"

# Educational Content Tools
def profanity_filter_tool(text, chat_history=[]): 
    """Check content for inappropriate language"""
    return call_gpt("Analyze this educational content for any inappropriate language or profanity. Respond with 'CLEAN' or 'INAPPROPRIATE' followed by specific concerns.", text, chat_history)

def child_filter_tool(text, chat_history=[]): 
    """Verify content is child-appropriate"""
    return call_gpt("Evaluate if this content is safe and age-appropriate for students. Check ONLY for harmful content (violence, inappropriate themes, mature content). Do NOT consider subject relevance - focus only on safety and age-appropriateness. Respond with 'APPROPRIATE' or 'INAPPROPRIATE' with reasoning.", text, chat_history)

def content_match_tool(text, subject, lesson, chat_history=[]): 
    """Verify content matches specified subject and lesson"""
    prompt = f"Does this content match the subject '{subject}' and lesson '{lesson}'? Respond with 'MATCH', 'PARTIAL_MATCH', or 'NO_MATCH' with explanation."
    return call_gpt(prompt, text, chat_history)

def generate_notes_tool(text, grade_level, subject=None, chapter=None, chat_history=[]): 
    """Generate grade-appropriate study notes with subject context"""
    context = f" for {subject} - {chapter}" if subject and chapter else ""
    prompt = f"Create comprehensive study notes appropriate for {grade_level} students{context}. Use vocabulary and concepts suitable for this grade level. Include key concepts, definitions, and important points in a well-structured format."
    return call_gpt(prompt, text, chat_history)

def generate_qna_tool(text, grade_level, subject=None, chapter=None, chat_history=[]):
    """Generate grade-appropriate subjective questions with intelligent drawing integration"""
    
    # Use enhanced version if subject context is available
    if subject and chapter:
        return generate_enhanced_qna_with_subject_context(text, grade_level, subject, chapter, chat_history)
    
    # Extract grade number for basic logic
    grade_match = re.search(r'(\d+)', str(grade_level))
    target_grade = int(grade_match.group(1)) if grade_match else 0
    
    # Determine if drawing questions are appropriate
    visual_subjects = ['science', 'biology', 'mathematics', 'geography', 'physics', 'chemistry', 'art', 'history']
    include_drawing = subject and any(subj in str(subject).lower() for subj in visual_subjects) if subject else False
    
    prompt = f"""Create exactly 3 subjective questions appropriate for {grade_level} students.

ENHANCED REQUIREMENTS:
• Use grade-appropriate language and concepts for {grade_level}
• Include diverse question types (analytical, practical, conceptual)
• {"Include at least 1 drawing question if educationally valuable" if include_drawing else "Focus on written response questions"}

DRAWING QUESTION GUIDELINES (if applicable):
• Provide specific, clear drawing instructions
• Include what to draw, what to label, and proportions
• Explain how the drawing connects to the concept
• Make drawing task achievable for {grade_level} students
• Include both drawing AND explanation components

MANDATORY FORMAT:
**Question 1:** [Analytical/reasoning question]
**Answer:** [Detailed explanation appropriate for {grade_level}]

**Question 2:** [{"Drawing/visual question" if include_drawing else "Practical application question"}]
**Answer:** [{"Drawing instructions + conceptual explanation" if include_drawing else "Detailed practical answer"}]

**Question 3:** [Critical thinking/application question]
**Answer:** [Comprehensive answer encouraging deeper understanding]

QUALITY CHECKLIST:
✓ Questions test different cognitive levels
✓ Answers provide clear, educational explanations
✓ {"Drawing questions include specific, achievable instructions" if include_drawing else "All questions encourage written analysis"}
✓ Content complexity matches {grade_level} cognitive abilities
✓ Questions encourage critical thinking and deeper learning"""

    return call_gpt(prompt, text)

def generate_enhanced_qna_with_subject_context(text, grade_level, subject, chapter, chat_history=[]):
    """Enhanced QNA generation with full subject context for better drawing question integration"""
    
    # Extract grade number
    grade_match = re.search(r'(\d+)', str(grade_level))
    target_grade = int(grade_match.group(1)) if grade_match else 0
    
    # Subject-specific drawing question templates
    subject_drawing_templates = {
        "science": {
            "low_grades": [
                "Draw and label the parts of a [plant/animal/object] mentioned in the text.",
                "Draw a simple diagram showing [process] and explain each step.",
                "Sketch [natural phenomenon] and write 2-3 sentences about it."
            ],
            "high_grades": [
                "Create a detailed labeled diagram of [scientific structure/process].",
                "Draw and annotate the stages of [biological/chemical process].",
                "Design a diagram that explains [scientific concept] and analyze its components."
            ]
        },
        "mathematics": {
            "low_grades": [
                "Draw [geometric shapes] and count their [properties].",
                "Draw a simple graph showing [data from text].",
                "Sketch and solve this problem using pictures."
            ],
            "high_grades": [
                "Graph the relationship between [variables] and analyze the trend.",
                "Draw geometric constructions to solve [mathematical problem].",
                "Create a diagram to represent and solve [complex math concept]."
            ]
        },
        "geography": {
            "low_grades": [
                "Draw a simple map showing [geographic features] mentioned.",
                "Sketch [landform/weather pattern] and explain what causes it.",
                "Draw the route of [geographic process] like a river or mountain formation."
            ],
            "high_grades": [
                "Create a detailed topographic representation of [geographic region].",
                "Draw and analyze the formation process of [geological feature].",
                "Design a map showing [geographic relationships] and their impact."
            ]
        }
    }
    
    # Enhanced prompt with subject-aware drawing integration
    prompt = f"""ENHANCED EDUCATIONAL QUESTION GENERATOR

TARGET: {grade_level} students
SUBJECT: {subject}
CHAPTER: {chapter}
CONTENT SOURCE: Educational text about {subject} - {chapter}

QUESTION REQUIREMENTS:
• Create exactly 3 subjective questions
• Include at least 1 drawing question if subject is visual/diagram-friendly
• Use grade-appropriate vocabulary for {grade_level}
• Questions should test understanding of the provided content
• Include both conceptual and practical questions

DRAWING QUESTION GUIDELINES FOR {subject.upper()}:
{'• Include clear, specific drawing instructions' if any(subj in subject.lower() for subj in ['science', 'math', 'geography', 'biology', 'physics', 'chemistry']) else '• Drawing questions optional for this subject'}
{'• Specify what to draw, what to label, and how it relates to the concept' if any(subj in subject.lower() for subj in ['science', 'math', 'geography', 'biology', 'physics', 'chemistry']) else ''}
{'• Make drawing tasks achievable for ' + grade_level + ' motor and cognitive skills' if any(subj in subject.lower() for subj in ['science', 'math', 'geography', 'biology', 'physics', 'chemistry']) else ''}

CONTENT TO ANALYZE:
{text}

OUTPUT FORMAT:
**Question 1:** [Analytical question about the content]
**Answer:** [Comprehensive answer with explanations]

**Question 2:** [Drawing/Visual question - if appropriate for subject]
**Answer:** [Drawing instructions + conceptual explanation]
Example: "Draw and label [specific elements]. Your drawing should show [requirements]. Explain how [concept] works: [detailed explanation]"

**Question 3:** [Application/Critical thinking question]
**Answer:** [Detailed answer connecting theory to practice]

QUALITY STANDARDS:
✓ Questions test different cognitive levels (knowledge, comprehension, application)
✓ Answers are detailed enough for effective learning
✓ Drawing questions include specific, achievable instructions
✓ All content is appropriate for {grade_level} level
✓ Questions encourage deeper understanding of {subject} concepts"""

    return call_gpt(prompt, text)

def generate_blanks_tool(text, grade_level, subject=None, chapter=None, chat_history=[]):
    """Generate grade-appropriate fill-in-the-blank exercises with subject context"""
    context = f" for {subject} - {chapter}" if subject and chapter else ""
    prompt = f"""Create exactly 5 fill-in-the-blank exercises appropriate for {grade_level} students{context}.

Use vocabulary and concepts suitable for {grade_level}. Format:

1. [Sentence with ________ blank using grade-appropriate vocabulary] 
   **Answer:** [correct answer]

2. [Sentence with ________ blank]
   **Answer:** [correct answer]

3. [Sentence with ________ blank]
   **Answer:** [correct answer]

4. [Sentence with ________ blank]
   **Answer:** [correct answer]

5. [Sentence with ________ blank]
   **Answer:** [correct answer]

Focus on important terms and concepts appropriate for {grade_level} understanding{context}."""
    
    return call_gpt(prompt, text)

def generate_match_tool(text, grade_level, subject=None, chapter=None, chat_history=[]):
    """Generate grade-appropriate match-the-following exercises with subject context"""
    context = f" for {subject} - {chapter}" if subject and chapter else ""
    prompt = f"""Create exactly 5 match-the-following pairs appropriate for {grade_level} students{context}.

Use vocabulary and concepts suitable for {grade_level}. Format:

**Match the Following:**

Column A:
1. [Item 1 - grade appropriate]
2. [Item 2 - grade appropriate] 
3. [Item 3 - grade appropriate]
4. [Item 4 - grade appropriate]
5. [Item 5 - grade appropriate]

Column B:
A. [Match option A]
B. [Match option B]
C. [Match option C] 
D. [Match option D]
E. [Match option E]

**Answers:**
1 - [Letter], 2 - [Letter], 3 - [Letter], 4 - [Letter], 5 - [Letter]

Focus on relationships and connections appropriate for {grade_level} cognitive development{context}."""
    
    return call_gpt(prompt, text)

def grade_level_check_tool(content, target_standard, subject, chapter):
    """Comprehensive grade-level validation using the enhanced validator"""
    return grade_validator.validate_grade_level(content, target_standard, subject, chapter)

# Add these comprehensive document processing tools

def extract_educational_content_with_docling(pdf_path, standard, subject, chapter):
    """Extract structured educational content using Docling's advanced AI"""
    
    logger.info(f"🔍 Processing PDF with Docling AI: {pdf_path}")
    
    # Initialize Docling converter
    try:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
    except ImportError as e:
        return f"ERROR: Docling not available - {str(e)}"
    
    try:
        # Temporarily suppress logging during Docling processing
        import logging
        original_level = logging.getLogger().level
        logging.getLogger().setLevel(logging.CRITICAL)
        
        # Convert the PDF with advanced document understanding
        result = converter.convert(pdf_path)
        
        # Restore logging
        logging.getLogger().setLevel(original_level)
        
        logger.info(f"✅ Successfully processed {len(result.document.texts)} text elements")
        
    except Exception as e:
        # Restore logging on error
        logging.getLogger().setLevel(logging.INFO)
        logger.error(f"❌ Error processing PDF with Docling: {e}")
        return None
    
    # Extract structured educational content
    educational_content = {
        "metadata": {
            "standard": standard,
            "subject": subject, 
            "chapter": chapter,
            "total_pages": len(result.pages) if hasattr(result, 'pages') else 0
        },
        "main_text": "",
        "figures": [],
        "tables": [],
        "key_concepts": [],
        "structured_elements": [],
        "extracted_images": []  # Add this for image processing
    }
    
    # Process document elements with educational context
    for element in result.document.texts:
        element_text = element.text.strip()
        
        if not element_text:
            continue
            
        # Categorize content based on document structure
        element_info = {
            "text": element_text,
            "type": getattr(element, 'label', 'text'),
            "confidence": getattr(element, 'confidence', 1.0),
            "bbox": getattr(element, 'bbox', None)
        }
        
        # Main text content
        if element_info["type"] in ["text", "paragraph"]:
            educational_content["main_text"] += element_text + "\n\n"
            
        # Headings and key concepts
        elif element_info["type"] in ["title", "heading", "section-header"]:
            educational_content["key_concepts"].append({
                "concept": element_text,
                "type": "heading",
                "importance": "high"
            })
            educational_content["main_text"] += f"## {element_text}\n\n"
            
        # Figure captions
        elif element_info["type"] in ["caption", "figure"]:
            educational_content["figures"].append({
                "caption": element_text,
                "type": "figure",
                "context": "Educational diagram or illustration"
            })
            
        # Tables and structured data
        elif element_info["type"] in ["table", "list-item"]:
            educational_content["tables"].append({
                "content": element_text,
                "type": "structured_data",
                "format": element_info["type"]
            })
            
        # Store all elements for comprehensive analysis
        educational_content["structured_elements"].append(element_info)
    
    # Extract images if available
    if hasattr(result.document, 'images') or hasattr(result, 'images'):
        images = getattr(result.document, 'images', getattr(result, 'images', []))
        for i, img_element in enumerate(images):
            # Create image info structure
            image_info = {
                "image_path": f"temp_image_{i}.png",  # Placeholder - would need actual extraction
                "caption": f"Figure {i+1}",
                "surrounding_text": "",
                "page": 1,
                "bbox": getattr(img_element, 'bbox', None),
                "image_type": "educational_diagram"
            }
            educational_content["extracted_images"].append(image_info)
    
    logger.info(f"📊 Extracted Content Summary:")
    logger.info(f"   • Main text: {len(educational_content['main_text'])} characters")
    logger.info(f"   • Figures: {len(educational_content['figures'])} items")
    logger.info(f"   • Tables: {len(educational_content['tables'])} items") 
    logger.info(f"   • Key concepts: {len(educational_content['key_concepts'])} items")
    logger.info(f"   • Images: {len(educational_content['extracted_images'])} items")
    
    return educational_content

def create_comprehensive_educational_context(educational_content):
    """Create rich educational context from extracted structured content"""
    
    metadata = educational_content["metadata"]
    
    context = f"""
EDUCATIONAL CONTENT ANALYSIS
Subject: {metadata['subject']}
Standard: {metadata['standard']}
Chapter: {metadata['chapter']}
Pages Processed: {metadata['total_pages']}

=== MAIN CONTENT ===
{educational_content['main_text']}

=== KEY CONCEPTS IDENTIFIED ===
"""
    
    # Add key concepts with structure
    for i, concept in enumerate(educational_content['key_concepts'], 1):
        context += f"{i}. {concept['concept']} (Type: {concept['type']})\n"
    
    context += "\n=== FIGURES AND DIAGRAMS ===\n"
    # Add figure information
    for i, figure in enumerate(educational_content['figures'], 1):
        context += f"Figure {i}: {figure['caption']}\n"
        context += f"Context: {figure['context']}\n\n"
    
    context += "=== TABLES AND STRUCTURED DATA ===\n"
    # Add table information  
    for i, table in enumerate(educational_content['tables'], 1):
        context += f"Table/List {i} ({table['format']}):\n{table['content']}\n\n"
    
    return context

def azure_openai_text_analysis(text_content, standard, subject, chapter):
    """Analyze text content with Azure OpenAI for educational insights"""
    
    prompt = f"""EDUCATIONAL TEXT ANALYSIS

TARGET: {standard} students
SUBJECT: {subject} | CHAPTER: {chapter}

ANALYSIS REQUIREMENTS:
1. Extract key educational concepts
2. Identify grade-level appropriateness 
3. Highlight important facts and definitions
4. Note relationships between concepts
5. Suggest educational applications

TEXT CONTENT:
{text_content}

Provide comprehensive educational analysis suitable for {standard} level processing."""

    return call_gpt(prompt, "")

def azure_openai_image_analysis(image_path, caption, surrounding_text, standard, subject, chapter):
    """Analyze individual images with educational context using Azure OpenAI Vision"""
    
    # Encode image
    encoded_image = encode_image_base64(image_path)
    
    if encoded_image.startswith("ERROR"):
        return f"Image analysis failed: {encoded_image}"
    
    prompt = f"""EDUCATIONAL IMAGE ANALYSIS

TARGET AUDIENCE: {standard} students
SUBJECT: {subject} | CHAPTER: {chapter}

IMAGE CONTEXT:
Caption: {caption if caption else 'No caption provided'}
Surrounding Text: {surrounding_text[:500] if surrounding_text else 'No surrounding text'}

ANALYSIS REQUIRED:
1. Describe what the image shows in {standard}-appropriate language
2. Explain educational significance for {subject} - {chapter}
3. Identify key concepts illustrated
4. Suggest how this image supports learning objectives
5. Note any grade-level appropriateness concerns

Provide comprehensive educational analysis suitable for {standard} level understanding."""

    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user", 
            "content": [
                {"type": "text", "text": "Analyze this educational image:"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
            ]
        }
    ]
    
    try:
        response = azure_client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=messages,
            temperature=0.1,  # Low temperature for consistent image analysis
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: Image analysis failed - {str(e)}"

def synthesize_educational_content(text_analysis, image_analyses, standard, subject, chapter):
    """Combine text and image analyses into comprehensive educational content"""
    
    synthesis_prompt = f"""COMPREHENSIVE EDUCATIONAL CONTENT SYNTHESIS

TARGET: {standard} students | SUBJECT: {subject} | CHAPTER: {chapter}

TEXT ANALYSIS:
{text_analysis}

IMAGE ANALYSES:
{chr(10).join([f"Image {i+1}: {analysis}" for i, analysis in enumerate(image_analyses)])}

SYNTHESIS REQUIREMENTS:
1. Create unified educational narrative
2. Show how images support textual concepts
3. Identify cross-references between text and visuals
4. Highlight key learning points combining both modalities
5. Ensure grade-level appropriateness throughout
6. Structure for optimal {standard} comprehension

Generate comprehensive educational content that leverages both textual and visual information."""

    return call_gpt(synthesis_prompt, "")

def normalize_content_for_validation(content, standard):
    """Normalize extracted content for consistent validation across extraction methods"""
    
    # Extract grade number for processing level
    grade_match = re.search(r'(\d+)', standard)
    target_grade = int(grade_match.group(1)) if grade_match else 6
    
    # Determine appropriate processing level based on grade
    if target_grade <= 3:
        max_sentence_length = 12
        complexity_level = "very simple"
    elif target_grade <= 6:
        max_sentence_length = 18
        complexity_level = "simple"
    elif target_grade <= 9:
        max_sentence_length = 25
        complexity_level = "moderate"
    else:
        max_sentence_length = 35
        complexity_level = "advanced"
    
    normalization_prompt = f"""BALANCED GRADE-LEVEL CONTENT OPTIMIZATION

TARGET: {standard} students
SENTENCE LENGTH RANGE: 12-{max_sentence_length} words per sentence
COMPLEXITY LEVEL: {complexity_level}
VOCABULARY LEVEL: Age-appropriate for {standard} (not too simple, not too complex)

CRITICAL REQUIREMENTS:
1. Every sentence must be between 12-{max_sentence_length} words (not shorter than 12, not longer than {max_sentence_length})
2. Use {standard}-appropriate vocabulary (scientific terms with simple explanations)
3. Maintain educational depth suitable for {standard} cognitive level
4. Keep concepts challenging but understandable for {standard}

BALANCING RULES:
1. Break sentences longer than {max_sentence_length} words into 2-3 sentences of 12-{max_sentence_length} words each
2. Combine very short sentences (under 12 words) to reach 12-{max_sentence_length} word range
3. Use appropriate scientific vocabulary for {standard} with brief explanations when needed
4. Maintain concept complexity suitable for {standard} students
5. Use varied sentence structures (not just Subject + Verb + Object)
6. Include connecting words appropriately (because, therefore, however - but keep sentences within limit)

EXAMPLE FOR {standard}:
Bad (too long): "Science is a systematic way of understanding the natural world through observation and experimentation which helps us learn about our environment and make predictions." (26 words)
Bad (too simple): "Science helps us understand nature. We observe things. We do experiments." (12 words but too basic)
Good ({standard} level): "Science is a systematic way of understanding the natural world around us. Scientists use observation and experimentation to learn about our environment. This scientific method helps us make accurate predictions about natural phenomena." (14, 15, 13 words - appropriate complexity)

ORIGINAL CONTENT:
{content}

OPTIMIZED CONTENT (sentences 12-{max_sentence_length} words, {standard}-appropriate vocabulary and concepts):"""

    # Use balanced approach for grade-appropriate content
    messages = [
        {"role": "system", "content": f"You are an expert educational content optimizer for {standard} students. You create content with sentences between 12-{max_sentence_length} words that maintains appropriate vocabulary and concept complexity for {standard} level."},
        {"role": "user", "content": normalization_prompt}
    ]
    
    try:
        result = azure_client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=messages,
            temperature=0.05,  # Very low temperature for strict sentence control
            max_tokens=2000
        )
        normalized_content = result.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ Content normalization failed: {e}")
        normalized_content = content  # Fallback to original content
    
    logger.info(f"📝 Content normalized for {standard} validation (max {max_sentence_length} words per sentence)")
    
    return normalized_content

def enhanced_docling_extraction(pdf_path):
    """Enhanced Docling extraction that preserves image-text relationships"""
    
    # This should call the main extraction function
    return extract_educational_content_with_docling(pdf_path, "Unknown", "Unknown", "Unknown")

def process_educational_content_tool(content_source, standard, subject, chapter, content_type="pdf"):
    """Main educational content processing tool"""
    
    if content_type == "pdf":
        # Use Docling for advanced PDF processing
        educational_content = extract_educational_content_with_docling(
            content_source, standard, subject, chapter
        )
        
        if not educational_content:
            return {"error": "Failed to extract content from PDF"}
            
        # Create comprehensive educational context
        comprehensive_context = create_comprehensive_educational_context(educational_content)
        final_context = comprehensive_context
        
    elif content_type == "images":
        logger.info(f"🖼️ Processing images with vision AI: {content_source}")
        if isinstance(content_source, str):
            image_paths = [content_source]
        else:
            image_paths = content_source
            
        final_context = vision_understand_tool(image_paths, standard, subject, chapter)
        
    else:
        # Direct text input
        final_context = f"""
Subject: {subject}
Standard: {standard}
Chapter: {chapter}

Content: {content_source}
"""
    
    # Create structured educational requests
    educational_requests = [
        {"role": "system", "content": f"You are an expert educational content generator specializing in {subject} for {standard} students, focusing on {chapter}."},
        {"role": "user", "content": f"Educational content to process:\n\n{final_context}"},
        {"role": "user", "content": "First, analyze this content for appropriateness and educational value."},
        {"role": "user", "content": "Generate comprehensive study notes that highlight key concepts, definitions, and important points."},
        {"role": "user", "content": "Create 5 fill-in-the-blank exercises with clear answers, focusing on important terms and concepts."},
        {"role": "user", "content": "Design match-the-following exercises with 5 pairs that test understanding of relationships and connections."},
        {"role": "user", "content": "Formulate 3 subjective questions that encourage critical thinking and detailed explanations."}
    ]
    
    logger.info("🧠 Processing through AI educational pipeline...")
    
    # Import here to avoid circular imports
    from graph import build_graph
    compiled_graph = build_graph()
    
    result = compiled_graph.invoke({
        "messages": educational_requests,
        "standard": standard,
        "subject": subject, 
        "chapter": chapter
    })
    
    return result

def format_educational_output_tool(result):
    """Educational output formatting tool"""
    
    if not result:
        return "No educational content generated - result is None."
    
    if 'messages' not in result:
        return f"No messages found in result. Available keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dictionary'}"
    
    messages = result['messages']
    if not messages:
        return "No messages in the messages list."
    
    logger.debug(f"🔍 Debug: Found {len(messages)} messages")
    
    # Extract the assistant's response - handle both dict and BaseMessage formats
    assistant_response = None
    for i, message in enumerate(messages):
        logger.debug(f"🔍 Debug: Message {i} type: {type(message)}")
        
        # Handle dictionary format
        if isinstance(message, dict):
            role = message.get('role')
            content = message.get('content', '')
            logger.debug(f"🔍 Debug: Dict message role: {role}")
        else:
            # Handle LangChain BaseMessage format
            try:
                role = getattr(message, 'type', None) or getattr(message, 'role', None)
                content = getattr(message, 'content', '') or str(message)
                logger.debug(f"🔍 Debug: BaseMessage role: {role}")
                
                # For LangChain messages, check if it's an AIMessage (assistant)
                if hasattr(message, '__class__'):
                    class_name = message.__class__.__name__
                    logger.debug(f"🔍 Debug: Message class: {class_name}")
                    if 'AI' in class_name or 'Assistant' in class_name:
                        role = 'assistant'
            except Exception as e:
                logger.debug(f"🔍 Debug: Error processing message {i}: {e}")
                continue
        
        if role == 'assistant' and content:
            assistant_response = content
            logger.debug(f"🔍 Debug: Found assistant response with {len(content)} characters")
            break
    
    if not assistant_response:
        # Try to get the last message regardless of role
        if messages:
            last_message = messages[-1]
            if isinstance(last_message, dict):
                assistant_response = last_message.get('content', '')
            else:
                assistant_response = getattr(last_message, 'content', '') or str(last_message)
            
            if assistant_response:
                logger.debug(f"🔍 Debug: Using last message as fallback with {len(assistant_response)} characters")
            else:
                return f"No educational content found in response. Last message: {str(last_message)[:200]}..."
        else:
            return "No educational content found in response - no messages available."
    
    # Clean up and format the response
    formatted_output = []
    
    # Split by sections and format each
    sections = assistant_response.split('\n\n')
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        # Identify section headers and add proper formatting
        if section.startswith('GRADE LEVEL VALIDATION:'):
            formatted_output.append("🎯 GRADE LEVEL VALIDATION")
            formatted_output.append("=" * 50)
            
        elif section.startswith('CONTENT SAFETY ANALYSIS:'):
            formatted_output.append("\n🔒 CONTENT SAFETY ANALYSIS")
            formatted_output.append("=" * 50)
            
        elif section.startswith('CONTENT RELEVANCE CHECK:'):
            formatted_output.append("\n🎯 CONTENT RELEVANCE CHECK")
            formatted_output.append("=" * 50)
            
        elif section.startswith('COMPREHENSIVE STUDY NOTES:'):
            formatted_output.append("\n📚 COMPREHENSIVE STUDY NOTES")
            formatted_output.append("=" * 50)
            
        elif section.startswith('FILL-IN-THE-BLANKS EXERCISES:'):
            formatted_output.append("\n📝 FILL-IN-THE-BLANKS EXERCISES")
            formatted_output.append("=" * 50)
            
        elif section.startswith('MATCH-THE-FOLLOWING EXERCISES:'):
            formatted_output.append("\n🔗 MATCH-THE-FOLLOWING EXERCISES")
            formatted_output.append("=" * 50)
            
        elif section.startswith('SUBJECTIVE QUESTIONS:'):
            formatted_output.append("\n❓ SUBJECTIVE QUESTIONS")
            formatted_output.append("=" * 50)
            
        else:
            # Add content to current section
            if section and not any(section.startswith(header) for header in [
                'Grade Level Validation:', 'Content Safety:', 'Study Notes:', 
                'Fill-in-the-Blanks:', 'Match-the-Following:', 'Subjective Questions:'
            ]):
                formatted_output.append(section)
    
    if not formatted_output:
        return f"No formatted content generated. Raw response preview:\n{assistant_response[:500]}..."
    
    return "\n".join(formatted_output)

def comprehensive_validation_tool(content, target_standard, subject, chapter):
    """Single comprehensive validation check for grade, safety, and relevance"""
    
    # Extract grade number for validation
    grade_match = re.search(r'(\d+)', target_standard)
    if not grade_match:
        return {
            "status": "FAILED",
            "reason": "Invalid grade format",
            "grade_check": "ERROR: Could not extract grade number",
            "safety_check": "SKIPPED",
            "relevance_check": "SKIPPED"
        }
    
    target_grade = int(grade_match.group(1))
    
    # Get grade standards for context
    if target_grade not in grade_validator.standards:
        return {
            "status": "FAILED", 
            "reason": "Unsupported grade",
            "grade_check": f"ERROR: Grade {target_grade} not supported",
            "safety_check": "SKIPPED",
            "relevance_check": "SKIPPED"
        }
    
    standards = grade_validator.standards[target_grade]
    
    # Create comprehensive validation prompt
    validation_prompt = f"""COMPREHENSIVE CONTENT VALIDATION

TARGET: {target_standard} ({standards.age_range})
SUBJECT: {subject}
CHAPTER: {chapter}

VALIDATION REQUIREMENTS:
1. GRADE APPROPRIATENESS: Is content suitable for {target_standard} students?
   - Vocabulary level: {standards.vocabulary_level}
   - Sentence complexity: {standards.sentence_length}
   - Concept difficulty: {standards.concept_complexity}

2. SAFETY CHECK: Is content safe for children?
   - No violence, inappropriate themes, or mature content
   - Age-appropriate language and concepts

3. RELEVANCE CHECK: Does content match the subject and chapter?
   - Subject: {subject}
   - Chapter: {chapter}
   - Content should be relevant to this specific topic

CONTENT TO VALIDATE:
{content}

REQUIRED RESPONSE FORMAT (EXACTLY):
GRADE_CHECK: [PASS/FAIL]
SAFETY_CHECK: [PASS/FAIL] 
RELEVANCE_CHECK: [PASS/FAIL]
OVERALL_STATUS: [PASS/FAIL]
REASON: [Brief explanation if any check failed]

VALIDATION RULES:
- GRADE_CHECK: PASS only if content is specifically appropriate for {target_standard} (be strict about grade level)
  * Class 1-2: Very simple vocabulary, 3-8 words per sentence, concrete concepts only
  * Class 3-4: Basic vocabulary, 6-12 words per sentence, simple processes
  * Class 5-6: Moderate vocabulary, 10-18 words per sentence, some abstract concepts
  * Class 7-8: Advanced vocabulary, 15-25 words per sentence, complex concepts
  * Class 9-12: Sophisticated vocabulary, 20+ words per sentence, theoretical concepts
- SAFETY_CHECK: PASS if content is safe for children (ignore subject relevance)
- RELEVANCE_CHECK: PASS if content matches {subject} and {chapter}
- OVERALL_STATUS: PASS only if ALL three checks pass
- REASON: Only provide if OVERALL_STATUS is FAIL

STRICT GRADE ASSESSMENT:
- If content seems designed for 2+ grades higher → FAIL
- If content seems designed for 2+ grades lower → FAIL
- Only PASS if content is specifically appropriate for {target_standard}

EXAMPLE RESPONSES:
✓ All Pass: "GRADE_CHECK: PASS\nSAFETY_CHECK: PASS\nRELEVANCE_CHECK: PASS\nOVERALL_STATUS: PASS\nREASON: All validations passed"

✗ Grade Fail: "GRADE_CHECK: FAIL\nSAFETY_CHECK: PASS\nRELEVANCE_CHECK: PASS\nOVERALL_STATUS: FAIL\nREASON: Content designed for Class 6 is too advanced for {target_standard}"

✗ Relevance Fail: "GRADE_CHECK: PASS\nSAFETY_CHECK: PASS\nRELEVANCE_CHECK: FAIL\nOVERALL_STATUS: FAIL\nREASON: Science content doesn't match {subject} subject"

✗ Grade Too Simple: "GRADE_CHECK: FAIL\nSAFETY_CHECK: PASS\nRELEVANCE_CHECK: PASS\nOVERALL_STATUS: FAIL\nREASON: Content designed for lower grades is too simple for {target_standard}"
"""

    try:
        # Single AI call for all validations
        ai_response = call_gpt(validation_prompt, "")
        
        # Parse the structured response
        result = {
            "status": "FAILED",
            "reason": "Parsing error",
            "grade_check": "UNKNOWN",
            "safety_check": "UNKNOWN", 
            "relevance_check": "UNKNOWN"
        }
        
        lines = ai_response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('GRADE_CHECK:'):
                result["grade_check"] = "PASS" if "PASS" in line else "FAIL"
            elif line.startswith('SAFETY_CHECK:'):
                result["safety_check"] = "PASS" if "PASS" in line else "FAIL"
            elif line.startswith('RELEVANCE_CHECK:'):
                result["relevance_check"] = "PASS" if "PASS" in line else "FAIL"
            elif line.startswith('OVERALL_STATUS:'):
                result["status"] = "PASS" if "PASS" in line else "FAILED"
            elif line.startswith('REASON:'):
                result["reason"] = line.replace('REASON:', '').strip()
        
        logger.info(f"🔍 Comprehensive Validation: {result['status']} - Grade:{result['grade_check']} Safety:{result['safety_check']} Relevance:{result['relevance_check']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Comprehensive validation failed: {e}")
        return {
            "status": "FAILED",
            "reason": f"Validation error: {str(e)}",
            "grade_check": "ERROR",
            "safety_check": "ERROR",
            "relevance_check": "ERROR"
        }
