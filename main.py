import warnings
import os
import logging
from datetime import datetime

# Suppress PyTorch MPS warnings on Apple Silicon
warnings.filterwarnings("ignore", message=".*pin_memory.*not supported on MPS.*")
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

# Configure logging to file only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('textbook_processor.log', mode='a')
    ],
    force=True  # Force override any existing configuration
)

# Create logger for this module
logger = logging.getLogger(__name__)

# Test logging immediately
logger.info("🚀 Logging system initialized successfully")

# Suppress generic root logger errors from dependencies
logging.getLogger("root").setLevel(logging.CRITICAL)
for noisy_logger in ["torch", "transformers", "docling", "PIL"]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile
import shutil
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from tools import (
    process_educational_content_tool,
    format_educational_output_tool
)
from models import ProcessResponse, StructuredContent
from parsers import parse_educational_content

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 FastAPI application started - logging test successful")

# Models are now imported from models.py

# Main processing endpoint with structured output
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
    Process educational content and return structured JSON response
    """
    
    try:
        logger.info(f"🚀 Processing request: {subject} | {standard} | {chapter} | {content_type}")
        
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
            result = process_educational_content_tool(
                content_source=text_content,
                standard=standard,
                subject=subject,
                chapter=chapter,
                content_type="text"
            )
            
        elif content_type == "pdf":
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
                os.unlink(temp_path)
                
        elif content_type == "images":
            if not files:
                raise HTTPException(
                    status_code=400,
                    detail="At least one image file is required"
                )
            
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
        
        # Debug the result from LangGraph
        print(f"🔍 DEBUG: LangGraph result keys: {list(result.keys()) if result else 'None'}")
        print(f"🔍 DEBUG: Processing status: {result.get('processing_status') if result else 'None'}")
        print(f"🔍 DEBUG: Error details: {result.get('error_details') if result else 'None'}")
        
        # Check for processing errors and format consistently
        if result and (result.get('error') or result.get('processing_status') == 'FAILED'):
            # Extract validation results for structured error response
            validation_results = result.get('validation_results', {})
            
            # Create structured error response
            error_response = {
                "status": "failed",
                "gradeValidation": validation_results.get('grade_check', 'UNKNOWN'),
                "safetyAnalysis": validation_results.get('safety_check', 'UNKNOWN'),
                "relevanceCheck": validation_results.get('relevance_check', 'UNKNOWN'),
                "reason": validation_results.get('reason', result.get('error_details', 'Processing validation failed'))
            }
            
            print(f"🔍 DEBUG: Returning structured error: {error_response}")
            return ProcessResponse(
                success=False,
                message="Processing failed",
                error=f"Validation failed: {error_response['reason']}",
                metadata={
                    "standard": standard,
                    "subject": subject,
                    "chapter": chapter,
                    "content_type": content_type,
                    "validation_details": error_response
                }
            )
        
        # Format and parse the output into structured JSON
        raw_output = format_educational_output_tool(result)
        print(f"🔍 DEBUG: Raw output length: {len(raw_output)} characters")
        print(f"🔍 DEBUG: Raw output preview: {raw_output[:500]}...")
        
        structured_content = parse_educational_content(raw_output)
        
        # Debug structured content
        print(f"🔍 DEBUG: Structured content - Notes: {bool(structured_content.importantNotes)}")
        print(f"🔍 DEBUG: Structured content - Blanks: {bool(structured_content.fillInTheBlanks.questions)}")
        print(f"🔍 DEBUG: Structured content - Matches: {bool(structured_content.matchTheFollowing.column_a)}")
        print(f"🔍 DEBUG: Structured content - Q&A: {bool(structured_content.questionAnswer.questions)}")
        
        # Check if the structured content is empty (validation likely failed)
        is_content_empty = (
            not structured_content.importantNotes and
            not structured_content.fillInTheBlanks.questions and
            not structured_content.matchTheFollowing.column_a and
            not structured_content.questionAnswer.questions
        )
        
        print(f"🔍 DEBUG: Is content empty: {is_content_empty}")
        
        # Also log to logger (in case it starts working)
        logger.info(f"🔍 Raw output length: {len(raw_output)} characters")
        logger.info(f"🔍 Is content empty: {is_content_empty}")
        
        if is_content_empty:
            # Check if validation actually failed (look for FAIL, not just any validation text)
            validation_failures = []
            
            if structured_content.gradeValidation and "FAIL" in structured_content.gradeValidation:
                validation_failures.append(f"Grade Validation: {structured_content.gradeValidation}")
            if structured_content.safetyAnalysis and "FAIL" in structured_content.safetyAnalysis:
                validation_failures.append(f"Safety Analysis: {structured_content.safetyAnalysis}")
            if structured_content.relevanceCheck and "FAIL" in structured_content.relevanceCheck:
                validation_failures.append(f"Relevance Check: {structured_content.relevanceCheck}")
            
            if validation_failures:
                error_details = "; ".join(validation_failures)
            else:
                error_details = "Content validation failed - no educational content generated"
            
            return ProcessResponse(
                success=False,
                message="Content validation failed",
                error=error_details,
                metadata={
                    "standard": standard,
                    "subject": subject,
                    "chapter": chapter,
                    "content_type": content_type,
                    "files_processed": len(files) if files else 0
                }
            )
        
        # Create structured success response from LangGraph validation results
        validation_results = result.get('validation_results', {})
        success_response = {
            "status": "passed",
            "gradeValidation": validation_results.get('grade_check', 'PASS'),
            "safetyAnalysis": validation_results.get('safety_check', 'PASS'),
            "relevanceCheck": validation_results.get('relevance_check', 'PASS')
        }
        
        return ProcessResponse(
            success=True,
            message="Educational content processed successfully",
            content=structured_content,
            metadata={
                "standard": standard,
                "subject": subject,
                "chapter": chapter,
                "content_type": content_type,
                "files_processed": len(files) if files else 0,
                "validation_details": success_response
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing content: {str(e)}")
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

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting AI Textbook Processor API...")
    logger.info("📚 Educational Content Processing with Structured JSON Output")
    logger.info("🌐 API Documentation: http://localhost:8000/docs")
    logger.info("🔧 ReDoc Documentation: http://localhost:8000/redoc")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 