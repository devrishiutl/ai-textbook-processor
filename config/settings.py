"""
Application Settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Import LLM config from configuration
from config.configuration import config

# Azure OpenAI Configuration (from config)
AZURE_ENDPOINT = config.AZURE_ENDPOINT
AZURE_API_KEY = config.AZURE_API_KEY
AZURE_DEPLOYMENT_NAME = config.AZURE_DEPLOYMENT_NAME
AZURE_API_VERSION = config.AZURE_API_VERSION
azure_client = config.azure_client

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