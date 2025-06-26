from pydantic import BaseModel
from typing import Dict, Optional

class FillInTheBlanks(BaseModel):
    """Model for fill-in-the-blanks exercises"""
    questions: Dict[str, str]  # {"1": "Science is a way of...", "2": "..."}
    answers: Dict[str, str]    # {"1": "universe", "2": "observation"}

class MatchTheFollowing(BaseModel):
    """Model for match-the-following exercises"""
    column_a: Dict[str, str]   # {"1": "Curiosity", "2": "Scientific Method"}
    column_b: Dict[str, str]   # {"A": "A guess that can be tested", "B": "..."}
    answers: Dict[str, str]    # {"1": "C", "2": "D", "3": "B"}

class QuestionAnswer(BaseModel):
    """Model for question-answer pairs"""
    questions: Dict[str, str]  # {"Q1": "Question text", "Q2": "..."}
    answers: Dict[str, str]    # {"Q1": "Answer text", "Q2": "..."}

class StructuredContent(BaseModel):
    """Main model for structured educational content"""
    importantNotes: str
    fillInTheBlanks: FillInTheBlanks
    matchTheFollowing: MatchTheFollowing
    questionAnswer: QuestionAnswer
    gradeValidation: Optional[str] = None
    safetyAnalysis: Optional[str] = None
    relevanceCheck: Optional[str] = None

class ProcessResponse(BaseModel):
    """API response model for the processing endpoint"""
    success: bool
    message: str
    content: Optional[StructuredContent] = None
    error: Optional[str] = None
    metadata: Optional[dict] = None 