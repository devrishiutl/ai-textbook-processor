"""
Simple API Routes
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from typing import List, Optional
import tempfile
import os
from agents.graph import graph
from agents.helper import extract_content_from_files, create_initial_state, format_response

app = FastAPI()

@app.post("/process")
async def process_content(
    standard: str = Form(...),
    subject: str = Form(...),
    chapter: str = Form(...),
    content_type: str = Form(...),
    pdf_file: Optional[UploadFile] = File(None),
    files: List[UploadFile] = File([]),
    text_content: Optional[str] = Form(None)
):
    try:
        if content_type == "text":
            if not text_content:
                raise HTTPException(400, "text_content required")
            content = text_content
        elif content_type == "pdf":
            # Handle PDF file from either pdf_file parameter or files parameter
            pdf_upload = None
            
            if pdf_file:
                # PDF file provided through pdf_file parameter
                pdf_upload = pdf_file
                if files:
                    raise HTTPException(400, "Only one PDF file is allowed when content_type is 'pdf'. Use either pdf_file or files parameter, not both.")
            elif files and len(files) == 1:
                # PDF file provided through files parameter
                pdf_upload = files[0]
            elif files and len(files) > 1:
                raise HTTPException(400, "Only one PDF file is allowed when content_type is 'pdf'")
            else:
                raise HTTPException(400, "pdf_file required when content_type is 'pdf'")
            
            # Validate file type
            if not pdf_upload.filename.lower().endswith('.pdf'):
                raise HTTPException(400, "Only PDF files are allowed when content_type is 'pdf'")
                
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
                f.write(await pdf_upload.read())
                content = extract_content_from_files(f.name, None)
                os.unlink(f.name)
                
                # Check if content extraction failed
                if content.startswith("ERROR"):
                    raise HTTPException(400, f"PDF processing failed: {content}")
                
                # Check if content is meaningful
                if len(content.strip()) < 100:
                    raise HTTPException(400, "PDF appears to contain insufficient text content. Please ensure the PDF contains actual educational text, not just images or metadata.")
        elif content_type == "images":
            if not files:
                raise HTTPException(400, "files required")
            image_paths = []
            for file in files:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
                    f.write(await file.read())
                    image_paths.append(f.name)
            content = extract_content_from_files(None, image_paths)
            for path in image_paths:
                os.unlink(path)
        else:
            raise HTTPException(400, "Invalid content_type")
        
        state = create_initial_state(standard, subject, chapter, content)
        result = graph.invoke(state)
        return format_response(result)
        
    except Exception as e:
        raise HTTPException(500, f"Processing error: {str(e)}") 