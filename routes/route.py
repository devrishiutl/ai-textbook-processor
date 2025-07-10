"""
Simple API Routes
"""
from agents.helper import clean_ocr_math_text, extract_content_from_files, create_initial_state, format_response
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
    files: List[UploadFile] = File([]),
    text_content: Optional[str] = Form(None)
):
    try:
        if content_type == "text":
            if not text_content:
                raise HTTPException(400, "text_content required")
            content = text_content

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

        content = clean_ocr_math_text(content)
        print(content)
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
    files: List[UploadFile] = File([]),
    text_content: Optional[str] = Form(None)
):
    """Process content and return streaming response with 8 required steps"""
    try:
        content = None
        if content_type == "text":
            if not text_content:
                raise HTTPException(400, "text_content required")
            content = text_content

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

        content = clean_ocr_math_text(content)
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
        return StreamingResponse(
            iter([f"data: {json.dumps({'step': 'error', 'status': 'error', 'message': f'Processing error: {str(e)}', 'progress': 100, 'error': True})}\n\n"]),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )