"""
Image Processing Service
"""
import logging
import os
import base64
from typing import List, Optional
from PIL import Image
import io

logger = logging.getLogger(__name__)

def preprocess_image(image_path: str) -> str:
    """Preprocess image for vision AI"""
    try:
        if not os.path.exists(image_path):
            return f"ERROR: Image file not found: {image_path}"
        
        # Check file extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        file_ext = os.path.splitext(image_path)[1].lower()
        
        if file_ext not in valid_extensions:
            return f"ERROR: Unsupported image format: {file_ext}"
        
        # Open and resize image if needed
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large (max 2048x2048)
            max_size = 2048
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            img_data = buffer.getvalue()
            
            return base64.b64encode(img_data).decode('utf-8')
            
    except Exception as e:
        logger.error(f"Error preprocessing image {image_path}: {str(e)}")
        return f"ERROR: Failed to preprocess image - {str(e)}"

def extract_text_from_images(image_paths: List[str]) -> str:
    """Extract text from images using OCR"""
    try:
        if not image_paths:
            return "ERROR: No image paths provided"
        
        extracted_texts = []
        
        for img_path in image_paths:
            try:
                # For now, we'll use vision AI instead of OCR
                # This function is kept for compatibility
                logger.info(f"Processing image: {img_path}")
                extracted_texts.append(f"Image processed: {os.path.basename(img_path)}")
                
            except Exception as e:
                logger.warning(f"Failed to process image {img_path}: {str(e)}")
                extracted_texts.append(f"Error processing {os.path.basename(img_path)}: {str(e)}")
        
        if extracted_texts:
            return "\n".join(extracted_texts)
        else:
            return "ERROR: No images could be processed"
            
    except Exception as e:
        logger.error(f"Error extracting text from images: {str(e)}")
        return f"ERROR: Failed to extract text from images - {str(e)}"

def validate_image_file(image_path: str) -> dict:
    """Validate image file"""
    validation = {
        "is_valid": False,
        "file_size": 0,
        "dimensions": None,
        "error_message": ""
    }
    
    try:
        if not os.path.exists(image_path):
            validation["error_message"] = f"Image file not found: {image_path}"
            return validation
        
        # Check file extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        file_ext = os.path.splitext(image_path)[1].lower()
        
        if file_ext not in valid_extensions:
            validation["error_message"] = f"Unsupported image format: {file_ext}"
            return validation
        
        file_size = os.path.getsize(image_path)
        validation["file_size"] = file_size
        
        # Check if file is not empty
        if file_size == 0:
            validation["error_message"] = "Image file is empty"
            return validation
        
        # Check if file is not too large (50MB limit)
        if file_size > 50 * 1024 * 1024:
            validation["error_message"] = "Image file is too large (max 50MB)"
            return validation
        
        # Get image dimensions
        try:
            with Image.open(image_path) as img:
                validation["dimensions"] = (img.width, img.height)
        except Exception as e:
            validation["error_message"] = f"Invalid image file: {str(e)}"
            return validation
        
        validation["is_valid"] = True
        
    except Exception as e:
        validation["error_message"] = f"Error validating image: {str(e)}"
    
    return validation 