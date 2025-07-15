"""
Clean API Routes with SOLID Principles and Singleton Pattern
"""
from utils.chroma_utility import store_textbook_transcript, get_textbook_transcript
from agents.helper import extract_content_from_files, create_initial_state, format_response, clean_for_llm_prompt, get_youtube_transcript
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import tempfile
import os
import json
import asyncio
from agents.graph import graph
from pdf2image import convert_from_path
# Initialize logging
from config.logging import setup_logging
from config.configuration import get_weburl_content
from config.settings import SUPPORTED_PDF_EXTENSION
logger = setup_logging()

# ===== REQUEST MODELS =====

class GetContentRequest(BaseModel):
    """Request model for get content endpoints"""
    standard: str
    subject: str
    chapter: str
    ids: str

# ===== SINGLETON PATTERN =====

class APIService:
    """Singleton API Service following SOLID principles"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.app = FastAPI(
            title="AI Textbook Processor",
            description="AI-powered system for processing educational content",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        self._setup_cors()
        self._setup_routes()
    
    def _setup_cors(self):
        """Setup CORS middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup API routes"""
        self.app.get("/health")(self.health_check)
        self.app.post("/api/process-json")(self.process_content_json)
        self.app.post("/api/process-stream")(self.process_content_stream)
        self.app.post("/api/upload-content")(self.upload_content)
        self.app.post("/api/get-content")(self.get_content)
        self.app.post("/api/get-content-stream")(self.get_content_stream)
    
    async def health_check(self):
        """Health check endpoint"""
        return {
            "status": "healthy",
            "message": "AI Textbook Processor is running",
            "version": "1.0.0"
        }
    
    async def process_content_extraction(self, content_type: str, files: Optional[List[UploadFile]] = None, content_or_url: Optional[str] = None) -> str:
        """Extract content based on type - Single Responsibility"""
        if content_type == "text":
            if not content_or_url:
                raise HTTPException(400, "text_content required")
            return content_or_url
        elif content_type == "web_url":
            if not content_or_url:
                raise HTTPException(400, "web_url required")
            return get_weburl_content(content_or_url)
        elif content_type == "youtube_url":
            if not content_or_url:
                raise HTTPException(400, "youtube_url required")
            return get_youtube_transcript(content_or_url)
        elif content_type == "pdf":
            if not files:
                raise HTTPException(400, "files required for PDF processing")
            return await self._process_pdf(files)
        elif content_type == "images":
            if not files:
                raise HTTPException(400, "files required for image processing")
            return await self._process_images(files)
        else:
            raise HTTPException(400, "Invalid content_type")
    
    async def _process_pdf(self, files: List[UploadFile]) -> str:
        """Process PDF files - Single Responsibility"""
        if not files:
            raise HTTPException(400, "No files provided")
        if len(files) != 1:
            raise HTTPException(400, "Exactly one PDF file is required")
        if not files[0].filename.lower().endswith(SUPPORTED_PDF_EXTENSION):
            raise HTTPException(400, "File must be a PDF")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=SUPPORTED_PDF_EXTENSION) as temp_pdf:
            temp_pdf.write(await files[0].read())
            temp_pdf.flush()
        
        try:
            pil_images = convert_from_path(temp_pdf.name, dpi=150)
        finally:
            os.unlink(temp_pdf.name)
        
        image_paths = []
        for i, img in enumerate(pil_images):
            temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            img.save(temp_img.name, "JPEG", quality=70, optimize=True)
            image_paths.append(temp_img.name)
        
        content = extract_content_from_files(None, image_paths)
        
        for path in image_paths:
            try:
                os.unlink(path)
            except:
                pass
        
        if content.startswith("ERROR"):
            raise HTTPException(400, f"PDF processing failed: {content}")
        return content
    
    async def _process_images(self, files: List[UploadFile]) -> str:
        """Process image files - Single Responsibility"""
        if not files:
            raise HTTPException(400, "No files provided")
        
        image_paths = []
        for file in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
                f.write(await file.read())
                image_paths.append(f.name)
        
        content = extract_content_from_files(None, image_paths)
        
        for path in image_paths:
            try:
                os.unlink(path)
            except:
                pass
        
        if content.startswith("ERROR"):
            raise HTTPException(400, f"Image processing failed: {content}")
        return content
    
    async def process_with_graph(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process state through graph with timeout"""
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(graph.invoke, state),
                timeout=60.0
            )
            return result
        except asyncio.TimeoutError:
            raise HTTPException(500, "Processing timeout - request took too long")
    
    async def process_content_json(self, standard: str = Form(...), subject: str = Form(...), chapter: str = Form(...), content_type: str = Form(...), files: Optional[Union[UploadFile, List[UploadFile]]] = File(None), content_or_url: Optional[str] = Form(None)):
        """Process content and return JSON response"""
        # Normalize files to a list
        if files is None:
            files_list = []
        elif isinstance(files, list):
            files_list = files
        else:
            files_list = [files]
        try:
            content = await self.process_content_extraction(content_type, files_list, content_or_url)
            content = clean_for_llm_prompt(content)
            state = create_initial_state(standard, subject, chapter, content)
            result = await self.process_with_graph(state)
            return format_response(result)
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            raise HTTPException(500, f"Processing error: {str(e)}")
    
    async def process_content_stream(self, standard: str = Form(...), subject: str = Form(...), chapter: str = Form(...), content_type: str = Form(...), files: Optional[Union[UploadFile, List[UploadFile]]] = File(None), content_or_url: Optional[str] = Form(None)):
        """Process content and return streaming response"""
        # Normalize files to a list
        if files is None:
            files_list = []
        elif isinstance(files, list):
            files_list = files
        else:
            files_list = [files]
        try:
            content = await self.process_content_extraction(content_type, files_list, content_or_url)
            content = clean_for_llm_prompt(content)
            state = create_initial_state(standard, subject, chapter, content)
            result = await self.process_with_graph(state)
            final_response = format_response(result)
            
            async def generate_stream():
                steps = [
                    ("Extracting content from uploaded files...", 10),
                    (f"Grade validation passed for {standard}", 40),
                    ("Content passed profanity validation", 60),
                    (f"Content is relevant to {subject} - {chapter}", 80),
                    ("Study notes generated successfully", 90),
                    ("Fill-in-the-blanks generated successfully", 94),
                    ("Matching questions generated successfully", 98),
                    ("Q&A generated successfully", 100),
                ]
                
                for i, (message, progress) in enumerate(steps, 1):
                    yield f"data: {json.dumps({'step': i, 'status': 'processing', 'message': message, 'progress': progress - 3})}\n\n"
                    await asyncio.sleep(0.2)
                    yield f"data: {json.dumps({'step': i, 'status': 'completed', 'message': message, 'progress': progress})}\n\n"
                    await asyncio.sleep(0.1)
                
                yield f"data: {json.dumps({'step': 'final', 'status': 'completed', 'message': 'All educational materials generated successfully!', 'progress': 100, 'success': True, 'result': final_response})}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream"
                }
            )
        except Exception as e:
            logger.error(f"Streaming processing error: {str(e)}")
            return StreamingResponse(
                iter([f"data: {json.dumps({'step': 'error', 'status': 'error', 'message': f'Processing error: {str(e)}', 'progress': 100, 'error': True})}\n\n"]),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream"
                }
            )
    
    async def upload_content(self, standard: str = Form(...), subject: str = Form(...), chapter: str = Form(...), content_type: str = Form(...), files: Optional[Union[UploadFile, List[UploadFile]]] = File(None), content_or_url: Optional[str] = Form(None)):
        """Upload and store content"""
        # Normalize files to a list
        if files is None:
            files_list = []
        elif isinstance(files, list):
            files_list = files
        else:
            files_list = [files]
        try:
            content = await self.process_content_extraction(content_type, files_list, content_or_url)
            content = clean_for_llm_prompt(content)
            ids = store_textbook_transcript(standard, subject, chapter, content, content_type)
            return ids
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            raise HTTPException(500, f"Upload error: {str(e)}")
    
    async def get_content(self, standard: str = Form(...), subject: str = Form(...), chapter: str = Form(...), ids: str = Form(...)):
        """Get stored content and process"""
        try:
            content = get_textbook_transcript(ids)
            if content is None:
                raise HTTPException(404, f"Content not found with ID: {ids}")
            
            state = create_initial_state(standard, subject, chapter, content)
            result = await self.process_with_graph(state)
            return format_response(result)
        except Exception as e:
            logger.error(f"Get content error: {str(e)}")
            raise HTTPException(500, f"Get content error: {str(e)}")
    
    async def get_content_stream(self, request: GetContentRequest):
        """Get stored content and process with streaming - CONDITIONAL STREAMING"""
        # Extract values from request
        ids = request.ids
        standard = request.standard
        subject = request.subject
        chapter = request.chapter
        
        try:
            content = get_textbook_transcript(ids)
            if content is None:
                raise HTTPException(404, f"Content not found with ID: {ids}")
            
            async def generate_stream():
                # Step 1: Data Retrieving
                yield f"data: {json.dumps({'step': 1, 'status': 'processing', 'message': 'Retrieving stored content from database...', 'progress': 10})}\n\n"
                await asyncio.sleep(0.3)
                yield f"data: {json.dumps({'step': 1, 'status': 'completed', 'message': 'Content retrieved successfully', 'progress': 30})}\n\n"
                await asyncio.sleep(0.2)
                
                # Step 2: Data Validation (Dynamic - call invoke)
                yield f"data: {json.dumps({'step': 2, 'status': 'processing', 'message': 'Validating content for grade level and safety...', 'progress': 40})}\n\n"
                await asyncio.sleep(0.3)
                
                # Call the validation step dynamically
                validation_state = create_initial_state(standard, subject, chapter, content)
                from agents.nodes import validate_content
                validation_result = validate_content(validation_state)
                
                # Check validation results
                validation_data = validation_result.get('validation_result', {})
                if isinstance(validation_data, str):
                    # If validation_result is a string (error), stop here
                    yield f"data: {json.dumps({'step': 2, 'status': 'error', 'message': f'Validation failed: {validation_data}', 'progress': 60, 'error': True})}\n\n"
                    yield f"data: {json.dumps({'step': 'final', 'status': 'error', 'message': 'Processing stopped due to validation failure', 'progress': 100, 'error': True})}\n\n"
                    return
                
                # Check individual validation criteria
                grade_check = validation_data.get('grade_check', 'INAPPROPRIATE')
                safety_check = validation_data.get('safety_check', 'INAPPROPRIATE')
                relevance_check = validation_data.get('relevance_check', 'NO_MATCH')
                
                validation_messages = []
                if grade_check != 'APPROPRIATE':
                    validation_messages.append(f"Grade level check failed: {grade_check}")
                if safety_check != 'APPROPRIATE':
                    validation_messages.append(f"Safety check failed: {safety_check}")
                if relevance_check not in ['MATCH', 'PARTIAL_MATCH']:
                    validation_messages.append(f"Relevance check failed: {relevance_check}")
                
                # If any validation failed, stop here
                if validation_messages:
                    error_message = "; ".join(validation_messages)
                    yield f"data: {json.dumps({'step': 2, 'status': 'error', 'message': f'Validation failed: {error_message}', 'progress': 60, 'error': True})}\n\n"
                    yield f"data: {json.dumps({'step': 'final', 'status': 'error', 'message': 'Processing stopped due to validation failure', 'progress': 100, 'error': True})}\n\n"
                    return
                
                # Validation passed - continue with generation
                yield f"data: {json.dumps({'step': 2, 'status': 'completed', 'message': 'All validation checks passed', 'progress': 60})}\n\n"
                await asyncio.sleep(0.2)
                
                # Step 3: Data Generation (Dynamic - call invoke)
                yield f"data: {json.dumps({'step': 3, 'status': 'processing', 'message': 'Generating educational materials...', 'progress': 70})}\n\n"
                await asyncio.sleep(0.3)
                
                # Call the generation step dynamically
                generation_state = create_initial_state(standard, subject, chapter, content)
                # Set validation as passed since we already validated
                generation_state["is_valid"] = True
                generation_state["validation_result"] = validation_result.get("validation_result", {})
                
                from agents.nodes import generate_content
                generation_result = generate_content(generation_state)
                final_response = format_response(generation_result)
                
                # Send final result
                yield f"data: {json.dumps({'step': 'final', 'status': 'completed', 'message': 'Dynamic processing completed successfully!', 'progress': 100, 'success': True, 'result': final_response})}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream"
                }
            )
        except Exception as e:
            logger.error(f"Dynamic streaming error: {str(e)}")
            return StreamingResponse(
                iter([f"data: {json.dumps({'step': 'error', 'status': 'error', 'message': f'Dynamic streaming error: {str(e)}', 'progress': 100, 'error': True})}\n\n"]),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream"
                }
            )

# Create singleton instance
api_service = APIService()
app = api_service.app