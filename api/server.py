"""
FastAPI Server for Educational Content Processing
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from config.logging import setup_logging

# Step 1: Setup logging first
logger = setup_logging()
logger.info("Initializing FastAPI server")

# Step 2: Create FastAPI app
app = FastAPI(
    title="Educational Content Processor",
    version="1.0.0",
    description="AI-powered educational content processing and generation"
)

# Step 3: Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Step 4: Include routes
app.include_router(router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("FastAPI server starting up")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("FastAPI server shutting down")

@app.get("/")
async def root():
    """Root endpoint with health check"""
    logger.info("Health check requested")
    return {
        "message": "Educational Content Processor API",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "process_json": "/api/process-json",
            "process_stream": "/api/process-stream"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "educational-content-processor"} 