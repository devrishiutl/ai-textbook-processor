"""
Simple and Flexible Configuration for LLM Connections
Supports multiple providers with environment-based selection
"""
import os
from typing import Optional, Dict, Any
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from openai import AzureOpenAI, OpenAI
from dotenv import load_dotenv
from langsmith.wrappers import wrap_openai
import requests
import json

load_dotenv()


class LLMConfig:
    """Simple LLM configuration with provider selection"""
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
        
        # Provider selection (azure, openai)
        self.provider = os.getenv("LLM_PROVIDER", "azure").lower()
        
        # LangSmith configuration
        self.langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        self.langsmith_project = os.getenv("LANGSMITH_PROJECT", "ai-textbook-processor")
        self.langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        
        # Azure OpenAI settings
        self.azure_endpoint = os.getenv("AZURE_OPENAI_API_BASE")
        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        # OpenAI settings
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # Serper API
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        
        # LLM settings with defaults
        self.validation_temperature = float(os.getenv("VALIDATION_TEMPERATURE", "0.05"))
        self.validation_max_tokens = int(os.getenv("VALIDATION_MAX_TOKENS", "200"))
        self.generation_temperature = float(os.getenv("GENERATION_TEMPERATURE", "0.2"))
        self.generation_max_tokens = int(os.getenv("GENERATION_MAX_TOKENS", "4000"))
        
        # Setup LangSmith if available
        self._setup_langsmith()
    
    def _setup_langsmith(self):
        """Setup LangSmith tracing if API key is provided"""
        if self.langsmith_api_key:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = self.langsmith_api_key
            os.environ["LANGCHAIN_PROJECT"] = self.langsmith_project
            os.environ["LANGCHAIN_ENDPOINT"] = self.langsmith_endpoint
    
    def get_openai_client(self):
        """Get OpenAI client based on provider"""
        if self.provider == "azure":
            return wrap_openai(AzureOpenAI(
                azure_endpoint=self.azure_endpoint,
                api_key=self.azure_api_key,
                api_version=self.azure_api_version
            ))
        else:
            return wrap_openai(OpenAI(api_key=self.openai_api_key))
    
    def get_validation_llm(self):
        """Get validation LLM with low temperature for consistent outputs"""
        if self.provider == "azure":
            return AzureChatOpenAI(
                azure_endpoint=self.azure_endpoint,
                api_key=self.azure_api_key,
                azure_deployment=self.azure_deployment,
                api_version=self.azure_api_version,
                temperature=self.validation_temperature,
                max_tokens=self.validation_max_tokens
            )
        else:
            return ChatOpenAI(
                api_key=self.openai_api_key,
                model=self.openai_model,
                temperature=self.validation_temperature,
                max_tokens=self.validation_max_tokens
            )
    
    def get_generation_llm(self):
        """Get generation LLM with higher temperature for creative outputs"""
        if self.provider == "azure":
            return AzureChatOpenAI(
                azure_endpoint=self.azure_endpoint,
                api_key=self.azure_api_key,
                azure_deployment=self.azure_deployment,
                api_version=self.azure_api_version,
                temperature=self.generation_temperature,
                max_tokens=self.generation_max_tokens
            )
        else:
            return ChatOpenAI(
                api_key=self.openai_api_key,
                model=self.openai_model,
                temperature=self.generation_temperature,
                max_tokens=self.generation_max_tokens
            )
    
    def get_model_name(self):
        """Get the current model/deployment name"""
        if self.provider == "azure":
            return self.azure_deployment
        else:
            return self.openai_model
    
    def validate_config(self):
        """Validate that required settings are present"""
        errors = []
        
        if self.provider == "azure":
            if not self.azure_endpoint:
                errors.append("AZURE_OPENAI_API_BASE is required")
            if not self.azure_api_key:
                errors.append("AZURE_OPENAI_API_KEY is required")
            if not self.azure_deployment:
                errors.append("AZURE_OPENAI_DEPLOYMENT_NAME is required")
        else:
            if not self.openai_api_key:
                errors.append("OPENAI_API_KEY is required")
        
        if errors:
            raise ValueError(f"Configuration errors: {'; '.join(errors)}")


class WebScraper:
    """Simple web scraping utility"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def scrape_url(self, url: str) -> str:
        """Scrape content from a URL using Serper API"""
        if not self.api_key:
            raise ValueError("SERPER_API_KEY is required for web scraping")
        
        scrape_url = "https://scrape.serper.dev"
        payload = json.dumps({"url": url})
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(scrape_url, headers=headers, data=payload)
        response.raise_for_status()
        return response.text


# Global instances
config = LLMConfig()
scraper = WebScraper(config.serper_api_key)

# Convenience functions
def get_validation_llm():
    """Get validation LLM instance"""
    return config.get_validation_llm()

def get_generation_llm():
    """Get generation LLM instance"""
    return config.get_generation_llm()

def get_llm_client():
    """Get OpenAI client instance"""
    return config.get_openai_client()

def get_weburl_content(url: str) -> str:
    """Scrape content from a URL"""
    return scraper.scrape_url(url)

def get_model_name() -> str:
    """Get current model/deployment name"""
    return config.get_model_name()

# Legacy aliases for backward compatibility
llm_client = get_llm_client()
LLM_MODEL = get_model_name() 