#!/usr/bin/env python3
"""
AI Textbook Processor API
Provides both streaming and JSON endpoints for processing educational content.
"""

import warnings
import os
import logging
import json
import asyncio
from typing import AsyncGenerator, List, Optional

# Suppress warnings and configure minimal logging
warnings.filterwarnings("ignore")
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

logging.basicConfig(level=logging.ERROR, handlers=[logging.FileHandler('errors.log')], force=True)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import tempfile
import shutil

from tools import process_educational_content_tool, format_educational_output_tool
from models import ProcessResponse
from parsers import parse_educational_content

# Initialize FastAPI app
app = FastAPI(
    title="AI Textbook Processor",
    version="1.0.0",
    description="Processes educational content with both streaming and JSON endpoints"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

async def stream_progress_updates(
    content_path: str,
    standard: str,
    subject: str,
    chapter: str,
    content_type: str,
    temp_paths: List[str] = None
) -> AsyncGenerator[str, None]:
    """Stream progress updates during processing"""
    
    try:
        # Step 1: Starting
        yield f"data: {json.dumps({'step': 1, 'status': 'starting', 'message': 'Initializing AI Textbook Processor...', 'progress': 5})}\n\n"
        await asyncio.sleep(0.5)
        
        # Step 2: Content extraction
        yield f"data: {json.dumps({'step': 2, 'status': 'extracting', 'message': f'Extracting content from {content_type}...', 'progress': 15})}\n\n"
        await asyncio.sleep(1)
        
        # Step 3: Validation starting
        yield f"data: {json.dumps({'step': 3, 'status': 'validating', 'message': 'Starting comprehensive validation...', 'progress': 25})}\n\n"
        await asyncio.sleep(1)
        
        # Step 4: Grade validation
        yield f"data: {json.dumps({'step': 4, 'status': 'validating', 'message': 'Checking grade level appropriateness...', 'progress': 35})}\n\n"
        await asyncio.sleep(2)
        
        # Step 5: Safety validation
        yield f"data: {json.dumps({'step': 5, 'status': 'validating', 'message': 'Performing safety analysis...', 'progress': 45})}\n\n"
        await asyncio.sleep(2)
        
        # Step 6: Relevance validation
        yield f"data: {json.dumps({'step': 6, 'status': 'validating', 'message': 'Checking content relevance...', 'progress': 55})}\n\n"
        await asyncio.sleep(2)
        
        # Step 7: Processing (this is where the actual work happens)
        yield f"data: {json.dumps({'step': 7, 'status': 'processing', 'message': 'Processing with LangGraph workflow...', 'progress': 65})}\n\n"
        
        # Run the actual processing
        result = process_educational_content_tool(content_path, standard, subject, chapter, content_type)
        
        # Check for validation failures
        if result and (result.get('error') or result.get('processing_status') == 'FAILED'):
            validation_results = result.get('validation_results', {})
            error_message = f"Validation failed: {validation_results.get('reason', 'Unknown error')}"
            yield f"data: {json.dumps({'step': 8, 'status': 'failed', 'message': error_message, 'progress': 100, 'error': True})}\n\n"
            return
        
        # Step 8: Content generation
        yield f"data: {json.dumps({'step': 8, 'status': 'generating', 'message': 'Generating educational content...', 'progress': 75})}\n\n"
        await asyncio.sleep(1)
        
        # Step 9: Formatting
        yield f"data: {json.dumps({'step': 9, 'status': 'formatting', 'message': 'Formatting output...', 'progress': 85})}\n\n"
        
        # Format the output
        raw_output = format_educational_output_tool(result)
        structured_content = parse_educational_content(raw_output)
        
        # Step 10: Finalizing
        yield f"data: {json.dumps({'step': 10, 'status': 'finalizing', 'message': 'Finalizing results...', 'progress': 95})}\n\n"
        await asyncio.sleep(0.5)
        
        # Check if content is empty
        if not any([
            structured_content.importantNotes,
            structured_content.fillInTheBlanks.questions,
            structured_content.matchTheFollowing.column_a,
            structured_content.questionAnswer.questions
        ]):
            yield f"data: {json.dumps({'step': 11, 'status': 'failed', 'message': 'No educational content generated', 'progress': 100, 'error': True})}\n\n"
            return
        
        # Success! Split into smaller chunks to avoid buffer limits
        validation_results = result.get('validation_results', {})
        
        # First send completion status
        completion_response = {
            'step': 11,
            'status': 'completed',
            'message': 'Educational content processed successfully!',
            'progress': 100,
            'success': True
        }
        yield f"data: {json.dumps(completion_response)}\n\n"
        await asyncio.sleep(0.1)
        
        # Send metadata in parts
        # Part 1: Basic metadata
        basic_metadata_response = {
            'step': 12,
            'status': 'metadata',
            'message': 'Sending basic metadata...',
            'progress': 100,
            'metadata': {
                'standard': standard,
                'subject': subject,
                'chapter': chapter,
                'content_type': content_type
            },
            'part': 1,
            'total_parts': 2
        }
        yield f"data: {json.dumps(basic_metadata_response)}\n\n"
        await asyncio.sleep(0.1)
        
        # Part 2: Validation details
        validation_metadata_response = {
            'step': 12,
            'status': 'metadata',
            'message': 'Sending validation details...',
            'progress': 100,
            'metadata': {
                'validation_details': {
                    'status': 'passed',
                    'gradeValidation': validation_results.get('grade_check', 'PASS'),
                    'safetyAnalysis': validation_results.get('safety_check', 'PASS'),
                    'relevanceCheck': validation_results.get('relevance_check', 'PASS')
                }
            },
            'part': 2,
            'total_parts': 2
        }
        yield f"data: {json.dumps(validation_metadata_response)}\n\n"
        await asyncio.sleep(0.1)
        
        # Send content in sections to avoid size limits
        content_dict = structured_content.dict()
        
        # Send important notes in chunks if they're long
        if content_dict.get('importantNotes'):
            notes = content_dict['importantNotes']
            # Split notes into chunks of roughly 500 characters each
            chunk_size = 500
            notes_chunks = [notes[i:i + chunk_size] for i in range(0, len(notes), chunk_size)]
            total_chunks = len(notes_chunks)
            
            for idx, chunk in enumerate(notes_chunks, 1):
                notes_response = {
                    'step': 13,
                    'status': 'content_notes',
                    'message': f'Sending important notes (part {idx} of {total_chunks})...',
                    'progress': 100,
                    'content_type': 'importantNotes',
                    'data': chunk,
                    'part': idx,
                    'total_parts': total_chunks
                }
                yield f"data: {json.dumps(notes_response)}\n\n"
                await asyncio.sleep(0.1)
        
        # Send fill in the blanks in parts
        if content_dict.get('fillInTheBlanks'):
            blanks = content_dict['fillInTheBlanks']
            # Send questions
            blanks_q_response = {
                'step': 14,
                'status': 'content_blanks',
                'message': 'Sending fill in the blanks questions...',
                'progress': 100,
                'content_type': 'fillInTheBlanks',
                'data': {'questions': blanks['questions']},
                'part': 1,
                'total_parts': 2
            }
            yield f"data: {json.dumps(blanks_q_response)}\n\n"
            await asyncio.sleep(0.1)
            
            # Send answers
            blanks_a_response = {
                'step': 14,
                'status': 'content_blanks',
                'message': 'Sending fill in the blanks answers...',
                'progress': 100,
                'content_type': 'fillInTheBlanks',
                'data': {'answers': blanks['answers']},
                'part': 2,
                'total_parts': 2
            }
            yield f"data: {json.dumps(blanks_a_response)}\n\n"
            await asyncio.sleep(0.1)
        
        # Send match the following in parts
        if content_dict.get('matchTheFollowing'):
            match = content_dict['matchTheFollowing']
            # Send column A
            match_a_response = {
                'step': 15,
                'status': 'content_match',
                'message': 'Sending match the following column A...',
                'progress': 100,
                'content_type': 'matchTheFollowing',
                'data': {'column_a': match['column_a']},
                'part': 1,
                'total_parts': 3
            }
            yield f"data: {json.dumps(match_a_response)}\n\n"
            await asyncio.sleep(0.1)
            
            # Send column B
            match_b_response = {
                'step': 15,
                'status': 'content_match',
                'message': 'Sending match the following column B...',
                'progress': 100,
                'content_type': 'matchTheFollowing',
                'data': {'column_b': match['column_b']},
                'part': 2,
                'total_parts': 3
            }
            yield f"data: {json.dumps(match_b_response)}\n\n"
            await asyncio.sleep(0.1)
            
            # Send answers
            match_ans_response = {
                'step': 15,
                'status': 'content_match',
                'message': 'Sending match the following answers...',
                'progress': 100,
                'content_type': 'matchTheFollowing',
                'data': {'answers': match['answers']},
                'part': 3,
                'total_parts': 3
            }
            yield f"data: {json.dumps(match_ans_response)}\n\n"
            await asyncio.sleep(0.1)
        
        # Send question answers in parts
        if content_dict.get('questionAnswer'):
            qa = content_dict['questionAnswer']
            # Send questions
            qa_q_response = {
                'step': 16,
                'status': 'content_qa',
                'message': 'Sending questions...',
                'progress': 100,
                'content_type': 'questionAnswer',
                'data': {'questions': qa['questions']},
                'part': 1,
                'total_parts': 2
            }
            yield f"data: {json.dumps(qa_q_response)}\n\n"
            await asyncio.sleep(0.1)
            
            # Send answers
            qa_a_response = {
                'step': 16,
                'status': 'content_qa',
                'message': 'Sending answers...',
                'progress': 100,
                'content_type': 'questionAnswer',
                'data': {'answers': qa['answers']},
                'part': 2,
                'total_parts': 2
            }
            yield f"data: {json.dumps(qa_a_response)}\n\n"
            await asyncio.sleep(0.1)
        
        # Final completion message
        final_response = {
            'step': 17,
            'status': 'final',
            'message': 'All content delivered successfully!',
            'progress': 100,
            'complete': True
        }
        yield f"data: {json.dumps(final_response)}\n\n"
        
    except Exception as e:
        logger.error(f"Streaming error: {str(e)}")
        yield f"data: {json.dumps({'step': -1, 'status': 'error', 'message': f'Processing error: {str(e)}', 'progress': 100, 'error': True})}\n\n"
    finally:
        # Clean up temporary files after processing is complete
        if temp_paths:
            for path in temp_paths:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup temp file {path}: {cleanup_error}")
                    pass

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Textbook Processor"
    }

