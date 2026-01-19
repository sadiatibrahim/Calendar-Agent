"""Custom exceptions for Calendar Assistant application."""


class CalendarAssistantError(Exception):
    """Base exception for all Calendar Assistant errors."""
    pass


class GoogleCalendarError(CalendarAssistantError):
    """Base exception for Google Calendar related errors."""
    pass


class CalendarAuthenticationError(GoogleCalendarError):
    """Raised when authentication with Google Calendar fails."""
    pass


class CalendarAPIError(GoogleCalendarError):
    """Raised when Google Calendar API calls fail."""
    pass


class EventNotFoundError(GoogleCalendarError):
    """Raised when a calendar event is not found."""
    pass


class EventValidationError(GoogleCalendarError):
    """Raised when event data validation fails."""
    pass


class VisionServiceError(CalendarAssistantError):
    """Raised when OpenAI Vision service encounters errors."""
    pass


class AgentExecutionError(CalendarAssistantError):
    """Raised when OpenAI Agent execution fails."""
    pass
