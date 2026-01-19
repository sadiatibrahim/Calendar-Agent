"""
Google Calendar API Client.

This module provides a client for interacting with Google Calendar API
and Google Tasks API with proper error handling, retry logic, and reusable methods.
"""

import logging
import time
from typing import List, Dict, Any
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..utils.exceptions import (
    CalendarAuthenticationError,
    CalendarAPIError,
    EventNotFoundError,
    EventValidationError
)
from ..models import (
    AddEventRequest,
    ListEventsRequest,
    GetEventRequest,
    DeleteEventRequest,
    AddTaskRequest,
    ListTasksRequest,
    UpdateTaskRequest,
    DeleteTaskRequest
)


logger = logging.getLogger(__name__)


class GoogleCalendarClient:
    """
    Client for interacting with Google Calendar API and Google Tasks API.
    
    Provides methods to list, add, and delete calendar events and tasks with
    proper error handling and retry logic.
    """
    
    def __init__(self, credentials: Credentials, calendar_id: str = 'primary'):
        """
        Initialize Google Calendar and Tasks client.
        
        Args:
            credentials: Google OAuth2 credentials
            calendar_id: Calendar ID to use (default: 'primary')
        """
        self.credentials = credentials
        self.calendar_id = calendar_id
        self.calendar_service = None
        self.tasks_service = None
        self.max_retries = 3
        self.base_retry_delay = 1  # seconds
        
        self._initialize_service()
    
    def _initialize_service(self) -> None:
        """
        Initialize Google Calendar and Tasks services with credential refresh.
        
        Raises:
            CalendarAuthenticationError: If authentication fails
        """
        try:
            # Refresh credentials if expired
            if self.credentials.expired and self.credentials.refresh_token:
                logger.info("Refreshing expired credentials")
                self.credentials.refresh(Request())
            
            self.calendar_service = build('calendar', 'v3', credentials=self.credentials)
            self.tasks_service = build('tasks', 'v1', credentials=self.credentials)
            logger.info("Google Calendar and Tasks services initialized successfully")
            
        except RefreshError as e:
            logger.error(f"Failed to refresh credentials: {e}")
            raise CalendarAuthenticationError(
                "Failed to refresh authentication credentials"
            ) from e
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise CalendarAuthenticationError(
                "Failed to initialize Google Calendar/Tasks services"
            ) from e
    
    def _execute_with_retry(self, request, operation_name: str) -> Any:
        """
        Execute API request with exponential backoff retry logic.
        
        Args:
            request: Google API request object to execute
            operation_name: Name of operation for logging
            
        Returns:
            API response
            
        Raises:
            CalendarAPIError: If request fails after retries
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Executing {operation_name}, attempt {attempt + 1}")
                response = request.execute()
                logger.info(f"{operation_name} completed successfully")
                return response
                
            except HttpError as e:
                last_error = e
                status_code = e.resp.status
                
                # Retry on rate limit (429) or server errors (5xx)
                if status_code in [429, 500, 503]:
                    if attempt < self.max_retries - 1:
                        delay = self.base_retry_delay * (2 ** attempt)
                        logger.warning(
                            f"{operation_name} failed with status {status_code}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                        continue
                
                # Don't retry on client errors (4xx except 429)
                if 400 <= status_code < 500 and status_code != 429:
                    logger.error(f"{operation_name} failed: {e}")
                    if status_code == 404:
                        raise EventNotFoundError(
                            f"Event not found: {e.error_details}"
                        ) from e
                    raise CalendarAPIError(
                        f"Calendar API request failed: {e.error_details}"
                    ) from e
                
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error in {operation_name}: {e}")
                break
        
        # All retries exhausted
        logger.error(f"{operation_name} failed after {self.max_retries} attempts")
        raise CalendarAPIError(
            f"Calendar API operation failed: {str(last_error)}"
        ) from last_error
    
    def list_events(self, request: ListEventsRequest) -> List[Dict[str, Any]]:
        """
        List calendar events.
        
        Args:
            request: ListEventsRequest object containing query parameters
            
        Returns:
            List of event dictionaries
            
        Raises:
            CalendarAPIError: If API call fails
        """
        try:
            logger.info(
                f"Listing events: max={request.max_results}, "
                f"time_min={request.time_min}, time_max={request.time_max}"
            )
            
            # Use current time as default if time_min not provided
            time_min = request.time_min
            if time_min is None:
                time_min = datetime.utcnow().isoformat() + 'Z'
            
            list_request = self.calendar_service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=request.time_max,
                maxResults=request.max_results,
                singleEvents=request.single_events,
                orderBy=request.order_by
            )
            
            response = self._execute_with_retry(list_request, "List events")
            events = response.get('items', [])
            
            logger.info(f"Retrieved {len(events)} events")
            return events
            
        except Exception as e:
            logger.error(f"Failed to list events: {e}")
            raise CalendarAPIError(f"Failed to list calendar events: {str(e)}") from e
    
    def add_event(self, request: AddEventRequest) -> Dict[str, Any]:
        """
        Add a new event to the calendar.
        
        Args:
            request: AddEventRequest object containing event details
            
        Returns:
            Created event details with ID
            
        Raises:
            EventValidationError: If event data is invalid
            CalendarAPIError: If API call fails
        """
        try:
            logger.info(f"Adding event: {request.summary}")
            
            # Build event data
            event_data = {
                'summary': request.summary,
                'start': {
                    'dateTime': request.start_time,
                    'timeZone': request.timezone,
                },
                'end': {
                    'dateTime': request.end_time,
                    'timeZone': request.timezone,
                },
                'description': request.description
            }
            
            if request.location:
                event_data['location'] = request.location
            
            if request.attendees:
                event_data['attendees'] = [{'email': email} for email in request.attendees]
            
            insert_request = self.calendar_service.events().insert(
                calendarId=self.calendar_id,
                body=event_data
            )
            
            event = self._execute_with_retry(insert_request, "Add event")
            
            logger.info(f"Event created successfully: {event.get('id')}")
            return event
            
        except EventValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to add event: {e}")
            raise CalendarAPIError(f"Failed to add calendar event: {str(e)}") from e
    
    def delete_event(self, request: DeleteEventRequest) -> bool:
        """
        Delete an event from the calendar.
        
        Args:
            request: DeleteEventRequest object containing event ID
            
        Returns:
            True if deletion successful
            
        Raises:
            EventNotFoundError: If event doesn't exist
            CalendarAPIError: If API call fails
        """
        try:
            logger.info(f"Deleting event: {request.event_id}")
            
            delete_request = self.calendar_service.events().delete(
                calendarId=self.calendar_id,
                eventId=request.event_id
            )
            
            self._execute_with_retry(delete_request, "Delete event")
            
            logger.info(f"Event deleted successfully: {request.event_id}")
            return True
            
        except EventNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete event: {e}")
            raise CalendarAPIError(f"Failed to delete calendar event: {str(e)}") from e
    
    def get_event(self, request: GetEventRequest) -> Dict[str, Any]:
        """
        Get details of a specific event.
        
        Args:
            request: GetEventRequest object containing event ID
            
        Returns:
            Event details dictionary
            
        Raises:
            EventNotFoundError: If event doesn't exist
            CalendarAPIError: If API call fails
        """
        try:
            logger.info(f"Getting event: {request.event_id}")
            
            get_request = self.calendar_service.events().get(
                calendarId=self.calendar_id,
                eventId=request.event_id
            )
            
            event = self._execute_with_retry(get_request, "Get event")
            
            logger.info(f"Event retrieved successfully: {request.event_id}")
            return event
            
        except EventNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get event: {e}")
            raise CalendarAPIError(f"Failed to retrieve calendar event: {str(e)}") from e
    
    # ===== Google Tasks Methods =====
    
    def add_task(self, request: AddTaskRequest, tasklist: str = '@default') -> Dict[str, Any]:
        """
        Add a new task to Google Tasks.
        
        Args:
            request: AddTaskRequest object containing task details
            tasklist: Task list ID (default: '@default' for primary list)
            
        Returns:
            Created task details with ID
            
        Raises:
            CalendarAPIError: If API call fails
        """
        try:
            logger.info(f"Adding task: {request.title}")
            
            # Build task data
            task_data = {
                'title': request.title
            }
            
            if request.notes:
                task_data['notes'] = request.notes
            
            if request.due:
                task_data['due'] = request.due
            
            insert_request = self.tasks_service.tasks().insert(
                tasklist=tasklist,
                body=task_data
            )
            
            task = self._execute_with_retry(insert_request, "Add task")
            
            logger.info(f"Task created successfully: {task.get('id')}")
            return task
            
        except Exception as e:
            logger.error(f"Failed to add task: {e}")
            raise CalendarAPIError(f"Failed to add task: {str(e)}") from e
    
    def list_tasks(self, request: ListTasksRequest, tasklist: str = '@default') -> List[Dict[str, Any]]:
        """
        List tasks from Google Tasks.
        
        Args:
            request: ListTasksRequest object containing query parameters
            tasklist: Task list ID (default: '@default' for primary list)
            
        Returns:
            List of task dictionaries
            
        Raises:
            CalendarAPIError: If API call fails
        """
        try:
            logger.info(f"Listing tasks: max={request.max_results}")
            
            list_request = self.tasks_service.tasks().list(
                tasklist=tasklist,
                maxResults=request.max_results,
                showCompleted=request.show_completed,
                showHidden=request.show_hidden
            )
            
            response = self._execute_with_retry(list_request, "List tasks")
            tasks = response.get('items', [])
            
            logger.info(f"Retrieved {len(tasks)} tasks")
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            raise CalendarAPIError(f"Failed to list tasks: {str(e)}") from e
    
    def update_task(self, request: UpdateTaskRequest, tasklist: str = '@default') -> Dict[str, Any]:
        """
        Update a task (mark as completed or not completed).
        
        Args:
            request: UpdateTaskRequest object containing task ID and completion status
            tasklist: Task list ID (default: '@default' for primary list)
            
        Returns:
            Updated task details
            
        Raises:
            EventNotFoundError: If task doesn't exist
            CalendarAPIError: If API call fails
        """
        try:
            logger.info(f"Updating task: {request.task_id}, completed={request.completed}")
            
            # Get current task
            get_request = self.tasks_service.tasks().get(
                tasklist=tasklist,
                task=request.task_id
            )
            task = self._execute_with_retry(get_request, "Get task")
            
            # Update status
            if request.completed:
                task['status'] = 'completed'
            else:
                task['status'] = 'needsAction'
                task.pop('completed', None)  # Remove completed timestamp
            
            # Update task
            update_request = self.tasks_service.tasks().update(
                tasklist=tasklist,
                task=request.task_id,
                body=task
            )
            
            updated_task = self._execute_with_retry(update_request, "Update task")
            
            logger.info(f"Task updated successfully: {request.task_id}")
            return updated_task
            
        except HttpError as e:
            if e.resp.status == 404:
                raise EventNotFoundError(f"Task not found: {request.task_id}") from e
            raise CalendarAPIError(f"Failed to update task: {str(e)}") from e
        except Exception as e:
            logger.error(f"Failed to update task: {e}")
            raise CalendarAPIError(f"Failed to update task: {str(e)}") from e
    
    def delete_task(self, request: DeleteTaskRequest, tasklist: str = '@default') -> bool:
        """
        Delete a task from Google Tasks.
        
        Args:
            request: DeleteTaskRequest object containing task ID
            tasklist: Task list ID (default: '@default' for primary list)
            
        Returns:
            True if deletion successful
            
        Raises:
            EventNotFoundError: If task doesn't exist
            CalendarAPIError: If API call fails
        """
        try:
            logger.info(f"Deleting task: {request.task_id}")
            
            delete_request = self.tasks_service.tasks().delete(
                tasklist=tasklist,
                task=request.task_id
            )
            
            self._execute_with_retry(delete_request, "Delete task")
            
            logger.info(f"Task deleted successfully: {request.task_id}")
            return True
            
        except HttpError as e:
            if e.resp.status == 404:
                raise EventNotFoundError(f"Task not found: {request.task_id}") from e
            raise CalendarAPIError(f"Failed to delete task: {str(e)}") from e
        except Exception as e:
            logger.error(f"Failed to delete task: {e}")
            raise CalendarAPIError(f"Failed to delete task: {str(e)}") from e