@app.post("/process-stream")
async def process_educational_content_stream(
    standard: str = Form(...),
    subject: str = Form(...),
    chapter: str = Form(...),
    content_type: str = Form("pdf"),
    files: Optional[List[UploadFile]] = File(None),
    text_content: Optional[str] = Form(None)
):
    """Stream processing with real-time progress updates"""
    
    try:
        # Input validation
        if content_type in ["pdf", "images"] and not files:
            raise HTTPException(400, "Files required for PDF/image processing")
        if content_type == "text" and not text_content:
            raise HTTPException(400, "Text content required")
        
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
            
            content_path = temp_paths
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
        logger.error(f"Stream setup error: {str(e)}")
        raise HTTPException(500, f"Internal processing error: {str(e)}")

@app.post("/process-json")
async def process_educational_content_json(
    standard: str = Form(...),
    subject: str = Form(...),
    chapter: str = Form(...),
    content_type: str = Form("pdf"),
    files: Optional[List[UploadFile]] = File(None),
    text_content: Optional[str] = Form(None)
):
    """Process educational content and return complete JSON response"""
    try:
        # Input validation
        if content_type in ["pdf", "images"] and not files:
            raise HTTPException(400, "Files required for PDF/image processing")
        if content_type == "text" and not text_content:
            raise HTTPException(400, "Text content required")
        
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
                
                content_path = temp_paths
            else:
                raise HTTPException(400, "Invalid content_type")

            # Process the content
            result = process_educational_content_tool(content_path, standard, subject, chapter, content_type)
            
            # Check for processing errors
            if result and (result.get('error') or result.get('processing_status') == 'FAILED'):
                validation_results = result.get('validation_results', {})
                return {
                    "success": False,
                    "message": "Processing failed",
                    "error": f"Validation failed: {validation_results.get('reason', 'Unknown error')}",
                    "metadata": {
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
                }
            
            # Format and parse the output
            raw_output = format_educational_output_tool(result)
            structured_content = parse_educational_content(raw_output)
            
            # Check if content is empty
            if not any([
                structured_content.importantNotes,
                structured_content.fillInTheBlanks.questions,
                structured_content.matchTheFollowing.column_a,
                structured_content.questionAnswer.questions
            ]):
                return {
                    "success": False,
                    "message": "Content validation failed",
                    "error": "No educational content generated",
                    "metadata": {
                        "standard": standard,
                        "subject": subject,
                        "chapter": chapter,
                        "content_type": content_type
                    }
                }
            
            # Success response
            validation_results = result.get('validation_results', {})
            return {
                "success": True,
                "message": "Educational content processed successfully",
                "content": structured_content.dict(),
                "metadata": {
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
            }
            
        finally:
            # Clean up temporary files
            for path in temp_paths:
                try:
                    if os.path.exists(path):
                        os.unlink(path)
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup temp file {path}: {cleanup_error}")
                    pass
                    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            "success": False,
            "message": "Internal processing error",
            "error": str(e),
            "metadata": {
                "standard": standard,
                "subject": subject,
                "chapter": chapter,
                "content_type": content_type
            }
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False) 