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
        
        # Identify section headers
        if '🎯 GRADE LEVEL VALIDATION' in line:
            current_section = 'grade_validation'
        elif '🔒 CONTENT SAFETY ANALYSIS' in line:
            current_section = 'safety_analysis'
        elif '🎯 CONTENT RELEVANCE CHECK' in line:
            current_section = 'relevance_check'
        elif '📚 COMPREHENSIVE STUDY NOTES' in line:
            current_section = 'study_notes'
        elif '📝 FILL-IN-THE-BLANKS EXERCISES' in line:
            current_section = 'fill_blanks'
        elif '🔗 MATCH-THE-FOLLOWING EXERCISES' in line:
            current_section = 'match_following'
        elif '❓ SUBJECTIVE QUESTIONS' in line:
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
    
    return StructuredContent(
        importantNotes=sections['study_notes'].strip(),
        fillInTheBlanks=fill_blanks_data,
        matchTheFollowing=match_following_data,
        questionAnswer=qa_data,
        gradeValidation=sections['grade_validation'].strip(),
        safetyAnalysis=sections['safety_analysis'].strip(),
        relevanceCheck=sections['relevance_check'].strip()
    )

def parse_fill_in_blanks(content: str) -> FillInTheBlanks:
    """Parse fill-in-the-blanks section"""
    questions = {}
    answers = {}
    
    # Pattern: 1. Question text with ________.
    #          **Answer:** answer_text
    pattern = r'(\d+)\.\s*(.*?)\s*\n\s*\*\*Answer:\*\*\s*(.*?)(?=\n\d+\.|\n\n|$)'
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
    current_column = None
    
    for line in lines:
        line = line.strip()
        
        if 'Column A:' in line:
            current_column = 'A'
        elif 'Column B:' in line:
            current_column = 'B'
        elif '**Answers:**' in line:
            current_column = 'answers'
        elif current_column == 'A' and re.match(r'^\d+\.', line):
            # Pattern: 1. Text
            match = re.match(r'^(\d+)\.\s*(.*)', line)
            if match:
                column_a[match.group(1)] = match.group(2)
        elif current_column == 'B' and re.match(r'^[A-Z]\.', line):
            # Pattern: A. Text
            match = re.match(r'^([A-Z])\.\s*(.*)', line)
            if match:
                column_b[match.group(1)] = match.group(2)
        elif current_column == 'answers' and ' - ' in line:
            # Pattern: 1 - C, 2 - D, 3 - B
            parts = line.split(', ')
            for part in parts:
                if ' - ' in part:
                    num, letter = part.split(' - ')
                    answers[num.strip()] = letter.strip()
    
    return MatchTheFollowing(column_a=column_a, column_b=column_b, answers=answers)

def parse_questions_answers(content: str) -> QuestionAnswer:
    """Parse questions and answers section"""
    questions = {}
    answers = {}
    
    # Pattern: **Question 1:** Question text
    #          **Answer:** Answer text
    pattern = r'\*\*Question\s*(\d+):\*\*\s*(.*?)\s*\*\*Answer:\*\*\s*(.*?)(?=\*\*Question|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        num, question, answer = match
        questions[f"Q{num}"] = question.strip()
        answers[f"Q{num}"] = answer.strip()
    
    return QuestionAnswer(questions=questions, answers=answers) 