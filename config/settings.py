"""
Configuration Settings
"""
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables from .env file
load_dotenv()

# Azure OpenAI Configuration
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_API_BASE", "https://your-resource.openai.azure.com/")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "your-api-key")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

# Initialize Azure client
azure_client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_API_KEY,
    api_version=AZURE_API_VERSION
)

# Application Settings
MAX_FILE_SIZE_PDF = 100 * 1024 * 1024  # 100MB
MAX_FILE_SIZE_IMAGE = 50 * 1024 * 1024  # 50MB
MAX_IMAGE_DIMENSION = 2048

# Supported file formats
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
SUPPORTED_PDF_FORMATS = ['.pdf']

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Processing Settings
MAX_CONTENT_LENGTH = 10000  # Maximum content length for processing
MAX_TOKENS_PER_REQUEST = 3000  # Maximum tokens for LLM requests
TEMPERATURE = 0.1  # LLM temperature setting

# Validation Settings
MIN_CONTENT_LENGTH = 50  # Minimum content length for validation
MIN_MEANINGFUL_CHARS = 20  # Minimum meaningful characters for validation

# LangSmith Configuration
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", None)
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "ai-textbook-processor")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com") 