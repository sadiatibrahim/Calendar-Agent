"""
Calendar Tools for OpenAI Agent.

This module provides tool functions for calendar operations that can be used
by the OpenAI agent. Each tool wraps Google Calendar API operations with
clear descriptions for agent understanding.
"""

import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from agents import FunctionTool, RunContextWrapper
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from ..services import GoogleCalendarClient
from ..models import (
    AddEventRequest,
    ListEventsRequest,
    DeleteEventRequest,
    AddTaskRequest,
    ListTasksRequest,
    UpdateTaskRequest,
    DeleteTaskRequest,
    ToolResponse
)
from ..utils.exceptions import (
    CalendarAPIError,
    EventNotFoundError,
    CalendarAuthenticationError
)


logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/tasks'
]

# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_calendar_credentials() -> Credentials:
    """
    Get or refresh Google Calendar API credentials.
    
    Returns:
        Credentials: Valid Google OAuth2 credentials
        
    Raises:
        CalendarAuthenticationError: If authentication fails
    """
    creds = None
    # Store credentials in the backend root directory
    token_file = os.path.join(BASE_DIR, 'token.json')
    credentials_file = os.path.join(BASE_DIR, 'credentials.json')
    
    try:
        # Load existing token if available
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        # Refresh or get new credentials if needed
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_file):
                    raise CalendarAuthenticationError(
                        f"Credentials file not found: {credentials_file}. "
                        "Please download it from Google Cloud Console."
                    )
                
                logger.info("Starting OAuth flow for new credentials")
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
            logger.info("Credentials saved successfully")
        
        return creds
        
    except Exception as e:
        logger.error(f"Failed to get calendar credentials: {e}")
        raise CalendarAuthenticationError(
            f"Failed to authenticate with Google Calendar: {str(e)}"
        ) from e


# Initialize Google Calendar client at module level
try:
    logger.info("Initializing Google Calendar client")
    credentials = get_calendar_credentials()
    calendar_client = GoogleCalendarClient(credentials)
    logger.info("Google Calendar client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize calendar client: {e}")
    calendar_client = None
    logger.warning("Calendar tools will not function without valid credentials")


async def add_calendar_event(
    ctx: RunContextWrapper[Any],
    args: str
) -> str:
    """
    Add a new event or task to Google Calendar.
    
    Use this tool when the user wants to create, schedule, or add a new event,
    meeting, appointment, or task to their calendar. This includes setting up
    reminders, meetings, or any time-based activities.
    
    Args:
        request: AddEventRequest object containing event details (summary, start_time, 
                 end_time, description, location, attendees, timezone)
        calendar_client: GoogleCalendarClient instance for API calls
        
    Returns:
        Dictionary containing:
            - success: True if event was created
            - event_id: ID of the created event
            - summary: Event title
            - start: Event start time
            - message: Success message
            
    Example:
        request = AddEventRequest(
            summary="Project Review",
            start_time="2026-01-20T14:00:00",
            end_time="2026-01-20T15:00:00",
            description="Quarterly project review meeting"
        )
        add_calendar_event(request, calendar_client)
    """
    try:
        if calendar_client is None:
            raise CalendarAuthenticationError(
                "Calendar client not initialized. Please check credentials."
            )
        
        logger.info(f"Agent tool: Adding calendar even")
        
        # Call calendar API
        parsed_args = AddEventRequest.model_validate_json(args)
        event = calendar_client.add_event(parsed_args)
        
        logger.info(f"Event created successfully: {event.get('id')}")
        
        response = ToolResponse(
            success=True,
            message=f"Successfully added event '{parsed_args.summary}' to calendar",
            data={
                "event_id": event.get('id'),
                "summary": event.get('summary'),
                "start": event.get('start', {}).get('dateTime')
            }
        )
        return response.model_dump_json()
        
    except Exception as e:
        logger.error(f"Failed to add event via agent tool: {e}")
        response = ToolResponse(
            success=False,
            message=f"Failed to add event: {str(e)}",
            error=str(e)
        )
        return response.model_dump_json()


