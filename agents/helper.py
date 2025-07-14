"""
Simple Agent Helper Functions
"""
from typing import Dict, Any, List, Union
# from utils.utility import read_data_from_image #,read_data_from_file
from utils.text_extractor import extract_text
from pdf2image import convert_from_path
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
import whisper
from cleantext import clean

def clean_for_llm_prompt(raw_text):
    cleaned = clean(raw_text, no_line_breaks=True, replace_with_punct=" ")
    cleaned = cleaned.replace("\\", "\\\\")  # Escape raw backslashes
    return cleaned


def get_youtube_transcript(video_url):
    video_id = video_url.split("v=")[-1]

    # Try to get transcript directly
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi'])
        text = ' '.join([item['text'] for item in transcript_list])
        return text
    except:

        # Download audio
        yt = YouTube(video_url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        audio_path = audio_stream.download(filename='audio.mp4')

        # Transcribe using Whisper
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        return result['text']


# def extract_content_from_files(pdf_path: str = None, image_paths: List[str] = None) -> str:
#     """Extract content from files"""
#     if pdf_path:
#         # Convert PDF to images using pdf2image
#         images = convert_from_path(pdf_path, dpi=300)
#         return read_data_from_image(images)
#     elif image_paths:
#         return read_data_from_image(image_paths)
#     return "ERROR: No files provided"

def extract_content_from_files(pdf_path: str = None, image_paths: List[str] = None) -> str:
    """Extract content from files"""
    if pdf_path:
        # For PDF files, use the text_extractor directly
        return extract_text(pdf_path, export_format="markdown")
    elif image_paths:
        # For image files, use the text_extractor
        return extract_text(image_paths, export_format="markdown")
    return "ERROR: No files provided"

def create_initial_state(standard: str, subject: str, chapter: str, content: str) -> Dict[str, Any]:
    """Create initial state"""
    return {
        "standard": standard,
        "subject": subject,
        "chapter": chapter,
        "content": content,
        "is_valid": False,
        "success": False,
        "error": None,
        "generated_content": None,
        "validation_result": None
    }

# def format_response(state: Dict[str, Any]) -> Dict[str, Any]:
#     """Format response"""
#     if state.get("error"):
#         return {
#             "success": False, 
#             "error": state["error"]
#         }
#     return {
#         "success": True,
#         "content": state.get("generated_content", ""),
#         "validation_result": state.get("validation_result"),
#         "metadata": {
#             "standard": state.get("standard"),
#             "subject": state.get("subject"),
#             "chapter": state.get("chapter")
#         }
#     } 

def format_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """Format response"""
    if state.get("error"):
        return {
            "success": False,
            "error": state["error"]
        }
    
    # Escape backslashes in generated content
    result = state.get("generated_content", "")
    if isinstance(result, str):
        result = result.replace("\\", "\\\\")
    
    return {
        "success": True,
        "content": result,
        "validation_result": state.get("validation_result"),
        "metadata": {
            "standard": state.get("standard"),
            "subject": state.get("subject"),
            "chapter": state.get("chapter")
        }
    }
