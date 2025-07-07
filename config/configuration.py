"""
Simple Configuration with LangSmith Integration
"""
import os
from langchain_openai import AzureChatOpenAI
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# LangSmith Configuration
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", None)
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "ai-textbook-processor")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

# Set LangChain environment variables for tracing
if LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT

# Azure OpenAI client for vision processing (direct OpenAI API)
# This is used for vision/image processing tasks
azure_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_API_BASE"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

def get_llm(temperature: float = 0.1, max_tokens: int = None):
    """Get LLM instance with LangSmith tracing enabled"""
    return AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_API_BASE"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature=temperature,
        max_tokens=max_tokens,
        # LangSmith tracing is automatically enabled when environment variables are set
        # tags=["cost-tracking"]  # Add tags for better organization
    )

def get_validation_llm():
    """Get LLM optimized for validation tasks with LangSmith tracing"""
    return get_llm(temperature=0.05, max_tokens=200)

def get_generation_llm():
    """Get LLM optimized for content generation tasks with LangSmith tracing"""
    return get_llm(temperature=0.2, max_tokens=4000) 