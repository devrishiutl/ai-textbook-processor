#!/usr/bin/env python3
"""
Streaming version of AI Textbook Processor with real-time progress updates.
Provides better UX for long-running operations.
"""

import warnings
import os
import logging
import json
import asyncio
from typing import AsyncGenerator

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
from typing import List, Optional
from tools import process_educational_content_tool, format_educational_output_tool
from models import ProcessResponse
from parsers import parse_educational_content

app = FastAPI(title="AI Textbook Processor - Streaming", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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
        
        # Success!
        validation_results = result.get('validation_results', {})
        success_response = {
            'step': 11,
            'status': 'completed',
            'message': 'Educational content processed successfully!',
            'progress': 100,
            'success': True,
            'data': {
                'content': structured_content.dict(),
                'metadata': {
                    'standard': standard,
                    'subject': subject,
                    'chapter': chapter,
                    'content_type': content_type,
                    'validation_details': {
                        'status': 'passed',
                        'gradeValidation': validation_results.get('grade_check', 'PASS'),
                        'safetyAnalysis': validation_results.get('safety_check', 'PASS'),
                        'relevanceCheck': validation_results.get('relevance_check', 'PASS')
                    }
                }
            }
        }
        
        yield f"data: {json.dumps(success_response)}\n\n"
        
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

# Keep the original non-streaming endpoint for compatibility
@app.post("/process", response_model=ProcessResponse)
async def process_educational_content(
    standard: str = Form(...),
    subject: str = Form(...),
    chapter: str = Form(...),
    content_type: str = Form("pdf"),
    files: Optional[List[UploadFile]] = File(None),
    text_content: Optional[str] = Form(None)
):
    """Original non-streaming endpoint for compatibility"""
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

@app.get("/streaming-demo")
async def streaming_demo():
    """Demo page for testing streaming functionality"""
    
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>AI Textbook Processor - Streaming Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        .progress-container { margin: 20px 0; }
        .progress-bar { width: 100%; height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #4CAF50, #45a049); transition: width 0.3s ease; }
        .status { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .status.starting { background: #e3f2fd; border-left: 4px solid #2196f3; }
        .status.extracting { background: #fff3e0; border-left: 4px solid #ff9800; }
        .status.validating { background: #fce4ec; border-left: 4px solid #e91e63; }
        .status.processing { background: #f3e5f5; border-left: 4px solid #9c27b0; }
        .status.generating { background: #e8f5e8; border-left: 4px solid #4caf50; }
        .status.completed { background: #e8f5e8; border-left: 4px solid #4caf50; font-weight: bold; }
        .status.failed { background: #ffebee; border-left: 4px solid #f44336; }
        .form-group { margin: 15px 0; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .btn { background: #2196f3; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #1976d2; }
        .btn:disabled { background: #ccc; cursor: not-allowed; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Textbook Processor - Streaming Demo</h1>
        <p>Test the streaming functionality with real-time progress updates!</p>
        
        <form id="streamingForm">
            <div class="form-group">
                <label>Standard/Grade:</label>
                <input type="text" name="standard" value="Class 6" required>
            </div>
            <div class="form-group">
                <label>Subject:</label>
                <input type="text" name="subject" value="Science" required>
            </div>
            <div class="form-group">
                <label>Chapter:</label>
                <input type="text" name="chapter" value="Scientific Method" required>
            </div>
            <div class="form-group">
                <label>Content Type:</label>
                <select name="content_type">
                    <option value="text">Text</option>
                    <option value="pdf">PDF</option>
                    <option value="images">Images</option>
                </select>
            </div>
            <div class="form-group">
                <label>Text Content:</label>
                <textarea name="text_content" rows="4" placeholder="Enter educational content here...">The scientific method is a systematic approach to understanding the natural world through observation, hypothesis formation, experimentation, and analysis.</textarea>
            </div>
            <button type="submit" class="btn" id="submitBtn">Start Streaming Process</button>
        </form>
        
        <div class="progress-container" id="progressContainer" style="display: none;">
            <h3>Processing Progress:</h3>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill" style="width: 0%;"></div>
            </div>
            <div id="statusMessages"></div>
        </div>
        
        <div id="results" style="margin-top: 20px;"></div>
    </div>
    
    <script>
        document.getElementById('streamingForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitBtn = document.getElementById('submitBtn');
            const progressContainer = document.getElementById('progressContainer');
            const progressFill = document.getElementById('progressFill');
            const statusMessages = document.getElementById('statusMessages');
            const results = document.getElementById('results');
            
            // Reset UI
            submitBtn.disabled = true;
            submitBtn.textContent = 'Processing...';
            progressContainer.style.display = 'block';
            statusMessages.innerHTML = '';
            results.innerHTML = '';
            progressFill.style.width = '0%';
            
            try {
                const response = await fetch('/process-stream', {
                    method: 'POST',
                    body: formData
                });
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                
                                // Update progress bar
                                progressFill.style.width = data.progress + '%';
                                
                                // Add status message
                                const statusDiv = document.createElement('div');
                                statusDiv.className = 'status ' + data.status;
                                statusDiv.innerHTML = `<strong>Step ${data.step}:</strong> ${data.message}`;
                                statusMessages.appendChild(statusDiv);
                                
                                // Scroll to latest message
                                statusDiv.scrollIntoView({ behavior: 'smooth' });
                                
                                // Handle completion
                                if (data.success) {
                                    results.innerHTML = '<h3>✅ Success!</h3><pre>' + JSON.stringify(data.data, null, 2) + '</pre>';
                                } else if (data.error) {
                                    results.innerHTML = '<h3>❌ Error</h3><p>' + data.message + '</p>';
                                }
                                
                            } catch (parseError) {
                                console.error('Parse error:', parseError);
                            }
                        }
                    }
                }
                
            } catch (error) {
                console.error('Streaming error:', error);
                results.innerHTML = '<h3>❌ Connection Error</h3><p>' + error.message + '</p>';
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Start Streaming Process';
            }
        });
    </script>
</body>
</html>'''
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False) 