async def list_calendar_events(
    ctx: RunContextWrapper[Any],
    args: str
) -> str:
    """
    List and view upcoming events from Google Calendar.
    
    Use this tool when the user wants to see their schedule, check upcoming events,
    view their calendar, find out what's planned, or ask "what's on my calendar".
    By default, shows the next 10 upcoming events starting from now.
    
    Args:
        request: ListEventsRequest object containing query parameters (max_results, 
                 time_min, time_max, order_by, single_events)
        calendar_client: GoogleCalendarClient instance for API calls
        
    Returns:
        Dictionary containing:
            - success: True if events were retrieved
            - count: Number of events found
            - events: List of event dictionaries with id, summary, start, end, description
            - message: Summary message
            
    Example:
        request = ListEventsRequest(max_results=5)
        list_calendar_events(request, calendar_client)
        
        request = ListEventsRequest(
            time_min="2026-01-20T00:00:00Z",
            time_max="2026-01-27T23:59:59Z"
        )
        list_calendar_events(request, calendar_client)
    """
    try:
        if calendar_client is None:
            raise CalendarAuthenticationError(
                "Calendar client not initialized. Please check credentials."
            )
        
        logger.info(f"Agent tool: Listing calendar events")
        
        # Call calendar API
        parsed_args = ListEventsRequest.model_validate_json(args)
        events = calendar_client.list_events(parsed_args)
        
        # Format events for agent
        formatted_events = []
        for event in events:
            formatted_events.append({
                "id": event.get('id'),
                "summary": event.get('summary', 'No Title'),
                "start": event.get('start', {}).get('dateTime') or event.get('start', {}).get('date'),
                "end": event.get('end', {}).get('dateTime') or event.get('end', {}).get('date'),
                "description": event.get('description', ''),
                "location": event.get('location', '')
            })
        
        logger.info(f"Retrieved {len(formatted_events)} events")
        
        if len(formatted_events) == 0:
            message = "No upcoming events found on the calendar"
        else:
            message = f"Found {len(formatted_events)} upcoming event(s)"
        
        response = ToolResponse(
            success=True,
            message=message,
            data={
                "count": len(formatted_events),
                "events": formatted_events
            }
        )
        return response.model_dump_json()
        
    except Exception as e:
        logger.error(f"Failed to list events via agent tool: {e}")
        response = ToolResponse(
            success=False,
            message=f"Failed to retrieve events: {str(e)}",
            error=str(e)
        )
        return response.model_dump_json()


async def delete_calendar_event(
    ctx: RunContextWrapper[Any],
    args: str
) -> str:
    """
    Delete or remove an event from Google Calendar.
    
    Use this tool when the user wants to delete, remove, cancel, or clear an event
    from their calendar. Requires the event ID which can be obtained from list_calendar_events.
    
    Args:
        request: DeleteEventRequest object containing event_id
        calendar_client: GoogleCalendarClient instance for API calls
        
    Returns:
        Dictionary containing:
            - success: True if event was deleted
            - event_id: ID of the deleted event
            - message: Success or error message
            
    Example:
        request = DeleteEventRequest(event_id="abc123xyz")
        delete_calendar_event(request, calendar_client)
        
    Note:
        You must first use list_calendar_events to find the event_id before deleting.
    """
    try:
        if calendar_client is None:
            raise CalendarAuthenticationError(
                "Calendar client not initialized. Please check credentials."
            )
        
        logger.info(f"Agent tool: Deleting calendar event")
        parsed_args = DeleteEventRequest.model_validate_json(args)
        
        # Call calendar API
        success = calendar_client.delete_event(parsed_args)
        
        logger.info(f"Event deleted successfully: {parsed_args.event_id}")
        
        response = ToolResponse(
            success=True,
            message=f"Successfully deleted event from calendar",
            data={"event_id": parsed_args.event_id}
        )
        return response.model_dump_json()
        
    except EventNotFoundError as e:
        logger.warning(f"Event not found:")
        response = ToolResponse(
            success=False,
            message=f"Event does not exist or has already been deleted",
            error="Event not found"
        )
        return response.model_dump_json()
    except Exception as e:
        logger.error(f"Failed to delete event via agent tool: {e}")
        response = ToolResponse(
            success=False,
            message=f"Failed to delete event: {str(e)}",
            error=str(e)
        )
        return response.model_dump_json()


# ===== Google Tasks Tool Functions =====

