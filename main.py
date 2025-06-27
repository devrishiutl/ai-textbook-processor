import warnings
import os
import logging
from datetime import datetime

# Suppress warnings and configure minimal logging
warnings.filterwarnings("ignore")
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

logging.basicConfig(level=logging.ERROR, handlers=[logging.FileHandler('errors.log')], force=True)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import shutil
import os
from typing import List, Optional
from tools import process_educational_content_tool, format_educational_output_tool
from models import ProcessResponse
from parsers import parse_educational_content

app = FastAPI(title="AI Textbook Processor", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/process", response_model=ProcessResponse)
async def process_educational_content(
    standard: str = Form(...),
    subject: str = Form(...),
    chapter: str = Form(...),
    content_type: str = Form("pdf"),
    files: Optional[List[UploadFile]] = File(None),
    text_content: Optional[str] = Form(None)
):
    try:
        # Input validation
        if content_type in ["pdf", "images"] and not files:
            raise HTTPException(400, "Files required for PDF/image processing")
        if content_type == "text" and not text_content:
            raise HTTPException(400, "Text content required")
        
        # Process content
        if content_type == "text":
            result = process_educational_content_tool(text_content, standard, subject, chapter, "text")
        elif content_type == "pdf":
            if len(files) != 1 or not files[0].filename.lower().endswith('.pdf'):
                raise HTTPException(400, "Exactly one PDF file required")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                shutil.copyfileobj(files[0].file, temp_file)
                temp_path = temp_file.name
            
            try:
                result = process_educational_content_tool(temp_path, standard, subject, chapter, "pdf")
            finally:
                os.unlink(temp_path)
                
        elif content_type == "images":
            allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
            temp_paths = []
            
            try:
                for file in files:
                    ext = os.path.splitext(file.filename.lower())[1]
                    if ext not in allowed_extensions:
                        raise HTTPException(400, f"Unsupported image format: {file.filename}")
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                        shutil.copyfileobj(file.file, temp_file)
                        temp_paths.append(temp_file.name)
                
                result = process_educational_content_tool(temp_paths, standard, subject, chapter, "images")
            finally:
                for path in temp_paths:
                    try: os.unlink(path)
                    except: pass
        else:
            raise HTTPException(400, "Invalid content_type")
        
        # Check for processing errors
        if result and (result.get('error') or result.get('processing_status') == 'FAILED'):
            validation_results = result.get('validation_results', {})
            return ProcessResponse(
                success=False,
                message="Processing failed",
                error=f"Validation failed: {validation_results.get('reason', 'Unknown error')}",
                metadata={
                    "standard": standard,
                    "subject": subject,
                    "chapter": chapter,
                    "content_type": content_type,
                    "validation_details": {
                        "status": "failed",
                        "gradeValidation": validation_results.get('grade_check', 'UNKNOWN'),
                        "safetyAnalysis": validation_results.get('safety_check', 'UNKNOWN'),
                        "relevanceCheck": validation_results.get('relevance_check', 'UNKNOWN'),
                        "reason": validation_results.get('reason', 'Processing failed')
                    }
                }
            )
        
        # Parse output
        raw_output = format_educational_output_tool(result)
        structured_content = parse_educational_content(raw_output)
        
        # Check if content is empty
        if not any([
            structured_content.importantNotes,
            structured_content.fillInTheBlanks.questions,
            structured_content.matchTheFollowing.column_a,
            structured_content.questionAnswer.questions
        ]):
            return ProcessResponse(
                success=False,
                message="Content validation failed",
                error="No educational content generated",
                metadata={"standard": standard, "subject": subject, "chapter": chapter, "content_type": content_type}
            )
        
        # Success response
        validation_results = result.get('validation_results', {})
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
                "validation_details": {
                    "status": "passed",
                    "gradeValidation": validation_results.get('grade_check', 'PASS'),
                    "safetyAnalysis": validation_results.get('safety_check', 'PASS'),
                    "relevanceCheck": validation_results.get('relevance_check', 'PASS')
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return ProcessResponse(
            success=False,
            message="Internal processing error",
            error=str(e),
            metadata={"standard": standard, "subject": subject, "chapter": chapter, "content_type": content_type}
                  )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False) 