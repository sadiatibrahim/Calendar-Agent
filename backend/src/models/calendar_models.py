"""Pydantic models for calendar operations."""

from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import uuid


class AddEventRequest(BaseModel):
    """Request model for adding a calendar event."""
    
    summary: str = Field(..., min_length=1, max_length=200, description="Event title/summary")
    start_time: str = Field(..., description="Start time in ISO 8601 format")
    end_time: str = Field(..., description="End time in ISO 8601 format")
    description: str = Field(..., min_length=1, description="Event description")
    location: Optional[str] = Field(None, description="Event location")
    attendees: Optional[List[str]] = Field(None, description="List of attendee email addresses")
    timezone: str = Field(default='UTC', description="Timezone for the event")
    
    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_datetime_format(cls, v: str) -> str:
        """Validate datetime is in ISO 8601 format."""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError(f"Invalid datetime format: {v}. Must be ISO 8601 format")
    
    @field_validator('attendees')
    @classmethod
    def validate_attendees(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate attendee email addresses."""
        if v is not None:
            for email in v:
                if '@' not in email:
                    raise ValueError(f"Invalid email address: {email}")
        return v


class ListEventsRequest(BaseModel):
    """Request model for listing calendar events."""
    
    max_results: int = Field(default=10, ge=1, le=250, description="Maximum number of events to return")
    time_min: Optional[str] = Field(None, description="Lower bound (RFC3339 timestamp)")
    time_max: Optional[str] = Field(None, description="Upper bound (RFC3339 timestamp)")
    order_by: str = Field(default='startTime', description="Order of events")
    single_events: bool = Field(default=True, description="Expand recurring events into instances")
    
    @field_validator('order_by')
    @classmethod
    def validate_order_by(cls, v: str) -> str:
        """Validate order_by field."""
        allowed_values = ['startTime', 'updated']
        if v not in allowed_values:
            raise ValueError(f"order_by must be one of {allowed_values}")
        return v


class GetEventRequest(BaseModel):
    """Request model for getting a specific event."""
    
    event_id: str = Field(..., min_length=1, description="ID of the event to retrieve")


class DeleteEventRequest(BaseModel):
    """Request model for deleting a specific event."""
    
    event_id: str = Field(..., min_length=1, description="ID of the event to delete")


class AddTaskRequest(BaseModel):
    """Request model for adding a task to Google Tasks."""
    
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    notes: Optional[str] = Field(None, description="Task notes/description")
    due: Optional[str] = Field(None, description="Due date in RFC 3339 format (e.g., '2026-01-20T00:00:00Z')")
    
    @field_validator('due')
    @classmethod
    def validate_due_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate due date format."""
        if v is not None:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
                return v
            except ValueError:
                raise ValueError(f"Invalid due date format: {v}. Must be RFC 3339 format")
        return v


class ListTasksRequest(BaseModel):
    """Request model for listing tasks."""
    
    max_results: int = Field(default=100, ge=1, le=100, description="Maximum number of tasks to return")
    show_completed: bool = Field(default=False, description="Whether to show completed tasks")
    show_hidden: bool = Field(default=False, description="Whether to show hidden tasks")


class UpdateTaskRequest(BaseModel):
    """Request model for updating/completing a task."""
    
    task_id: str = Field(..., min_length=1, description="ID of the task to update")
    completed: bool = Field(..., description="Mark task as completed or not")


class DeleteTaskRequest(BaseModel):
    """Request model for deleting a task."""
    
    task_id: str = Field(..., min_length=1, description="ID of the task to delete")


class CalendarEvent(BaseModel):
    """Model for a calendar event."""
    
    id: str = Field(..., description="Event ID")
    summary: str = Field(..., description="Event title")
    start: str = Field(..., description="Start time")
    end: str = Field(..., description="End time")
    description: Optional[str] = Field(None, description="Event description")
    location: Optional[str] = Field(None, description="Event location")


class ToolResponse(BaseModel):
    """Response model for all calendar tool operations."""
    
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Human-readable message about the result")
    error: Optional[str] = Field(None, description="Error message if operation failed")
    data: Optional[Any] = Field(None, description="Additional data for successful operations")


class UserContext(BaseModel):
    """User context for agent session."""
    
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique user identifier")
    

class CalendarAgentOutput(BaseModel):
    """Output model for calendar agent responses."""
    
    message: str = Field(..., description="The agent's response message")
    user_id: Optional[str] = Field(None, description="User identifier for the session")
    error: Optional[str] = Field(None, description="Error message if the agent encountered an error")

