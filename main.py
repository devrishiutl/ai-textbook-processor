from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import tempfile
import shutil
from typing import List, Optional
from pydantic import BaseModel
from tools import (
    process_educational_content_tool,
    format_educational_output_tool
)

# Create FastAPI app
app = FastAPI(
    title="🎓 AI Textbook Processor",
    description="Advanced Educational Content Processing with Docling Document Intelligence",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class ProcessRequest(BaseModel):
    standard: str
    subject: str
    chapter: str
    content_type: str = "pdf"  # pdf, images, text

class ProcessResponse(BaseModel):
    success: bool
    message: str
    content: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[dict] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    service: str

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        service="AI Textbook Processor"
    )

# Main processing endpoint
@app.post("/process", response_model=ProcessResponse)
async def process_educational_content(
    standard: str = Form(..., description="Student standard/grade (e.g., 'Class 10', '5th Grade')"),
    subject: str = Form(..., description="Subject name (e.g., 'Science', 'Mathematics', 'Biology')"),
    chapter: str = Form(..., description="Chapter/topic name (e.g., 'Plant Kingdom', 'Algebra')"),
    content_type: str = Form("pdf", description="Type of content input (pdf, images, text)"),
    files: Optional[List[UploadFile]] = File(None, description="PDF or image files"),
    text_content: Optional[str] = Form(None, description="Direct text input (if content_type is 'text')")
):
    """
    Process educational content from PDF, images, or text
    
    - **standard**: Grade level (e.g., "Class 6", "Grade 8")
    - **subject**: Subject name (e.g., "Science", "Mathematics")
    - **chapter**: Chapter or topic name
    - **content_type**: Type of input ("pdf", "images", "text")
    - **files**: Upload PDF or image files
    - **text_content**: Direct text input (alternative to files)
    """
    
    try:
        print(f"🚀 Processing request: {subject} | {standard} | {chapter} | {content_type}")
        
        # Validate input
        if content_type in ["pdf", "images"] and not files:
            raise HTTPException(
                status_code=400, 
                detail="Files are required for PDF and image processing"
            )
        
        if content_type == "text" and not text_content:
            raise HTTPException(
                status_code=400, 
                detail="Text content is required for text processing"
            )
        
        # Process based on content type
        if content_type == "text":
            # Direct text processing
            result = process_educational_content_tool(
                content_source=text_content,
                standard=standard,
                subject=subject,
                chapter=chapter,
                content_type="text"
            )
            
        elif content_type == "pdf":
            # Handle PDF upload
            if len(files) != 1:
                raise HTTPException(
                    status_code=400,
                    detail="Exactly one PDF file is required"
                )
            
            file = files[0]
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail="File must be a PDF"
                )
            
            # Save uploaded PDF to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                shutil.copyfileobj(file.file, temp_file)
                temp_path = temp_file.name
            
            try:
                result = process_educational_content_tool(
                    content_source=temp_path,
                    standard=standard,
                    subject=subject,
                    chapter=chapter,
                    content_type="pdf"
                )
            finally:
                # Cleanup temporary file
                os.unlink(temp_path)
                
        elif content_type == "images":
            # Handle image uploads
            if not files:
                raise HTTPException(
                    status_code=400,
                    detail="At least one image file is required"
                )
            
            # Validate image files
            allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
            temp_paths = []
            
            try:
                for file in files:
                    file_ext = os.path.splitext(file.filename.lower())[1]
                    if file_ext not in allowed_extensions:
                        raise HTTPException(
                            status_code=400,
                            detail=f"File {file.filename} is not a supported image format"
                        )
                    
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                        shutil.copyfileobj(file.file, temp_file)
                        temp_paths.append(temp_file.name)
                
                result = process_educational_content_tool(
                    content_source=temp_paths,
                    standard=standard,
                    subject=subject,
                    chapter=chapter,
                    content_type="images"
                )
            finally:
                # Cleanup temporary files
                for temp_path in temp_paths:
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid content_type. Must be 'pdf', 'images', or 'text'"
            )
        
        # Check for processing errors
        if result and result.get('error'):
            return ProcessResponse(
                success=False,
                message="Processing failed",
                error=result.get('error'),
                metadata={
                    "standard": standard,
                    "subject": subject,
                    "chapter": chapter,
                    "content_type": content_type
                }
            )
        
        # Format the output
        formatted_output = format_educational_output_tool(result)
        
        return ProcessResponse(
            success=True,
            message="Educational content processed successfully",
            content=formatted_output,
            metadata={
                "standard": standard,
                "subject": subject,
                "chapter": chapter,
                "content_type": content_type,
                "files_processed": len(files) if files else 0
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error processing content: {str(e)}")
        return ProcessResponse(
            success=False,
            message="Internal processing error",
            error=str(e),
            metadata={
                "standard": standard,
                "subject": subject,
                "chapter": chapter,
                "content_type": content_type
            }
        )

# Text-only processing endpoint (simplified)
@app.post("/process-text", response_model=ProcessResponse)
async def process_text_content(request: ProcessRequest, text_content: str = Form(...)):
    """
    Simplified endpoint for text-only processing
    """
    try:
        result = process_educational_content_tool(
            content_source=text_content,
            standard=request.standard,
            subject=request.subject,
            chapter=request.chapter,
            content_type="text"
        )
        
        if result and result.get('error'):
            return ProcessResponse(
                success=False,
                message="Processing failed",
                error=result.get('error')
            )
        
        formatted_output = format_educational_output_tool(result)
        
        return ProcessResponse(
            success=True,
            message="Text content processed successfully",
            content=formatted_output
        )
        
    except Exception as e:
        return ProcessResponse(
            success=False,
            message="Processing error",
            error=str(e)
        )

# Get supported file types
@app.get("/supported-types")
async def get_supported_types():
    """Get supported content types and file formats"""
    return {
        "content_types": ["pdf", "images", "text"],
        "supported_image_formats": [".png", ".jpg", ".jpeg", ".gif", ".bmp"],
        "supported_document_formats": [".pdf"],
        "max_file_size": "50MB",
        "max_images": 10
    }

# Example usage endpoint
@app.get("/examples")
async def get_examples():
    """Get example requests for testing"""
    return {
        "pdf_example": {
            "standard": "Class 6",
            "subject": "Science",
            "chapter": "The Wonderful World of Science",
            "content_type": "pdf",
            "description": "Upload a PDF file with the above parameters"
        },
        "images_example": {
            "standard": "Grade 8",
            "subject": "Mathematics",
            "chapter": "Algebra",
            "content_type": "images",
            "description": "Upload multiple image files with the above parameters"
        },
        "text_example": {
            "standard": "Class 10",
            "subject": "Biology",
            "chapter": "Cell Structure",
            "content_type": "text",
            "text_content": "Cells are the basic unit of life...",
            "description": "Send text content with the above parameters"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting AI Textbook Processor API...")
    print("📚 Educational Content Processing with Advanced AI")
    print("🌐 API Documentation: http://localhost:8000/docs")
    print("🔧 ReDoc Documentation: http://localhost:8000/redoc")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 