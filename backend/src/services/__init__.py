"""Service modules for business logic."""

from .google_calendar_client import GoogleCalendarClient
from .vision_service import VisionService

# Import ChatService lazily to avoid circular import
# (ChatService -> CalendarAgentRunner -> tools -> GoogleCalendarClient)
def __getattr__(name):
    if name == 'ChatService':
        from .chat_service import ChatService
        return ChatService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ['GoogleCalendarClient', 'VisionService', 'ChatService']
