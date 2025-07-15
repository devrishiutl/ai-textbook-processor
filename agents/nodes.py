"""
Graph Nodes following SOLID principles
"""
from typing import Dict, Any, Protocol, Optional, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
from config.configuration import get_validation_llm, get_generation_llm
from config.logging import get_logger
from config.settings import (
    VALIDATION_MAX_CONTENT_LENGTH, GENERATION_MAX_CONTENT_LENGTH,
    VALIDATION_CRITERIA, NODE_TEMPLATE_PATH,
    VALIDATION_PROMPT_TEMPLATE, GENERATION_PROMPT_TEMPLATE,
    GENERATION_JSON_TEMPLATE
)
from langsmith import traceable
from pydantic import BaseModel, Field
from trustcall import create_extractor
import re
import json

logger = get_logger(__name__)


# ===== PYDANTIC MODELS =====

class ValidationResult(BaseModel):
    """Validation result schema"""
    grade_check: str = Field(description="Whether content is appropriate for the grade level")
    safety_check: str = Field(description="Whether content is safe and appropriate")
    relevance_check: str = Field(description="Whether content is relevant to the subject/chapter")
    reason: str = Field(description="Brief explanation of the validation result")


class Flashcard(BaseModel):
    """Flashcard schema"""
    term: str = Field(description="The key term")
    definition: str = Field(description="Clear and concise definition of the term")
    example: str = Field(description="Example or usage of the term")


class MCQQuestion(BaseModel):
    """Multiple choice question schema"""
    question: str = Field(description="The question text")
    options: Dict[str, str] = Field(description="Answer options A, B, C, D")
    correct_answer: str = Field(description="The correct answer (A, B, C, or D)")
    explanation: str = Field(description="Brief explanation of why this is correct")


class FillInTheBlanks(BaseModel):
    """Fill in the blanks section schema"""
    questions: Dict[str, str] = Field(description="Fill in the blank questions")
    answers: Dict[str, str] = Field(description="Answers for the questions")


class MatchTheFollowing(BaseModel):
    """Match the following section schema"""
    column_a: Dict[str, str] = Field(description="Terms in column A")
    column_b: Dict[str, str] = Field(description="Definitions in column B")
    answers: Dict[str, str] = Field(description="Matching answers")


class QuestionAnswer(BaseModel):
    """Question and answer section schema"""
    questions: Dict[str, str] = Field(description="Questions")
    answers: Dict[str, str] = Field(description="Answers to the questions")


class MCQSection(BaseModel):
    """MCQ section schema"""
    questions: Dict[str, MCQQuestion] = Field(description="Multiple choice questions")


class GenerationResult(BaseModel):
    """Generation result schema matching the JSON template"""
    importantNotes: str = Field(description="Study notes with markdown formatting")
    flashcards: Dict[str, Flashcard] = Field(description="Flashcards with key terms")
    mcq: MCQSection = Field(description="Multiple choice questions section")
    fillInTheBlanks: FillInTheBlanks = Field(description="Fill in the blank questions")
    matchTheFollowing: MatchTheFollowing = Field(description="Match the following questions")
    questionAnswer: QuestionAnswer = Field(description="Question and answer section")


# ===== ABSTRACTIONS =====

class LLMProvider(Protocol):
    """Abstract LLM provider interface"""
    def invoke(self, prompt: str) -> Any:
        ...


class PromptBuilder(ABC):
    """Abstract prompt builder"""
    @abstractmethod
    def build_prompt(self, context: Dict[str, Any]) -> str:
        pass


class JSONParser(ABC):
    """Abstract JSON parser"""
    @abstractmethod
    def parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        pass


class StateManager(ABC):
    """Abstract state manager"""
    @abstractmethod
    def update_state(self, state: Dict[str, Any], key: str, value: Any) -> None:
        pass


# ===== CONCRETE IMPLEMENTATIONS =====

@dataclass
class ValidationConfig:
    """Configuration for validation"""
    max_content_length: int = VALIDATION_MAX_CONTENT_LENGTH
    validation_criteria: Dict[str, str] = None
    
    def __post_init__(self):
        if self.validation_criteria is None:
            self.validation_criteria = VALIDATION_CRITERIA


@dataclass
class GenerationConfig:
    """Configuration for content generation"""
    max_content_length: int = GENERATION_MAX_CONTENT_LENGTH
    template_path: Optional[str] = NODE_TEMPLATE_PATH


class ValidationPromptBuilder(PromptBuilder):
    """Builds validation prompts"""
    
    def build_prompt(self, context: Dict[str, Any]) -> str:
        content = context.get("content", "")[:VALIDATION_MAX_CONTENT_LENGTH]
        standard = context.get("standard", "")
        subject = context.get("subject", "")
        chapter = context.get("chapter", "")
        
        return VALIDATION_PROMPT_TEMPLATE.format(
            standard=standard,
            subject=subject,
            chapter=chapter,
            content=content
        )


class GenerationPromptBuilder(PromptBuilder):
    """Builds content generation prompts"""
    
    def __init__(self, template: str):
        self.template = template
    
    def build_prompt(self, context: Dict[str, Any]) -> str:
        content = context.get("content", "")[:GENERATION_MAX_CONTENT_LENGTH]
        standard = context.get("standard", "")
        subject = context.get("subject", "")
        chapter = context.get("chapter", "")
        
        return GENERATION_PROMPT_TEMPLATE.format(
            standard=standard,
            subject=subject,
            chapter=chapter,
            content=content,
            template=self.template
        )


