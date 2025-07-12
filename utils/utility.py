"""
Image Processing and Vision AI Utilities
Follows SOLID principles with proper separation of concerns
"""
import os
import base64
import requests
from typing import List, Tuple, Optional, Union
from dataclasses import dataclass
from PIL import Image
import io
from config.configuration import get_llm_client, get_model_name
from config.settings import (
    IMAGE_TARGET_SIZE, IMAGE_QUALITY, IMAGE_MAX_TOKENS, IMAGE_TEMPERATURE,
    VISION_SYSTEM_PROMPT, VISION_USER_PROMPT
)
from langsmith import traceable


@dataclass
class ImageProcessingConfig:
    """Configuration for image processing"""
    target_size: Tuple[int, int] = IMAGE_TARGET_SIZE
    quality: int = IMAGE_QUALITY
    max_tokens: int = IMAGE_MAX_TOKENS
    temperature: float = IMAGE_TEMPERATURE


class ImagePreprocessor:
    """Handles image preprocessing operations"""
    
    def __init__(self, config: ImageProcessingConfig):
        self.config = config
    
    def resize_image(self, img: Image.Image) -> Image.Image:
        """Resize image while maintaining aspect ratio"""
        aspect_ratio = img.width / img.height
        
        if aspect_ratio > 1:
            # Width is larger
            new_width = min(img.width, self.config.target_size[0])
            new_height = int(new_width / aspect_ratio)
        else:
            # Height is larger
            new_height = min(img.height, self.config.target_size[1])
            new_width = int(new_height * aspect_ratio)
        
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def convert_to_rgb(self, img: Image.Image) -> Image.Image:
        """Convert image to RGB format"""
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            return background
        elif img.mode != 'RGB':
            return img.convert('RGB')
        return img
    
    def encode_to_base64(self, img: Image.Image) -> str:
        """Encode image to base64 string"""
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=self.config.quality, optimize=True)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def preprocess_image(self, image_path: str) -> Union[str, str]:
        """
        Preprocess image for LLM processing
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image or error message
        """
        try:
            img = Image.open(image_path)
            img = self.resize_image(img)
            img = self.convert_to_rgb(img)
            return self.encode_to_base64(img)
        except Exception as e:
            return f"ERROR: Image preprocessing failed - {str(e)}"


class VisionPromptBuilder:
    """Builds prompts for vision AI processing"""
    
    @staticmethod
    def build_system_prompt() -> str:
        """Build system prompt for text extraction"""
        return VISION_SYSTEM_PROMPT
    
    @staticmethod
    def build_user_prompt() -> str:
        """Build user prompt for text extraction"""
        return VISION_USER_PROMPT


class VisionAIProcessor:
    """Handles vision AI processing with proper separation of concerns"""
    
    def __init__(self, config: ImageProcessingConfig):
        self.config = config
        self.preprocessor = ImagePreprocessor(config)
        self.prompt_builder = VisionPromptBuilder()
        self.llm_client = get_llm_client()
        self.model_name = get_model_name()
    
    def create_image_content(self, encoded_image: str) -> dict:
        """Create image content for LLM"""
        return {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}
        }
    
    def process_images(self, image_paths: List[str]) -> str:
        """
        Process multiple images with vision AI
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            Extracted text content or error message
        """
        try:
            # Build user content with text prompt
            user_content = [
                {"type": "text", "text": self.prompt_builder.build_user_prompt()}
            ]
            
            # Process each image
            for img_path in image_paths:
                encoded = self.preprocessor.preprocess_image(img_path)
                
                if encoded.startswith("ERROR"):
                    return encoded
                
                user_content.append(self.create_image_content(encoded))
            
            # Make LLM request
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.prompt_builder.build_system_prompt()},
                    {"role": "user", "content": user_content}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"ERROR: Vision processing failed - {str(e)}"


class ImageContentExtractor:
    """High-level interface for image content extraction"""
    
    def __init__(self, config: Optional[ImageProcessingConfig] = None):
        self.config = config or ImageProcessingConfig()
        self.processor = VisionAIProcessor(self.config)
    
    def extract_content(self, image_paths: List[str]) -> str:
        """
        Extract content from images using vision AI
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            Extracted text content or error message
        """
        if not image_paths:
            return "No images provided"
        
        return self.processor.process_images(image_paths)


# Legacy functions for backward compatibility
@traceable(name="image_vision_processing")
def vision_understand_tool(images: List[str], standard: str = "", subject: str = "", chapter: str = "") -> str:
    """Legacy function for backward compatibility"""
    extractor = ImageContentExtractor()
    return extractor.extract_content(images)


def preprocess_image(image_path: str, target_size: Tuple[int, int] = IMAGE_TARGET_SIZE, quality: int = IMAGE_QUALITY) -> str:
    """Legacy function for backward compatibility"""
    config = ImageProcessingConfig(target_size=target_size, quality=quality)
    preprocessor = ImagePreprocessor(config)
    return preprocessor.preprocess_image(image_path)


def read_data_from_image(image_paths: List[str]) -> str:
    """Legacy function for backward compatibility"""
    extractor = ImageContentExtractor()
    return extractor.extract_content(image_paths) 