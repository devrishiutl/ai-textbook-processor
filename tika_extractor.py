#!/usr/bin/env python3
"""
Apache Tika PDF Extractor
Separate module for Tika-based PDF text extraction
Can be used as fallback when Docling fails
"""

import requests
import logging
import time
from typing import Optional

# Create logger for this module
logger = logging.getLogger(__name__)

class TikaExtractor:
    """Apache Tika PDF text extractor"""
    
    def __init__(self, server_url: str = "http://localhost:8004/tika", timeout: int = 120):
        """
        Initialize Tika extractor
        
        Args:
            server_url: URL of the Tika server
            timeout: Request timeout in seconds
        """
        self.server_url = server_url
        self.timeout = timeout
        self.session = requests.Session()
    
    def check_server_status(self) -> bool:
        """Check if Tika server is running and accessible"""
        try:
            response = self.session.get(self.server_url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Tika server not accessible: {str(e)}")
            return False
    
    def extract_text(self, pdf_path: str) -> str:
        """
        Extract text from PDF using Tika server
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
            
        Raises:
            Exception: If extraction fails
        """
        try:
            logger.info(f"Extracting text from PDF using Tika: {pdf_path}")
            start_time = time.time()
            
            # Check server status first
            if not self.check_server_status():
                raise Exception("Tika server is not running or accessible")
            
            # Read PDF file
            with open(pdf_path, 'rb') as f:
                headers = {
                    "Accept": "text/plain"
                }
                
                # Send request to Tika server
                response = self.session.put(
                    self.server_url, 
                    headers=headers, 
                    data=f, 
                    timeout=self.timeout
                )
            
            # Check response
            if response.status_code == 200:
                text = response.text
                elapsed_time = time.time() - start_time
                logger.info(f"Tika extraction completed in {elapsed_time:.2f} seconds")
                logger.info(f"Extracted {len(text)} characters of text")
                
                # Validate extracted content
                if not text or not text.strip():
                    raise Exception("Tika extracted no text content")
                
                return text
            else:
                raise Exception(f"Tika server returned status {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            raise Exception(f"Tika extraction timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to Tika server. Make sure it's running on port 8004")
        except FileNotFoundError:
            raise Exception(f"PDF file not found: {pdf_path}")
        except Exception as e:
            logger.error(f"Tika extraction failed: {str(e)}")
            raise Exception(f"Tika extraction failed: {str(e)}")

# Global Tika extractor instance
tika_extractor = TikaExtractor()

def extract_pdf_content_tika(pdf_path: str) -> str:
    """
    Extract PDF content using Tika (convenience function)
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text content or error message
    """
    try:
        return tika_extractor.extract_text(pdf_path)
    except Exception as e:
        return f"ERROR: {str(e)}"

def is_tika_available() -> bool:
    """
    Check if Tika is available and server is running
    
    Returns:
        True if Tika is available, False otherwise
    """
    try:
        return tika_extractor.check_server_status()
    except Exception:
        return False

# Test function
def test_tika_extraction(pdf_path: str) -> None:
    """Test Tika extraction with detailed output"""
    print(f"🧪 Testing Tika extraction for: {pdf_path}")
    print("=" * 60)
    
    # Test server status
    print("1️⃣ Checking Tika server status...")
    if tika_extractor.check_server_status():
        print("✅ Tika server is running and accessible")
    else:
        print("❌ Tika server is not accessible")
        print("   Make sure to start Tika server with: java -jar tika-server.jar --port 8004")
        return
    
    # Test text extraction
    print("\n2️⃣ Testing text extraction...")
    try:
        text = tika_extractor.extract_text(pdf_path)
        print(f"✅ Text extraction successful: {len(text)} characters")
        print(f"📝 First 300 characters:\n{text[:300]}...")
    except Exception as e:
        print(f"❌ Text extraction failed: {str(e)}")

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = input("Enter PDF file path: ").strip()
    
    if pdf_path:
        test_tika_extraction(pdf_path)
    else:
        print("❌ No PDF file specified")
        print("\nUsage:")
        print("python tika_extractor.py path/to/file.pdf")
        print("\nOr start Tika server first:")
        print("java -jar tika-server.jar --port 8004") 