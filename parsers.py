import re
from models import StructuredContent, FillInTheBlanks, MatchTheFollowing, QuestionAnswer

def parse_educational_content(raw_content: str) -> StructuredContent:
    """Parse raw content into structured format"""
    
    sections = {
        'grade_validation': '',
        'study_notes': '',
        'fill_blanks': '',
        'match_following': '',
        'questions': ''
    }
    
    current_section = None
    lines = raw_content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if 'COMPREHENSIVE VALIDATION RESULTS:' in line:
            current_section = 'grade_validation'
        elif 'COMPREHENSIVE STUDY NOTES' in line:
            current_section = 'study_notes'
        elif 'FILL-IN-THE-BLANKS EXERCISES' in line:
            current_section = 'fill_blanks'
        elif 'MATCH-THE-FOLLOWING EXERCISES' in line:
            current_section = 'match_following'
        elif 'SUBJECTIVE QUESTIONS' in line:
            current_section = 'questions'
        elif line.startswith('='):
            continue
        elif current_section and line:
            sections[current_section] += line + '\n'
    
    return StructuredContent(
        importantNotes=sections['study_notes'].strip(),
        fillInTheBlanks=parse_fill_in_blanks(sections['fill_blanks']),
        matchTheFollowing=parse_match_following(sections['match_following']),
        questionAnswer=parse_questions_answers(sections['questions'])
    )

def parse_fill_in_blanks(content: str) -> FillInTheBlanks:
    """Parse fill-in-blanks section"""
    questions = {}
    answers = {}
    
    pattern = r'(\d+)\.\s*(.*?)\s*\n\s*Answer:\s*(.*?)(?=\n\d+\.|\n\n|$)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        num, question, answer = match
        questions[num] = question.strip()
        answers[num] = answer.strip()
    
    return FillInTheBlanks(questions=questions, answers=answers)

def parse_match_following(content: str) -> MatchTheFollowing:
    """Parse match-the-following section with aggressive extraction"""
    column_a = {}
    column_b = {}
    answers = {}
    
    if not content or content.strip() == "Not generated":
        return MatchTheFollowing(column_a=column_a, column_b=column_b, answers=answers)
    
    # More aggressive parsing - look for the patterns anywhere in the content
    
    # Extract Column A items
    column_a_match = re.search(r'Column A:\s*(.*?)(?=Column B:|Answers:|$)', content, re.DOTALL)
    if column_a_match:
        items_text = column_a_match.group(1)
        items = re.findall(r'(\d+)\.([^0-9]+?)(?=\d+\.|$)', items_text)
        for num, item in items:
            column_a[num] = item.strip()
    
    # Extract Column B items
    column_b_match = re.search(r'Column B:\s*(.*?)(?=Answers:|$)', content, re.DOTALL)
    if column_b_match:
        items_text = column_b_match.group(1).strip()
        # Split on letter patterns and extract
        parts = re.split(r'\s*([A-E])\.', items_text)
        # parts will be ['', 'A', 'text1', 'B', 'text2', 'C', 'text3', ...]
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                letter = parts[i]
                text = parts[i + 1].strip()
                # Remove any trailing letter pattern that might be attached
                text = re.sub(r'\s*[A-E]\..*$', '', text).strip()
                if text:
                    column_b[letter] = text
    
    # Extract Answers
    answers_match = re.search(r'Answers?:\s*(.+)', content)
    if answers_match:
        answers_text = answers_match.group(1)
        pairs = re.findall(r'(\d+)-([A-Z])', answers_text)
        for num, letter in pairs:
            answers[num] = letter
    
    # Fallback: Extract any numbered and lettered items
    if not column_a:
        numbered_items = re.findall(r'(\d+)\.([^0-9\n]+)', content)
        for num, item in numbered_items[:5]:
            column_a[num] = item.strip()
    
    if not column_b:
        lettered_items = re.findall(r'([A-E])\.([^A-E\n]+)', content)
        for letter, item in lettered_items[:5]:
            column_b[letter] = item.strip()
    
    # Generate answers if missing
    if column_a and column_b and not answers:
        nums = sorted(column_a.keys())[:5]
        letters = sorted(column_b.keys())[:5]
        for i, num in enumerate(nums):
            if i < len(letters):
                answers[num] = letters[i]
    
    return MatchTheFollowing(column_a=column_a, column_b=column_b, answers=answers)

def parse_questions_answers(content: str) -> QuestionAnswer:
    """Parse questions and answers section"""
    questions = {}
    answers = {}
    
    pattern = r'Q(\d+):\s*(.*?)\s*A\1:\s*(.*?)(?=Q\d+:|$)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        num, question, answer = match
        questions[f"Q{num}"] = question.strip()
        answers[f"Q{num}"] = answer.strip()
    
    return QuestionAnswer(questions=questions, answers=answers) 