async def add_task(
    ctx: RunContextWrapper[Any],
    args: str
) -> str:
    """
    Add a new task to Google Tasks (to-do list).
    
    Use this tool when the user wants to create a to-do item, task, reminder,
    or something they need to complete. Tasks are different from calendar events -
    they have due dates (not start/end times) and can be checked off as completed.
    
    Args:
        ctx: Run context wrapper
        args: JSON string with AddTaskRequest (title, notes, due)
        
    Returns:
        JSON string with ToolResponse containing task details
        
    Example:
        To add "Buy groceries" task:
        args = {"title": "Buy groceries", "notes": "Milk, bread, eggs", "due": "2026-01-20T00:00:00Z"}
    """
    try:
        if calendar_client is None:
            raise CalendarAuthenticationError(
                "Calendar client not initialized. Please check credentials."
            )
        
        logger.info("Agent tool: Adding task")
        
        parsed_args = AddTaskRequest.model_validate_json(args)
        task = calendar_client.add_task(parsed_args)
        
        logger.info(f"Task created successfully: {task.get('id')}")
        
        response = ToolResponse(
            success=True,
            message=f"Successfully added task '{parsed_args.title}' to your to-do list",
            data={
                "task_id": task.get('id'),
                "title": task.get('title'),
                "due": task.get('due'),
                "status": task.get('status')
            }
        )
        return response.model_dump_json()
        
    except Exception as e:
        logger.error(f"Failed to add task via agent tool: {e}")
        response = ToolResponse(
            success=False,
            message=f"Failed to add task: {str(e)}",
            error=str(e)
        )
        return response.model_dump_json()


async def list_tasks(
    ctx: RunContextWrapper[Any],
    args: str
) -> str:
    """
    List tasks from Google Tasks (to-do list).
    
    Use this tool when the user wants to see their tasks, to-do items, or things
    they need to complete. By default, shows incomplete tasks only.
    
    Args:
        ctx: Run context wrapper
        args: JSON string with ListTasksRequest (max_results, show_completed, show_hidden)
        
    Returns:
        JSON string with ToolResponse containing list of tasks
        
    Example:
        To see all tasks including completed:
        args = {"max_results": 20, "show_completed": true}
    """
    try:
        if calendar_client is None:
            raise CalendarAuthenticationError(
                "Calendar client not initialized. Please check credentials."
            )
        
        logger.info("Agent tool: Listing tasks")
        
        parsed_args = ListTasksRequest.model_validate_json(args)
        tasks = calendar_client.list_tasks(parsed_args)
        
        # Format tasks for agent
        formatted_tasks = []
        for task in tasks:
            formatted_tasks.append({
                "id": task.get('id'),
                "title": task.get('title'),
                "status": task.get('status'),
                "due": task.get('due'),
                "notes": task.get('notes', ''),
                "completed": task.get('completed')
            })
        
        logger.info(f"Retrieved {len(formatted_tasks)} tasks")
        
        if len(formatted_tasks) == 0:
            message = "No tasks found in your to-do list"
        else:
            message = f"Found {len(formatted_tasks)} task(s) in your to-do list"
        
        response = ToolResponse(
            success=True,
            message=message,
            data={
                "count": len(formatted_tasks),
                "tasks": formatted_tasks
            }
        )
        return response.model_dump_json()
        
    except Exception as e:
        logger.error(f"Failed to list tasks via agent tool: {e}")
        response = ToolResponse(
            success=False,
            message=f"Failed to retrieve tasks: {str(e)}",
            error=str(e)
        )
        return response.model_dump_json()


async def complete_task(
    ctx: RunContextWrapper[Any],
    args: str
) -> str:
    """
    Mark a task as completed or not completed in Google Tasks.
    
    Use this tool when the user wants to check off a task, mark it done,
    or uncomplete a task. Requires the task ID which can be obtained from list_tasks.
    
    Args:
        ctx: Run context wrapper
        args: JSON string with UpdateTaskRequest (task_id, completed)
        
    Returns:
        JSON string with ToolResponse
        
    Example:
        To mark task as done:
        args = {"task_id": "abc123", "completed": true}
    """
    try:
        if calendar_client is None:
            raise CalendarAuthenticationError(
                "Calendar client not initialized. Please check credentials."
            )
        
        logger.info("Agent tool: Updating task completion status")
        parsed_args = UpdateTaskRequest.model_validate_json(args)
        
        task = calendar_client.update_task(parsed_args)
        
        status_text = "completed" if parsed_args.completed else "marked as incomplete"
        logger.info(f"Task {status_text}: {parsed_args.task_id}")
        
        response = ToolResponse(
            success=True,
            message=f"Successfully {status_text} task",
            data={
                "task_id": task.get('id'),
                "title": task.get('title'),
                "status": task.get('status')
            }
        )
        return response.model_dump_json()
        
    except EventNotFoundError as e:
        logger.warning("Task not found")
        response = ToolResponse(
            success=False,
            message="Task does not exist or has already been deleted",
            error="Task not found"
        )
        return response.model_dump_json()
    except Exception as e:
        logger.error(f"Failed to update task via agent tool: {e}")
        response = ToolResponse(
            success=False,
            message=f"Failed to update task: {str(e)}",
            error=str(e)
        )
        return response.model_dump_json()


async def delete_task(
    ctx: RunContextWrapper[Any],
    args: str
) -> str:
    """
    Delete a task from Google Tasks.
    
    Use this tool when the user wants to delete or remove a task from their to-do list.
    Requires the task ID which can be obtained from list_tasks.
    
    Args:
        ctx: Run context wrapper
        args: JSON string with DeleteTaskRequest (task_id)
        
    Returns:
        JSON string with ToolResponse
        
    Example:
        args = {"task_id": "abc123"}
    """
    try:
        if calendar_client is None:
            raise CalendarAuthenticationError(
                "Calendar client not initialized. Please check credentials."
            )
        
        logger.info("Agent tool: Deleting task")
        parsed_args = DeleteTaskRequest.model_validate_json(args)
        
        success = calendar_client.delete_task(parsed_args)
        
        logger.info(f"Task deleted successfully: {parsed_args.task_id}")
        
        response = ToolResponse(
            success=True,
            message="Successfully deleted task from your to-do list",
            data={"task_id": parsed_args.task_id}
        )
        return response.model_dump_json()
        
    except EventNotFoundError as e:
        logger.warning("Task not found")
        response = ToolResponse(
            success=False,
            message="Task does not exist or has already been deleted",
            error="Task not found"
        )
        return response.model_dump_json()
    except Exception as e:
        logger.error(f"Failed to delete task via agent tool: {e}")
        response = ToolResponse(
            success=False,
            message=f"Failed to delete task: {str(e)}",
            error=str(e)
        )
        return response.model_dump_json()

add_event_tool = FunctionTool(
    name="add_calendar_event",
    description=(
        "Add a new event to the client's Google Calendar. "
        "Use this for scheduled meetings, appointments, or time-specific activities. "
        "Requires: summary (event title), start_time, end_time (RFC3339 format), and description. "
        "Optional: location, attendees (list of emails), timezone."
    ),
    params_json_schema=AddEventRequest.model_json_schema(),
    on_invoke_tool=add_calendar_event)

list_event_tool = FunctionTool(
    name="list_calendar_events",
    description=(
        "Retrieve upcoming events from the client's Google Calendar. "
        "Use this to show scheduled meetings, appointments, or time-specific activities. "
        "Optional: max_results (default 10), time_min, time_max (RFC3339 format), order_by."
    ),
    params_json_schema=ListEventsRequest.model_json_schema(),
    on_invoke_tool=list_calendar_events)

delete_event_tool = FunctionTool(
    name="delete_calendar_event",
    description=(
        "Delete an event from the client's Google Calendar. "
        "Requires: event_id (get this from list_calendar_events first)."
    ),
    params_json_schema=DeleteEventRequest.model_json_schema(),
    on_invoke_tool=delete_calendar_event
)

add_task_tool = FunctionTool(
    name="add_task",
    description=(
        "Add a new task to the client's Google Tasks. "
        "Use this for to-do items, assignments, deadlines without specific times. "
        "Requires: title (task name). "
        "Optional: notes (details), due (RFC3339 format date)."
    ),
    params_json_schema=AddTaskRequest.model_json_schema(),
    on_invoke_tool=add_task)

list_tasks_tool = FunctionTool(
    name="list_tasks",
    description=(
        "Retrieve tasks from the client's Google Tasks. "
        "Use this to show to-do items and their completion status. "
        "Optional: max_results (default 10), show_completed (default false), show_hidden (default false)."
    ),
    params_json_schema=ListTasksRequest.model_json_schema(),
    on_invoke_tool=list_tasks)

complete_task_tool = FunctionTool(
    name="complete_task",
    description=(
        "Mark a task as completed or revert to needs action. "
        "Requires: task_id (get this from list_tasks first), status ('completed' or 'needsAction')."
    ),
    params_json_schema=UpdateTaskRequest.model_json_schema(),
    on_invoke_tool=complete_task)

delete_task_tool = FunctionTool(
    name="delete_task",
    description=(
        "Delete a task from the client's Google Tasks. "
        "Requires: task_id (get this from list_tasks first)."
    ),
    params_json_schema=DeleteTaskRequest.model_json_schema(),
    on_invoke_tool=delete_task
)