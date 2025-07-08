"""
Simple Utility Functions
"""
import os
import base64
import requests
from typing import List
from PIL import Image
import io
from config.configuration import get_generation_llm, azure_client, AZURE_DEPLOYMENT_NAME
from langsmith import traceable

def read_data_from_file(pdf_path: str) -> str:
    """Read PDF using Tika server"""
    try:
        # Read file content first
        with open(pdf_path, 'rb') as f:
            file_content = f.read()
        
        # Use PUT method to /tika endpoint for text extraction
        response = requests.put(
            'http://localhost:8004/tika', 
            data=file_content, 
            headers={
                'Content-Type': 'application/pdf',
                'Accept': 'text/plain'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            text = response.text
            # Check if we got meaningful content
            if len(text.strip()) < 100:
                return "ERROR: PDF extraction returned insufficient content. Please ensure the PDF contains actual educational text."
            return text[:50000] + "... [truncated]" if len(text) > 50000 else text
        else:
            return f"ERROR: Tika server returned status {response.status_code}. Response: {response.text}"
            
    except requests.exceptions.ConnectionError:
        return "ERROR: Cannot connect to Tika server. Please ensure Tika server is running on localhost:8004"
    except requests.exceptions.Timeout:
        return "ERROR: Tika server request timed out"
    except Exception as e:
        return f"ERROR: PDF extraction failed - {str(e)}"

def preprocess_image(image_path: str, target_size=(800, 800), quality=85) -> str:
    """
    Preprocess image before sending to LLM:
    1. Resize while maintaining aspect ratio
    2. Optimize quality
    3. Convert to base64
    
    Args:
        image_path: Path to image file
        target_size: Maximum dimensions (width, height)
        quality: JPEG quality (0-100)
    
    Returns:
        Base64 encoded optimized image or error message
    """
    try:
        # Open image with PIL
        img = Image.open(image_path)
        
        # Calculate aspect ratio preserving resize dimensions
        aspect_ratio = img.width / img.height
        if aspect_ratio > 1:
            # Width is larger
            new_width = min(img.width, target_size[0])
            new_height = int(new_width / aspect_ratio)
        else:
            # Height is larger
            new_height = min(img.height, target_size[1])
            new_width = int(new_height * aspect_ratio)
            
        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Save to bytes with quality optimization
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return encoded
    except Exception as e:
        return f"ERROR: Image preprocessing failed - {str(e)}"

@traceable(name="image_vision_processing")
def vision_understand_tool(images, standard, subject, chapter):
    """Process images with vision AI"""
    try:
        # Fixed prompt: Extract ACTUAL content from images, not generate based on subject/chapter
        user_content = [{"type": "text", "text": "Extract all educational content from these images. Describe exactly what you see - text, diagrams, concepts, topics, etc. Do not generate new content, only describe what is actually present in the images."}]
        
        for img_path in images:
            # Preprocess image before encoding
            encoded = preprocess_image(
                img_path,
                target_size=(800, 800),  # Max dimensions while maintaining aspect ratio
                quality=85  # Good balance between quality and size
            )
            
            if encoded.startswith("ERROR"):
                return encoded
            
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}
            })

        response = azure_client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are an educational content extractor. Extract and describe only the actual content present in the images."},
                {"role": "user", "content": user_content}
            ],
            temperature=0.1,
            max_tokens=3000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: {str(e)}"

def read_data_from_image(image_paths: List[str]) -> str:
    """Extract content from images using vision AI"""
    if not image_paths:
        return "No images provided"
    
    # Use vision AI to process images
    content = vision_understand_tool(image_paths, "", "", "")
    
    if content.startswith("ERROR"):
        return content
    
    return content 