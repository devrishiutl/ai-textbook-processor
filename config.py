import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables from .env file
load_dotenv()

# LangSmith Configuration
LANGSMITH_API_KEY = os.getenv("LANG_SMITH_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "ai-textbook-processor")

# Set up LangSmith tracing environment variables
if LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY  # This is the key line
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    print(f"✅ LangSmith tracing enabled for project: {LANGSMITH_PROJECT}")
else:
    print("⚠️ LangSmith tracing disabled - LANG_SMITH_KEY not found")

# Your existing Azure OpenAI setup
azure_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_API_BASE")
)
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# Wrap Azure client with LangSmith tracing
try:
    if LANGSMITH_API_KEY:
        from langsmith.wrappers import wrap_openai
        azure_client = wrap_openai(azure_client)
        print("✅ Azure OpenAI client wrapped with LangSmith tracing")
except ImportError:
    print("⚠️ LangSmith not installed. Install with: pip install langsmith")
except Exception as e:
    print(f"⚠️ LangSmith wrapping failed: {e}")