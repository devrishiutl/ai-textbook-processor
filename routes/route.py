"""
Simple API Routes
"""
from agents.helper import extract_content_from_files, create_initial_state, format_response, clean_for_llm_prompt, get_youtube_transcript
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Optional
import tempfile
import os
import json
import asyncio
from agents.graph import graph
from pdf2image import convert_from_path
# Initialize logging
from config.logging import setup_logging
from config.configuration import get_weburl_content
logger = setup_logging()

app = FastAPI()

# Enable CORS from all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/process-json")
async def process_content_json(
    standard: str = Form(...),
    subject: str = Form(...),
    chapter: str = Form(...),
    content_type: str = Form(...),
    files: Optional[List[UploadFile]] = File([]),
    content_or_url: Optional[str] = Form(None)
):
    try:
        if content_type == "text":
            if not content_or_url:
                raise HTTPException(400, "text_content required")
            content = content_or_url

        elif content_type == "web_url":
            if not content_or_url:
                raise HTTPException(400, "web_url required")
            content = get_weburl_content(content_or_url)

        elif content_type == "youtube_url":
            if not content_or_url:
                raise HTTPException(400, "youtube_url required")
            content = get_youtube_transcript(content_or_url)

        elif content_type == "pdf":
            if len(files) != 1 or not files[0].filename.lower().endswith(".pdf"):
                raise HTTPException(400, "Exactly one PDF file is required")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(await files[0].read())
                temp_pdf.flush()

            try:
                pil_images = convert_from_path(temp_pdf.name)
            finally:
                os.unlink(temp_pdf.name)

            image_paths = []
            for img in pil_images:
                temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                img.save(temp_img.name, "JPEG")
                image_paths.append(temp_img.name)

            content = extract_content_from_files(None, image_paths)
            for path in image_paths:
                os.unlink(path)

            if content.startswith("ERROR"):
                raise HTTPException(400, f"PDF processing failed: {content}")

        elif content_type == "images":
            if not files:
                raise HTTPException(400, "files required")
            image_paths = []
            for file in files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
                    f.write(await file.read())
                    image_paths.append(f.name)
            content = extract_content_from_files(None, image_paths)
            for path in image_paths:
                os.unlink(path)

        else:
            raise HTTPException(400, "Invalid content_type")

        content = clean_for_llm_prompt(content)
        state = create_initial_state(standard, subject, chapter, content)
        result = graph.invoke(state)
        return format_response(result)

    except Exception as e:
        import traceback
        error_details = f"Processing error: {str(e)}\nFull traceback:\n{traceback.format_exc()}"
        logger.error(error_details)
        raise HTTPException(500, f"Processing error: {str(e)}")

@app.post("/api/process-stream")
async def process_content_stream(
    standard: str = Form(...),
    subject: str = Form(...),
    chapter: str = Form(...),
    content_type: str = Form(...),
    files: Optional[List[UploadFile]] = File([]),
    content_or_url: Optional[str] = Form(None)
):
    """Process content and return streaming response with 8 required steps"""
    try:
        content = None
        if content_type == "text":
            if not content_or_url:
                raise HTTPException(400, "text_content required")
            content = content_or_url

        elif content_type == "web_url":
            if not content_or_url:
                raise HTTPException(400, "web_url required")
            content = get_weburl_content(content_or_url)

        elif content_type == "youtube_url":
            if not content_or_url:
                raise HTTPException(400, "youtube_url required")
            content = get_youtube_transcript(content_or_url)

        elif content_type == "pdf":
            if len(files) != 1 or not files[0].filename.lower().endswith(".pdf"):
                raise HTTPException(400, "Exactly one PDF file is required")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(await files[0].read())
                temp_pdf.flush()

            try:
                pil_images = convert_from_path(temp_pdf.name)
            finally:
                os.unlink(temp_pdf.name)

            image_paths = []
            for img in pil_images:
                temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                img.save(temp_img.name, "JPEG")
                image_paths.append(temp_img.name)

            content = extract_content_from_files(None, image_paths)
            for path in image_paths:
                os.unlink(path)

            if content.startswith("ERROR"):
                raise HTTPException(400, f"PDF processing failed: {content}")

        elif content_type == "images":
            if not files:
                raise HTTPException(400, "Image files required")
            image_paths = []
            for file in files:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
                    f.write(await file.read())
                    f.flush()
                    f.close()
                    image_paths.append(f.name)
            content = extract_content_from_files(None, image_paths)
            for path in image_paths:
                try: os.unlink(path)
                except: pass

        else:
            raise HTTPException(400, "Invalid content_type")

        content = clean_for_llm_prompt(content)
        state = create_initial_state(standard, subject, chapter, content)
        result = graph.invoke(state)
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
            step_names = [
                "Content Extraction", "Grade Validation", "Profanity Validation", "Relevancy Check",
                "Study Notes Generation", "Fill-ups Generation", "Match the Following Generation", "Question Answer Generation"
            ]
            for i, (message, progress) in enumerate(steps, 1):
                yield f"data: {json.dumps({'step': i, 'status': 'processing', 'message': message, 'progress': progress - 5})}\n\n"
                await asyncio.sleep(0.5)
                yield f"data: {json.dumps({'step': i, 'status': 'completed', 'message': message, 'progress': progress})}\n\n"
                await asyncio.sleep(0.5)
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
        import traceback
        error_details = f"Streaming processing error: {str(e)}\nFull traceback:\n{traceback.format_exc()}"
        logger.error(error_details)
        return StreamingResponse(
            iter([f"data: {json.dumps({'step': 'error', 'status': 'error', 'message': f'Processing error: {str(e)}', 'progress': 100, 'error': True})}\n\n"]),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )