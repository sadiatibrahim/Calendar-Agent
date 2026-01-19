"""
Agent Runner for Calendar Assistant.

This module creates and runs the OpenAI agent with calendar and task management tools.
"""

import logging
import os
from typing import Optional, Dict, List

from agents import (
    Agent,
    FunctionTool,
    ModelSettings,
    Runner
)
from openai import OpenAI

from ..config import get_agent_instructions
from ..models import UserContext, CalendarAgentOutput
from ..tools import (
    add_event_tool,
    list_event_tool,
    delete_event_tool,
    add_task_tool,
    list_tasks_tool,
    complete_task_tool,
    delete_task_tool
)

logger = logging.getLogger(__name__)


class CalendarAgentRunner:
    """
    Calendar Assistant Agent Runner.
    
    This class initializes and manages the OpenAI agent for calendar and task management.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-5",
        temperature: float = 0.0
    ):
        """
        Initialize the Calendar Agent Runner.
        
        Args:
            api_key: OpenAI API key. If not provided, will use OPENAI_API_KEY from environment
            model: OpenAI model to use (default: gpt-5)
            temperature: Model temperature for response generation (default: 0.0)
            
        Raises:
            ValueError: If API key is not provided and not found in environment
        """
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Provide it as parameter or set OPENAI_API_KEY environment variable."
            )
        
        self.model = model
        self.temperature = temperature
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        # Initialize conversation history storage (user_id -> list of messages)
        self.conversation_histories: Dict[str, List[dict]] = {}
        
        # Get agent instructions with current date
        self.instructions = get_agent_instructions()
        
        # Import pre-defined tools from calendar_tools
        self.tools = [
            add_event_tool,
            list_event_tool,
            delete_event_tool,
            add_task_tool,
            list_tasks_tool,
            complete_task_tool,
            delete_task_tool
        ]
        
        # Create the agent with session
        self.agent = Agent(
            name="Calendar Assistant",
            instructions=self.instructions,
            tools=self.tools,
            model=self.model,
            model_settings=ModelSettings(tool_choice="required"),
            output_type=CalendarAgentOutput
        )
        
        logger.info(
            f"Initialized CalendarAgentRunner with model {self.model} and {len(self.tools)} tools"
        )
    
    async def run(self, user_message: str, user_context: Optional[UserContext] = None) -> CalendarAgentOutput:
        """
        Run the agent with a user message.
        
        Args:
            user_message: The user's message/request
            user_context: Optional user context. If not provided, a new one will be generated
            
        Returns:
            CalendarAgentOutput: The agent's response with message and user_id
            
        Raises:
            Exception: If agent execution fails
        """
        try:
            # Create or use existing user context
            if user_context is None:
                user_context = UserContext()
            
            logger.info(f"Running agent for user {user_context.user_id} with message: {user_message[:100]}...")
            
            # Get existing history or initialize empty list
            if user_context.user_id not in self.conversation_histories:
                self.conversation_histories[user_context.user_id] = []
            
            # Build input list: previous history + new user message
            input_list = self.conversation_histories[user_context.user_id] + [{"role": "user", "content": user_message}]
            
            # Run the agent with input list and context
            result = await Runner.run(
                starting_agent=self.agent,
                input=input_list,
                context=user_context.model_dump()
            )
            
            # Update the stored history with the full conversation from this result
            self.conversation_histories[user_context.user_id] = result.to_input_list()
            
            # Get the final output from result
            output = result.final_output
            
            # Ensure user_id is set in the output
            if output.user_id is None:
                output.user_id = user_context.user_id
            
            logger.info(f"Agent response generated for user {user_context.user_id}")
            
            return output
            
        except Exception as e:
            logger.error(f"Error running agent: {str(e)}", exc_info=True)
            raise Exception(f"Agent execution failed: {str(e)}")
    
    def clear_history(self, user_id: str):
        """
        Clear conversation history for a specific user.
        
        Args:
            user_id: The user's ID
        """
        if user_id in self.conversation_histories:
            del self.conversation_histories[user_id]
            logger.info(f"Cleared conversation history for user {user_id}")
    
    def get_history(self, user_id: str) -> List[dict]:
        """
        Get conversation history for a specific user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List[dict]: List of messages in the conversation history
        """
        return self.conversation_histories.get(user_id, [])

