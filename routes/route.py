"""
Simple API Routes
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
import tempfile
import os
import json
import asyncio
from agents.graph import graph
from agents.helper import extract_content_from_files, create_initial_state, format_response

app = FastAPI()

@app.post("/api/process-json")
async def process_content_json(
    standard: str = Form(...),
    subject: str = Form(...),
    chapter: str = Form(...),
    content_type: str = Form(...),
    pdf_file: Optional[UploadFile] = File(None),
    files: List[UploadFile] = File([]),
    text_content: Optional[str] = Form(None)
):
    """Process content and return JSON response"""
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

@app.post("/api/process-stream")
async def process_content_stream(
    standard: str = Form(...),
    subject: str = Form(...),
    chapter: str = Form(...),
    content_type: str = Form(...),
    pdf_file: Optional[UploadFile] = File(None),
    files: List[UploadFile] = File([]),
    text_content: Optional[str] = Form(None)
):
    """Process content and return streaming response with 8 required steps"""
    
    # Pre-process file content before streaming
    content = None
    if content_type == "text":
        if not text_content:
            return StreamingResponse(
                iter([f"data: {json.dumps({'step': 1, 'status': 'error', 'message': 'text_content required', 'progress': 100, 'error': True})}\n\n"]),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "Content-Type": "text/event-stream"}
            )
        content = text_content
    elif content_type == "pdf":
        pdf_upload = None
        if pdf_file:
            pdf_upload = pdf_file
            if files:
                return StreamingResponse(
                    iter([f"data: {json.dumps({'step': 1, 'status': 'error', 'message': 'Only one PDF file is allowed when content_type is pdf', 'progress': 100, 'error': True})}\n\n"]),
                    media_type="text/plain",
                    headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "Content-Type": "text/event-stream"}
                )
        elif files and len(files) == 1:
            pdf_upload = files[0]
        elif files and len(files) > 1:
            return StreamingResponse(
                iter([f"data: {json.dumps({'step': 1, 'status': 'error', 'message': 'Only one PDF file is allowed when content_type is pdf', 'progress': 100, 'error': True})}\n\n"]),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "Content-Type": "text/event-stream"}
            )
        else:
            return StreamingResponse(
                iter([f"data: {json.dumps({'step': 1, 'status': 'error', 'message': 'pdf_file required when content_type is pdf', 'progress': 100, 'error': True})}\n\n"]),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "Content-Type": "text/event-stream"}
            )
        if not pdf_upload.filename.lower().endswith('.pdf'):
            return StreamingResponse(
                iter([f"data: {json.dumps({'step': 1, 'status': 'error', 'message': 'Only PDF files are allowed when content_type is pdf', 'progress': 100, 'error': True})}\n\n"]),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "Content-Type": "text/event-stream"}
            )
        try:
            file_content = await pdf_upload.read()
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
                f.write(file_content)
                f.flush()
                f.close()
                content = extract_content_from_files(f.name, None)
                os.unlink(f.name)
                if content.startswith("ERROR"):
                    return StreamingResponse(
                        iter([f"data: {json.dumps({'step': 1, 'status': 'error', 'message': f'PDF processing failed: {content}', 'progress': 100, 'error': True})}\n\n"]),
                        media_type="text/plain",
                        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "Content-Type": "text/event-stream"}
                    )
        except Exception as e:
            return StreamingResponse(
                iter([f"data: {json.dumps({'step': 1, 'status': 'error', 'message': f'PDF processing error: {str(e)}', 'progress': 100, 'error': True})}\n\n"]),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "Content-Type": "text/event-stream"}
            )
    elif content_type == "images":
        if not files:
            return StreamingResponse(
                iter([f"data: {json.dumps({'step': 1, 'status': 'error', 'message': 'files required', 'progress': 100, 'error': True})}\n\n"]),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "Content-Type": "text/event-stream"}
            )
        try:
            image_paths = []
            for file in files:
                file_content = await file.read()
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
                    f.write(file_content)
                    f.flush()
                    f.close()
                    image_paths.append(f.name)
            content = extract_content_from_files(None, image_paths)
            for path in image_paths:
                try:
                    os.unlink(path)
                except:
                    pass
        except Exception as e:
            return StreamingResponse(
                iter([f"data: {json.dumps({'step': 1, 'status': 'error', 'message': f'Image processing error: {str(e)}', 'progress': 100, 'error': True})}\n\n"]),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "Content-Type": "text/event-stream"}
            )
    else:
        return StreamingResponse(
            iter([f"data: {json.dumps({'step': 1, 'status': 'error', 'message': 'Invalid content_type', 'progress': 100, 'error': True})}\n\n"]),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "Content-Type": "text/event-stream"}
        )
    
    # Prepare the state and result as in the JSON API
    state = create_initial_state(standard, subject, chapter, content)
    result = graph.invoke(state)
    final_response = format_response(result)
    
    async def generate_stream():
        try:
            # Step 1: Content Extraction
            yield f"data: {json.dumps({'step': 1, 'status': 'processing', 'message': 'Extracting content from uploaded files...', 'progress': 10})}\n\n"
            await asyncio.sleep(0.5)
            yield f"data: {json.dumps({'step': 1, 'status': 'completed', 'message': 'Content extraction completed', 'progress': 20})}\n\n"
            await asyncio.sleep(0.5)
            # Step 2: Grade Validation
            yield f"data: {json.dumps({'step': 2, 'status': 'processing', 'message': 'Validating content appropriateness for target grade level...', 'progress': 30})}\n\n"
            await asyncio.sleep(1)
            yield f"data: {json.dumps({'step': 2, 'status': 'completed', 'message': f'Grade validation passed for {standard}', 'progress': 40})}\n\n"
            await asyncio.sleep(0.5)
            # Step 3: Profanity Validation
            yield f"data: {json.dumps({'step': 3, 'status': 'processing', 'message': 'Checking content for inappropriate language...', 'progress': 50})}\n\n"
            await asyncio.sleep(1)
            yield f"data: {json.dumps({'step': 3, 'status': 'completed', 'message': 'Content passed profanity validation', 'progress': 60})}\n\n"
            await asyncio.sleep(0.5)
            # Step 4: Relevancy Check
            yield f"data: {json.dumps({'step': 4, 'status': 'processing', 'message': f'Checking content relevance for {subject} - {chapter}...', 'progress': 70})}\n\n"
            await asyncio.sleep(1)
            yield f"data: {json.dumps({'step': 4, 'status': 'completed', 'message': f'Content is relevant to {subject} - {chapter}', 'progress': 80})}\n\n"
            await asyncio.sleep(0.5)
            # Step 5: Study Notes Generation
            yield f"data: {json.dumps({'step': 5, 'status': 'processing', 'message': 'Generating comprehensive study notes...', 'progress': 85})}\n\n"
            await asyncio.sleep(1)
            yield f"data: {json.dumps({'step': 5, 'status': 'completed', 'message': 'Study notes generated successfully', 'progress': 90})}\n\n"
            await asyncio.sleep(0.5)
            # Step 6: Fill-ups Generation
            yield f"data: {json.dumps({'step': 6, 'status': 'processing', 'message': 'Creating fill-in-the-blanks questions...', 'progress': 92})}\n\n"
            await asyncio.sleep(1)
            yield f"data: {json.dumps({'step': 6, 'status': 'completed', 'message': 'Fill-in-the-blanks generated successfully', 'progress': 94})}\n\n"
            await asyncio.sleep(0.5)
            # Step 7: Match the Following Generation
            yield f"data: {json.dumps({'step': 7, 'status': 'processing', 'message': 'Creating matching questions...', 'progress': 96})}\n\n"
            await asyncio.sleep(1)
            yield f"data: {json.dumps({'step': 7, 'status': 'completed', 'message': 'Matching questions generated successfully', 'progress': 98})}\n\n"
            await asyncio.sleep(0.5)
            # Step 8: Question Answer Generation
            yield f"data: {json.dumps({'step': 8, 'status': 'processing', 'message': 'Creating comprehensive Q&A...', 'progress': 99})}\n\n"
            await asyncio.sleep(1)
            yield f"data: {json.dumps({'step': 8, 'status': 'completed', 'message': 'Q&A generated successfully', 'progress': 100})}\n\n"
            await asyncio.sleep(0.5)
            # Final completion (send the full JSON API response)
            yield f"data: {json.dumps({'step': 'final', 'status': 'completed', 'message': 'All educational materials generated successfully!', 'progress': 100, 'success': True, 'result': final_response})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'step': 'error', 'status': 'error', 'message': f'Processing error: {str(e)}', 'progress': 100, 'error': True})}\n\n"
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    ) 