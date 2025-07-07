"""
Main Entry Point for Educational Content Processor
"""
import logging
import sys
from config.logging import setup_logging
from services.content_service import ContentProcessingService

def main():
    """Main entry point with proper initialization order"""
    try:
        # Step 1: Setup logging first
        logger = setup_logging()
        logger.info("Starting Educational Content Processor")
        
        # Step 2: Initialize service
        logger.info("Initializing Content Processing Service")
        service = ContentProcessingService()
        
        # Step 3: Example usage with proper error handling
        logger.info("Running example processing")
        result = service.process_content(
            standard="Class 10",
            subject="Mathematics", 
            chapter="Algebra",
            pdf_path="example.pdf"  # Optional
        )
        
        if result.get('success'):
            logger.info("Processing completed successfully")
            print("✅ Processing complete!")
        else:
            logger.error(f"Processing failed: {result.get('error', 'Unknown error')}")
            print("❌ Processing failed!")
            return 1
        
        return result
        
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        print(f"❌ Application error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 