class TrustcallJSONParser(JSONParser):
    """Parses JSON using trustcall for robust error handling"""
    
    def __init__(self, llm, model_class):
        self.llm = llm
        self.model_class = model_class
        self.extractor = create_extractor(
            llm,
            tools=[model_class],
            tool_choice=model_class.__name__
        )
    
    def parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            # Use trustcall to extract structured output
            result = self.extractor.invoke({
                "messages": [{"role": "user", "content": text}]
            })
            
            if result["responses"]:
                parsed_result = result["responses"][0]
                return parsed_result.model_dump()
            else:
                logger.error(f"No {self.model_class.__name__} result returned from trustcall")
                return None
                
        except Exception as e:
            logger.error(f"Trustcall JSON parsing error: {e}")
            return None


class StateManagerImpl(StateManager):
    """Concrete state manager implementation"""
    
    def update_state(self, state: Dict[str, Any], key: str, value: Any) -> None:
        state[key] = value


class TokenUsageTracker:
    """Tracks token usage for cost monitoring"""
    
    @staticmethod
    def log_usage(response: Any, operation: str) -> None:
        if hasattr(response, 'usage'):
            usage = response.usage
            logger.info(f"{operation} tokens - Input: {usage.prompt_tokens}, Output: {usage.completion_tokens}, Total: {usage.total_tokens}")


# ===== VALIDATION LOGIC =====

class ContentValidator:
    """Handles content validation logic"""
    
    def __init__(self, config: ValidationConfig):
        self.config = config
        self.prompt_builder = ValidationPromptBuilder()
        self.state_manager = StateManagerImpl()
        self.token_tracker = TokenUsageTracker()
    
    def validate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content using SOLID principles with trustcall"""
        try:
            # Build prompt
            prompt = self.prompt_builder.build_prompt(state)
            
            # Get LLM and create trustcall parser
            llm = get_validation_llm()
            json_parser = TrustcallJSONParser(llm, ValidationResult)
            
            # Track usage (if available)
            try:
                self.token_tracker.log_usage(llm, "Validation")
            except:
                pass
            
            # Parse response using trustcall
            validation_result = json_parser.parse_json(prompt)
            
            if validation_result:
                self.state_manager.update_state(state, "validation_result", validation_result)
                self._check_validation_result(state, validation_result)
            else:
                self.state_manager.update_state(state, "error", "Failed to generate valid validation JSON")
                self.state_manager.update_state(state, "validation_result", "ERROR")
                
        except Exception as e:
            self._handle_validation_error(state, e)
        
        return state
    
    def _check_validation_result(self, state: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Check if validation passed"""
        criteria = self.config.validation_criteria
        
        if all(result.get(key) == value for key, value in criteria.items()):
            self.state_manager.update_state(state, "is_valid", True)
            logger.info("Validation passed")
        else:
            reason = result.get("reason", "Validation failed")
            self.state_manager.update_state(state, "error", f"Content validation failed: {reason}")
            logger.warning(f"Validation failed: {reason}")
    
    def _handle_validation_error(self, state: Dict[str, Any], error: Exception) -> None:
        """Handle validation errors"""
        import traceback
        error_details = f"Validation error: {str(error)}\nFull traceback:\n{traceback.format_exc()}"
        self.state_manager.update_state(state, "error", f"Validation error: {str(error)}")
        self.state_manager.update_state(state, "validation_result", "ERROR")
        logger.error(error_details)


# ===== CONTENT GENERATION LOGIC =====

class ContentGenerator:
    """Handles content generation logic"""
    
    def __init__(self, config: GenerationConfig):
        self.config = config
        self.state_manager = StateManagerImpl()
        self.token_tracker = TokenUsageTracker()
        self.prompt_builder = GenerationPromptBuilder(GENERATION_JSON_TEMPLATE)
    
    def generate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content using SOLID principles with trustcall"""
        # Check if validation passed
        if not state.get("is_valid"):
            logger.warning("Skipping content generation - validation failed")
            return state
        
        try:
            # Build prompt
            prompt = self.prompt_builder.build_prompt(state)
            
            # Get LLM and create trustcall parser
            llm = get_generation_llm()
            json_parser = TrustcallJSONParser(llm, GenerationResult)
            
            # Track usage (if available)
            try:
                self.token_tracker.log_usage(llm, "Generation")
            except:
                pass
            
            # Parse response using trustcall
            generated_content = json_parser.parse_json(prompt)
            
            if generated_content:
                self.state_manager.update_state(state, "generated_content", generated_content)
                self.state_manager.update_state(state, "success", True)
                logger.info("Content generation completed successfully")
            else:
                self.state_manager.update_state(state, "error", "Failed to generate valid JSON")
                logger.error("Failed to generate valid JSON")
                
        except Exception as e:
            self._handle_generation_error(state, e, prompt)
        
        return state
    

    
    def _handle_generation_error(self, state: Dict[str, Any], error: Exception, prompt: str) -> None:
        """Handle generation errors"""
        import traceback
        error_details = f"Generation error: {str(error)}\nFull traceback:\n{traceback.format_exc()}"
        self.state_manager.update_state(state, "error", f"Generation error: {str(error)}")
        logger.error(error_details)
        logger.error(f"Prompt that caused error: {prompt[:500]}...")


# ===== GRAPH NODES (LEGACY INTERFACE) =====

@traceable(name="content_validation")
def validate_content(state: Dict[str, Any]) -> Dict[str, Any]:
    """Validate content - Legacy interface for graph compatibility"""
    validator = ContentValidator(ValidationConfig())
    return validator.validate(state)


@traceable(name="educational_content_generation")
def generate_content(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate content - Legacy interface for graph compatibility"""
    generator = ContentGenerator(GenerationConfig())
    return generator.generate(state) 