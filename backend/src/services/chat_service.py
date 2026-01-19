"""
Chat Service for handling user interactions with the calendar assistant.

This service manages the flow of text messages and file uploads,
extracting content and coordinating with the agent runner.
"""

import logging
import uuid
from typing import Optional, Tuple

from openai import OpenAI

from ..calendar_agents import CalendarAgentRunner
from .vision_service import VisionService
from ..models import UserContext, CalendarAgentOutput

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for handling chat interactions with file processing and agent coordination.
    """
    
    def __init__(self, agent_runner: CalendarAgentRunner, vision_service: VisionService):
        """
        Initialize the Chat Service.
        
        Args:
            agent_runner: Calendar agent runner instance
            vision_service: Vision service for text extraction
        """
        self.agent_runner = agent_runner
        self.vision_service = vision_service
        logger.info("Initialized ChatService")
    
    async def process_chat(
        self,
        message: Optional[str] = None,
        file_data: Optional[bytes] = None,
        file_type: Optional[str] = None,
        file_name: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> CalendarAgentOutput:
        """
        Process a chat request with optional file upload.
        
        Args:
            message: Optional text message from user
            file_data: Optional file bytes
            file_type: Optional file MIME type
            file_name: Optional file name
            user_id: Optional user ID for session continuity
            
        Returns:
            CalendarAgentOutput: Agent output
            
        Raises:
            ValueError: If neither message nor file provided, or invalid file type
            Exception: If processing fails
        """
        try:
            # Validate that at least one input is provided
            if not message and not file_data:
                raise ValueError("Either message or file must be provided")
            
            # Generate user_id if not provided
            if user_id is None:
                user_id = str(uuid.uuid4())
                logger.info(f"Generated new user_id: {user_id}")
            
            extracted_text = None
            user_message = ""
            
            # If user only passes message (no file), call agent runner directly
            if message and not file_data:
                logger.info(f"Processing text-only message for user {user_id}")
                
                # Create user context
                user_context = UserContext(user_id=user_id)
                
                # Run agent directly with text message
                output = await self.agent_runner.run(
                    user_message=message,
                    user_context=user_context
                )
                
                return output
            
            # If file is provided, extract text and combine with message
            if file_data:
                logger.info(f"Processing file: {file_name} (type: {file_type}) for user {user_id}")
                
                # Validate file type
                allowed_types = [
                    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
                    'image/bmp', 'application/pdf'
                ]
                
                if file_type not in allowed_types:
                    raise ValueError(
                        f"Unsupported file type: {file_type}. "
                        f"Supported types: images (JPEG, PNG, GIF, WebP, BMP) and PDF"
                    )
                
                if len(file_data) == 0:
                    raise ValueError("Empty file provided")
                
                # Extract text from file using vision service
                logger.info(f"Extracting text from {file_type} file")
                extracted_text = self.vision_service.process_file(
                    file_data=file_data,
                    file_type=file_type
                )
                
                logger.info(f"Extracted {len(extracted_text)} characters from file")
                
                # Build combined message
                if message:
                    # User provided both message and file
                    user_message = f"{message}\n\n[Content extracted from {file_name}]:\n{extracted_text}"
                else:
                    # User provided only file
                    user_message = f"[Content extracted from {file_name}]:\n{extracted_text}"
            
            logger.info(f"Sending message to agent for user {user_id}: {user_message[:100]}...")
            
            # Create user context
            user_context = UserContext(user_id=user_id)
            
            # Run agent with the combined message
            output = await self.agent_runner.run(
                user_message=user_message,
                user_context=user_context
            )
            
            return output
            
        except ValueError as e:
            logger.warning(f"Validation error in chat service: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error in chat service: {str(e)}", exc_info=True)
            raise
