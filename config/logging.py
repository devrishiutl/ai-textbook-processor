"""
Logging Configuration with LangSmith Integration
"""
import logging
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Get logging settings directly
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logging():
    """Setup logging configuration with LangSmith integration"""
    # Ensure logs directory exists
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(os.path.join(logs_dir, 'app.log'))
        ]
    )
    
    # Set specific logger levels to reduce noise
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    # Create logger for the application
    logger = logging.getLogger(__name__)
    
    # Setup LangSmith if API key is available
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "ai-textbook-processor")
    LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    
    if LANGSMITH_API_KEY:
        try:
            # Set environment variables for LangSmith
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT
            os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
            os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
            
            # Import and verify LangSmith is working
            import langsmith
            logger.info(f"LangSmith tracing enabled for cost tracking - Project: {LANGSMITH_PROJECT}")
        except ImportError:
            logger.warning("LangSmith not installed - cost tracking disabled")
        except Exception as e:
            logger.warning(f"Failed to setup LangSmith: {str(e)}")
    else:
        logger.warning("LANGSMITH_API_KEY not set - cost tracking disabled")
    
    logger.info("Logging configured successfully")
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with proper configuration"""
    return logging.getLogger(name)

def log_cost_tracking(operation: str, tokens_used: int = None, cost_estimate: float = None):
    """Log cost tracking information"""
    logger = logging.getLogger(__name__)
    if tokens_used:
        logger.info(f"Cost Tracking - Operation: {operation}, Tokens: {tokens_used}")
    if cost_estimate:
        logger.info(f"Cost Tracking - Operation: {operation}, Estimated Cost: ${cost_estimate:.4f}") 