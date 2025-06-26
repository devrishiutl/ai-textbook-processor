import re
from models import StructuredContent, FillInTheBlanks, MatchTheFollowing, QuestionAnswer

def parse_educational_content(raw_content: str) -> StructuredContent:
    """Parse the raw educational content into structured JSON format"""
    
    # Initialize sections
    sections = {
        'grade_validation': '',
        'safety_analysis': '',
        'relevance_check': '',
        'study_notes': '',
        'fill_blanks': '',
        'match_following': '',
        'questions': ''
    }
    
    # Split content by section headers
    current_section = None
    lines = raw_content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Identify section headers (updated for new comprehensive validation format)
        if 'COMPREHENSIVE VALIDATION RESULTS:' in line:
            current_section = 'grade_validation'  # Store all validation info here
        elif 'COMPREHENSIVE STUDY NOTES' in line:  # Remove colon requirement
            current_section = 'study_notes'
        elif 'FILL-IN-THE-BLANKS EXERCISES' in line:  # Remove colon requirement
            current_section = 'fill_blanks'
        elif 'MATCH-THE-FOLLOWING EXERCISES' in line:  # Remove colon requirement
            current_section = 'match_following'
        elif 'SUBJECTIVE QUESTIONS' in line:  # Remove colon requirement
            current_section = 'questions'
        elif line.startswith('='):
            continue  # Skip separator lines
        elif current_section and line:
            sections[current_section] += line + '\n'
    
    # Parse Fill-in-the-Blanks
    fill_blanks_data = parse_fill_in_blanks(sections['fill_blanks'])
    
    # Parse Match-the-Following
    match_following_data = parse_match_following(sections['match_following'])
    
    # Parse Questions and Answers
    qa_data = parse_questions_answers(sections['questions'])
    
    # Parse comprehensive validation results
    validation_text = sections['grade_validation'].strip()
    grade_validation = ""
    safety_analysis = ""
    relevance_check = ""
    
    # Extract individual validation results from comprehensive format
    if validation_text:
        lines = validation_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('Grade Check:'):
                grade_validation = line.replace('Grade Check:', '').strip()
            elif line.startswith('Safety Check:'):
                safety_analysis = line.replace('Safety Check:', '').strip()
            elif line.startswith('Relevance Check:'):
                relevance_check = line.replace('Relevance Check:', '').strip()
    
    return StructuredContent(
        importantNotes=sections['study_notes'].strip(),
        fillInTheBlanks=fill_blanks_data,
        matchTheFollowing=match_following_data,
        questionAnswer=qa_data
        # Validation details now only in metadata.validation_details
    )

def parse_fill_in_blanks(content: str) -> FillInTheBlanks:
    """Parse fill-in-the-blanks section"""
    questions = {}
    answers = {}
    
    # New simplified pattern: 1. Question text with ________ blank
    #                        Answer: word
    pattern = r'(\d+)\.\s*(.*?)\s*\n\s*Answer:\s*(.*?)(?=\n\d+\.|\n\n|$)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        num, question, answer = match
        questions[num] = question.strip()
        answers[num] = answer.strip()
    
    return FillInTheBlanks(questions=questions, answers=answers)

def parse_match_following(content: str) -> MatchTheFollowing:
    """Parse match-the-following section"""
    column_a = {}
    column_b = {}
    answers = {}
    
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # New simplified format: Column A: 1. Item1  2. Item2  3. Item3  4. Item4  5. Item5
        if line.startswith('Column A:'):
            # Extract items after "Column A:"
            items_text = line.replace('Column A:', '').strip()
            # Pattern: 1. Item1  2. Item2  etc.
            items = re.findall(r'(\d+)\.\s*([^0-9]+?)(?=\s*\d+\.|$)', items_text)
            for num, item in items:
                column_a[num] = item.strip()
                
        elif line.startswith('Column B:'):
            # Extract items after "Column B:"
            items_text = line.replace('Column B:', '').strip()
            # Pattern: A. Match1  B. Match2  etc.
            items = re.findall(r'([A-Z])\.\s*([^A-Z]+?)(?=\s*[A-Z]\.|$)', items_text)
            for letter, item in items:
                column_b[letter] = item.strip()
                
        elif line.startswith('Answers:'):
            # Extract answers: 1-A, 2-B, 3-C, 4-D, 5-E
            answers_text = line.replace('Answers:', '').strip()
            pairs = re.findall(r'(\d+)-([A-Z])', answers_text)
            for num, letter in pairs:
                answers[num] = letter
    
    return MatchTheFollowing(column_a=column_a, column_b=column_b, answers=answers)

def parse_questions_answers(content: str) -> QuestionAnswer:
    """Parse questions and answers section"""
    questions = {}
    answers = {}
    
    # New simplified pattern: Q1: [question]
    #                        A1: [answer]
    pattern = r'Q(\d+):\s*(.*?)\s*A\1:\s*(.*?)(?=Q\d+:|$)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        num, question, answer = match
        questions[f"Q{num}"] = question.strip()
        answers[f"Q{num}"] = answer.strip()
    
    return QuestionAnswer(questions=questions, answers=answers) 