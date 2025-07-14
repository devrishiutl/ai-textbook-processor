import os
from dotenv import load_dotenv
from langsmith import traceable

load_dotenv()
from mistralai import Mistral

# Set up the client
api_key =  os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)

@traceable(name="mistral_file_upload")
def upload_file(file_path):
    """Upload file to Mistral and return signed URL."""
    with open(file_path, "rb") as f:
        uploaded = client.files.upload(
            file={"file_name": os.path.basename(file_path), "content": f},
            purpose="ocr"
        )
    signed_url = client.files.get_signed_url(file_id=uploaded.id)
    return signed_url.url

@traceable(name="mistral_ocr_processing")
def ocr_from_url(url, file_type="document_url"):
    """Process OCR from given signed URL (PDF or image)."""
    response = client.ocr.process(
        model="mistral-ocr-latest",
        document={"type": file_type, "document_url": url},
        include_image_base64=False
    )
    
    # Extract markdown from all pages
    markdown_content = ""
    for page in response.pages:
        markdown_content += page.markdown + "\n\n"
    
    return markdown_content.strip()

# --- OCR for PDF ---
@traceable(name="mistral_pdf_text_extraction")
def extract_text_from_pdf(pdf_path):
    pdf_url = upload_file(pdf_path)
    pdf_text = ocr_from_url(pdf_url)
    return pdf_text

# --- OCR for Image Array ---
@traceable(name="mistral_image_text_extraction")
def extract_text_from_image(image_paths):
    for image_path in image_paths:
        image_url = upload_file(image_path)
        image_text = ocr_from_url(image_url)
        return image_text