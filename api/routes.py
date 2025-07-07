"""
API Routes for Educational Content Processing
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional
import json
import asyncio
import tempfile
import shutil
import os
from services.content_service import ContentProcessingService
from models.schemas import create_success_response, create_failure_response

router = APIRouter()
service = ContentProcessingService()

async def stream_progress_updates(content_path: str, standard: str, subject: str, chapter: str, content_type: str, temp_paths: List[str] = None):
    """Stream progress updates during processing"""
    try:
        # Step 1: Processing text
        yield f"data: {json.dumps({'step': 1, 'status': 'processing', 'message': 'Processing text...', 'progress': 10})}\n\n"
        await asyncio.sleep(0.1)
        
        # Step 2: Checking grade level validation
        yield f"data: {json.dumps({'step': 2, 'status': 'validating', 'message': 'Checking grade level validation...', 'progress': 20})}\n\n"
        await asyncio.sleep(0.1)
        
        # Step 3: Checking profanity
        yield f"data: {json.dumps({'step': 3, 'status': 'validating', 'message': 'Checking profanity...', 'progress': 30})}\n\n"
        await asyncio.sleep(0.1)
        
        # Step 4: Checking relevance
        yield f"data: {json.dumps({'step': 4, 'status': 'validating', 'message': 'Checking relevance...', 'progress': 40})}\n\n"
        await asyncio.sleep(0.1)
        
        # Run the actual processing
        if content_type == "text":
            # For text content, use process_from_messages
            messages = [
                {
                    "role": "system",
                    "content": f"You are an educational content processor specializing in {subject} for {standard} students, focusing on {chapter}."
                },
                {
                    "role": "user", 
                    "content": f"Educational content to process: {content_path}"
                }
            ]
            result = service.process_from_messages(messages)
        else:
            # For files, use process_content
            result = service.process_content(
                standard=standard,
                subject=subject,
                chapter=chapter,
                pdf_path=content_path if content_type == "pdf" else None,
                image_paths=temp_paths if content_type == "images" else None
            )
        
        # Check for validation failures
        if not result.get('success'):
            error_message = result.get('error') or result.get('message') or 'Processing failed'
            yield f"data: {json.dumps({'step': 5, 'status': 'failed', 'message': error_message, 'progress': 100, 'error': True})}\n\n"
            return
        
        # Get the generated content
        generated_content = result.get('content', {})
        
        # Step 5: Generating notes
        notes_content = generated_content.get('importantNotes', 'Not generated')
        yield f"data: {json.dumps({'step': 5, 'status': 'generating', 'message': 'Generating notes...', 'progress': 50, 'content': notes_content})}\n\n"
        await asyncio.sleep(0.1)
        
        # Step 6: Generating fillups
        fillups_content = generated_content.get('fillInTheBlanks', {})
        yield f"data: {json.dumps({'step': 6, 'status': 'generating', 'message': 'Generating fillups...', 'progress': 60, 'content': fillups_content})}\n\n"
        await asyncio.sleep(0.1)
        
        # Step 7: Generating matching
        matching_content = generated_content.get('matchTheFollowing', {})
        yield f"data: {json.dumps({'step': 7, 'status': 'generating', 'message': 'Generating matching...', 'progress': 70, 'content': matching_content})}\n\n"
        await asyncio.sleep(0.1)
        
        # Step 8: Generating question answers
        qna_content = generated_content.get('questionAnswer', {})
        yield f"data: {json.dumps({'step': 8, 'status': 'generating', 'message': 'Generating question answers...', 'progress': 80, 'content': qna_content})}\n\n"
        await asyncio.sleep(0.1)
        
        # Send final content with completion
        final_response = {
            'step': 9,
            'status': 'completed',
            'message': 'Educational content processed successfully!',
            'progress': 100,
            'success': True,
            'content': result.get('content', {}),
            'metadata': {
                'standard': standard,
                'subject': subject,
                'chapter': chapter,
                'content_type': content_type,
                'validation_details': result.get('metadata', {}).get('validation_details', {})
            }
        }
        yield f"data: {json.dumps(final_response)}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'step': -1, 'status': 'error', 'message': f'Processing error: {str(e)}', 'progress': 100, 'error': True})}\n\n"
    finally:
        # Clean up temporary files after processing is complete
        if temp_paths:
            for path in temp_paths:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except Exception as cleanup_error:
                    print(f"Failed to cleanup temp file {path}: {cleanup_error}")

@router.post("/process-stream")
async def process_educational_content_stream(request: Request):
    """Stream processing with real-time progress updates"""
    try:
        form_data = await request.form()
        
        # Extract form data
        standard = form_data.get("standard")
        subject = form_data.get("subject")
        chapter = form_data.get("chapter")
        content_type = form_data.get("content_type", "pdf")
        text_content = form_data.get("text_content")
        files = form_data.getlist("files")
        
        # Input validation
        if not all([standard, subject, chapter]):
            raise HTTPException(400, "Missing required parameters: standard, subject, chapter")
        
        if content_type == "text":
            if not text_content:
                raise HTTPException(400, "Text content required for text processing")
        elif content_type in ["pdf", "images"]:
            if not files:
                raise HTTPException(400, "Files required for PDF/image processing")
        else:
            raise HTTPException(400, "Invalid content_type")
        
        # Prepare content for processing
        content_path = None
        temp_paths = []
        
        if content_type == "text":
            content_path = text_content
        elif content_type == "pdf":
            if len(files) != 1 or not files[0].filename.lower().endswith('.pdf'):
                raise HTTPException(400, "Exactly one PDF file required")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                shutil.copyfileobj(files[0].file, temp_file)
                content_path = temp_file.name
                temp_paths.append(content_path)
                
        elif content_type == "images":
            allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
            
            for file in files:
                ext = os.path.splitext(file.filename.lower())[1]
                if ext not in allowed_extensions:
                    raise HTTPException(400, f"Unsupported image format: {file.filename}")
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                    shutil.copyfileobj(file.file, temp_file)
                    temp_paths.append(temp_file.name)
            
            content_path = temp_paths[0] if temp_paths else None
        else:
            raise HTTPException(400, "Invalid content_type")
        
        # Return streaming response
        return StreamingResponse(
            stream_progress_updates(content_path, standard, subject, chapter, content_type, temp_paths),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
                    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Internal processing error: {str(e)}")

@router.post("/process-json")
async def process_educational_content_json(request: Request):
    """Process educational content and return complete JSON response"""
    try:
        form_data = await request.form()
        
        # Extract form data
        standard = form_data.get("standard")
        subject = form_data.get("subject")
        chapter = form_data.get("chapter")
        content_type = form_data.get("content_type", "pdf")
        text_content = form_data.get("text_content")
        files = form_data.getlist("files")
        
        # Input validation
        if not all([standard, subject, chapter]):
            raise HTTPException(400, "Missing required parameters: standard, subject, chapter")
        
        if content_type == "text":
            if not text_content:
                raise HTTPException(400, "Text content required for text processing")
        elif content_type in ["pdf", "images"]:
            if not files:
                raise HTTPException(400, "Files required for PDF/image processing")
        else:
            raise HTTPException(400, "Invalid content_type")
        
        # Prepare content for processing
        content_path = None
        temp_paths = []
        
        try:
            # Handle different content types
            if content_type == "text":
                content_path = text_content
            elif content_type == "pdf":
                if len(files) != 1 or not files[0].filename.lower().endswith('.pdf'):
                    raise HTTPException(400, "Exactly one PDF file required")
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    shutil.copyfileobj(files[0].file, temp_file)
                    content_path = temp_file.name
                    temp_paths.append(content_path)
                    
            elif content_type == "images":
                allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
                
                for file in files:
                    ext = os.path.splitext(file.filename.lower())[1]
                    if ext not in allowed_extensions:
                        raise HTTPException(400, f"Unsupported image format: {file.filename}")
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                        shutil.copyfileobj(file.file, temp_file)
                        temp_paths.append(temp_file.name)
                
                content_path = temp_paths[0] if temp_paths else None
            else:
                raise HTTPException(400, "Invalid content_type")

            # Process the content
            if content_type == "text":
                # For text content, use process_from_messages
                messages = [
                    {
                        "role": "system",
                        "content": f"You are an educational content processor specializing in {subject} for {standard} students, focusing on {chapter}."
                    },
                    {
                        "role": "user", 
                        "content": f"Educational content to process: {content_path}"
                    }
                ]
                result = service.process_from_messages(messages)
            else:
                # For files, use process_content
                result = service.process_content(
                    standard=standard,
                    subject=subject,
                    chapter=chapter,
                    pdf_path=content_path if content_type == "pdf" else None,
                    image_paths=temp_paths if content_type == "images" else None
                )
            
            # Check for processing errors
            if not result.get('success'):
                metadata = {
                    "standard": standard,
                    "subject": subject,
                    "chapter": chapter,
                    "content_type": content_type,
                    "files_processed": len(files) if files else 0
                }
                # Get the actual error message from the result
                error_message = result.get('error') or result.get('message') or 'Processing failed'
                # Get validation details if available
                validation_details = result.get('metadata', {}).get('validation_details')
                return create_failure_response(error_message, metadata, validation_details)
            
            # Success response
            metadata = {
                "standard": standard,
                "subject": subject,
                "chapter": chapter,
                "content_type": content_type,
                "files_processed": len(files) if files else 0,
                "validation_details": result.get('metadata', {}).get('validation_details', {})
            }
            return create_success_response(result.get('content', {}), metadata)
            
        finally:
            # Clean up temporary files
            for path in temp_paths:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except Exception as cleanup_error:
                    print(f"Failed to cleanup temp file {path}: {cleanup_error}")
                    
    except HTTPException:
        raise
    except Exception as e:
        metadata = {
            "standard": standard,
            "subject": subject,
            "chapter": chapter,
            "content_type": content_type,
            "files_processed": len(files) if files else 0
        }
        return create_failure_response(str(e), metadata, None) 