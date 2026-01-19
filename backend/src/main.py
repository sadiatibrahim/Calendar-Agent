"""
FastAPI main application for Calendar Assistant backend.

This module provides REST API endpoints for the calendar assistant,
handling text input, file uploads (images/PDFs), and agent interactions.
"""

import logging
import os
import sys
from typing import Optional, Union
from pathlib import Path
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from openai import OpenAI

from src.calendar_agents import CalendarAgentRunner
from src.services import VisionService, ChatService
from src.models import UserContext, CalendarAgentOutput

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Calendar Assistant API",
    description="AI-powered calendar and task management assistant",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")

openai_client = OpenAI(api_key=openai_api_key)
agent_runner = CalendarAgentRunner(api_key=openai_api_key)
vision_service = VisionService(client=openai_client)
chat_service = ChatService(agent_runner=agent_runner, vision_service=vision_service)

logger.info("Calendar Assistant API initialized")


# Request/Response Models
class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    message: str = Field(..., description="Agent's response message")
    user_id: Optional[str] = Field(None, description="User ID for the session")
    extracted_text: Optional[str] = Field(None, description="Text extracted from file (if applicable)")


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "status": "healthy",
        "service": "Calendar Assistant API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "services": {
            "agent": "running",
            "vision": "running"
        }
    }


@app.post("/chat", response_model=CalendarAgentOutput)
async def chat(
    message: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    user_id: Optional[str] = Form(None)
):
    """
    Chat endpoint for interacting with the calendar assistant.
    
    Handles text messages, file uploads (images/PDFs), or both.
    If a file is provided, text is extracted and appended to the user's message.
    
    Args:
        message: Optional text message from user
        file: Optional file upload (image, screenshot, or PDF)
        user_id: Optional user ID for session continuity (auto-generated if not provided)
        
    Returns:
        CalendarAgentOutput: Agent's response with message and user_id
        
    Raises:
        HTTPException: If processing fails or no input provided
    """
    try:
        # Read file data if provided
        file_data = None
        file_type = None
        file_name = None
        
        if file:
            file_data = await file.read()
            file_type = file.content_type
            file_name = file.filename
        
        # Process chat through service
        output = await chat_service.process_chat(
            message=message,
            file_data=file_data,
            file_type=file_type,
            file_name=file_name,
            user_id=user_id
        )
        
        return output
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat request: {str(e)}"
        )


# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
