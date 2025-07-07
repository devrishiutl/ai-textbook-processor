"""
Simple Singleton Configuration for LLM Connections
"""
import os
from langchain_openai import AzureChatOpenAI
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Simple singleton configuration for LLM connections"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        """Initialize LLM configuration once"""
        # LangSmith
        self.LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
        self.LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "ai-textbook-processor")
        self.LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        
        # Azure OpenAI
        self.AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_API_BASE")
        self.AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
        self.AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        # Setup LangSmith
        if self.LANGSMITH_API_KEY:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = self.LANGSMITH_API_KEY
            os.environ["LANGCHAIN_PROJECT"] = self.LANGSMITH_PROJECT
            os.environ["LANGCHAIN_ENDPOINT"] = self.LANGSMITH_ENDPOINT
        
        # Initialize connections
        self._azure_client = None
        self._validation_llm = None
        self._generation_llm = None
    
    @property
    def azure_client(self):
        """Get Azure client (lazy init)"""
        if self._azure_client is None:
            self._azure_client = AzureOpenAI(
                azure_endpoint=self.AZURE_ENDPOINT,
                api_key=self.AZURE_API_KEY,
                api_version=self.AZURE_API_VERSION
            )
        return self._azure_client
    
    def get_validation_llm(self):
        """Get validation LLM"""
        if self._validation_llm is None:
            self._validation_llm = AzureChatOpenAI(
                azure_endpoint=self.AZURE_ENDPOINT,
                api_key=self.AZURE_API_KEY,
                azure_deployment=self.AZURE_DEPLOYMENT_NAME,
                api_version=self.AZURE_API_VERSION,
                temperature=0.05,
                max_tokens=200
            )
        return self._validation_llm
    
    def get_generation_llm(self):
        """Get generation LLM"""
        if self._generation_llm is None:
            self._generation_llm = AzureChatOpenAI(
                azure_endpoint=self.AZURE_ENDPOINT,
                api_key=self.AZURE_API_KEY,
                azure_deployment=self.AZURE_DEPLOYMENT_NAME,
                api_version=self.AZURE_API_VERSION,
                temperature=0.2,
                max_tokens=4000
            )
        return self._generation_llm

# Global instance
config = Config()

# Convenience functions
def get_validation_llm():
    return config.get_validation_llm()

def get_generation_llm():
    return config.get_generation_llm()

# Legacy aliases
azure_client = config.azure_client
AZURE_DEPLOYMENT_NAME = config.AZURE_DEPLOYMENT_NAME 