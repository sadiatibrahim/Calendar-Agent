# Calendar Assistant - AI Agent Programming Guidelines

## Project Overview
Full-stack web application integrating OpenAI Vision + Agent SDK with Google Calendar API. TypeScript frontend processes user inputs (text, screenshots, documents), Python backend extracts content via OpenAI Vision, then orchestrates calendar operations through an OpenAI agent with custom tools.

## Role: Senior Software Engineer
Write production-ready, maintainable code following enterprise patterns. Prioritize code quality, error handling, and reusability.

---

## Architecture

### Frontend (TypeScript)
- **React** with functional components and hooks
- Strict TypeScript mode enabled
- Component-driven development with reusable UI components
- API client in `services/` layer
- Custom hooks for shared logic in `hooks/`

### Backend (Python)
- **Layered architecture**: API → Services → Integrations
- `agents/`: OpenAI agent implementation with tool definitions
- `services/`: Business logic (vision extraction, calendar operations)
- `tools/`: Agent tool functions (add_event, delete_event, list_events)
- `integrations/`: External API clients (OpenAI, Google Calendar)
- `models/`: Pydantic models for validation
- `utils/`: Helper functions and custom exceptions

---

## Exception Handling (Required)

### Python
```python
# Always use specific exceptions with context
try:
    result = await calendar_service.add_event(event_data)
except GoogleAPIError as e:
    logger.error(f"Calendar API failed: {e}", extra={"event": event_data})
    raise CalendarServiceError(f"Failed to add event: {str(e)}") from e
except ValidationError as e:
    logger.warning(f"Invalid event data: {e}")
    raise
except Exception as e:
    logger.critical(f"Unexpected error: {e}", exc_info=True)
    raise
finally:
    # Cleanup operations
    await cleanup_resources()
```

**Rules:**
- Catch specific exceptions first, generic last
- Log with context (user ID, request ID, data)
- Never use bare `except:`
- Use `raise ... from e` to preserve stack traces
- Implement retry logic with exponential backoff for API calls

### TypeScript
```typescript
try {
  const response = await apiClient.uploadFile(file);
  return response.data;
} catch (error) {
  if (error instanceof ValidationError) {
    toast.error('Invalid file format');
  } else if (error instanceof NetworkError) {
    logger.error('API request failed', { error, file });
    toast.error('Network error. Please try again.');
  } else {
    logger.error('Unexpected error', { error });
    toast.error('An error occurred. Please contact support.');
  }
  throw error;
}
```

---

## Coding Standards

### Python
- **Type hints**: Always use (PEP 484)
- **Naming**: snake_case functions/variables, PascalCase classes
- **Docstrings**: Google style for functions/classes
- **Async/await**: Use for I/O operations (API calls, file ops)
- **Pydantic models**: For request/response validation
- **Logging**: Use `logging` module, never `print`

```python
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class CalendarEvent(BaseModel):
    """Represents a calendar event."""
    title: str = Field(..., min_length=1, max_length=200)
    start_time: str
    end_time: str
    description: Optional[str] = None
    
async def create_event(event: CalendarEvent) -> dict:
    """
    Creates a calendar event via Google Calendar API.
    
    Args:
        event: Validated calendar event data
        
    Returns:
        dict: Created event details with ID
        
    Raises:
        CalendarServiceError: If API call fails
    """
    try:
        logger.info(f"Creating event: {event.title}")
        result = await calendar_client.insert_event(event.dict())
        return result
    except Exception as e:
        logger.error(f"Failed to create event: {e}")
        raise CalendarServiceError("Event creation failed") from e
```

### TypeScript
- **Strict mode**: Enable in tsconfig.json
- **Naming**: camelCase functions/variables, PascalCase classes/interfaces
- **Types**: Avoid `any`, use `unknown` when truly unknown
- **Interfaces**: Define for all object shapes
- **Async/await**: For all asynchronous operations

```typescript
interface UploadRequest {
  file: File;
  type: 'image' | 'document' | 'text';
}

interface UploadResponse {
  extractedText: string;
  eventsSuggested: CalendarEvent[];
}

async function uploadContent(request: UploadRequest): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', request.file);
  formData.append('type', request.type);
  
  try {
    const response = await fetch('/api/extract', {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    logger.error('Upload failed', { error, request });
    throw error;
  }
}
```

---

## OpenAI Agent Implementation

### Agent Tools Structure
```python
from openai import OpenAI

def add_event_tool(title: str, start: str, end: str, description: str = "") -> dict:
    """
    Adds an event to Google Calendar.
    
    Args:
        title: Event title (required)
        start: Start datetime in ISO format (required)
        end: End datetime in ISO format (required)
        description: Event description (optional)
    """
    try:
        event = CalendarEvent(
            title=title,
            start_time=start,
            end_time=end,
            description=description
        )
        result = calendar_service.add_event(event)
        return {"success": True, "event_id": result["id"]}
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return {"success": False, "error": str(e)}

# Tool definitions for agent
tools = [
    {
        "type": "function",
        "function": {
            "name": "add_event_tool",
            "description": "Add a new event to Google Calendar",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Event title"},
                    "start": {"type": "string", "description": "Start time (ISO 8601)"},
                    "end": {"type": "string", "description": "End time (ISO 8601)"},
                    "description": {"type": "string", "description": "Event details"}
                },
                "required": ["title", "start", "end"]
            }
        }
    }
]
```

---

## Google Calendar Integration

### Authentication
- Implement OAuth 2.0 flow
- Store tokens securely (environment variables, encrypted storage)
- Auto-refresh expired tokens
- Handle refresh token expiration gracefully

### API Operations
```python
class GoogleCalendarClient:
    """Client for Google Calendar API with retry logic."""
    
    def __init__(self, credentials: Credentials):
        self.service = build('calendar', 'v3', credentials=credentials)
        self.max_retries = 3
        
    @retry_with_backoff(max_retries=3, base_delay=1)
    async def add_event(self, event_data: dict) -> dict:
        """Adds event with retry logic for transient failures."""
        try:
            event = self.service.events().insert(
                calendarId='primary',
                body=event_data
            ).execute()
            logger.info(f"Event created: {event['id']}")
            return event
        except HttpError as e:
            if e.resp.status in [429, 503]:  # Rate limit or service unavailable
                logger.warning(f"Retryable error: {e}")
                raise  # Retry decorator handles this
            logger.error(f"Calendar API error: {e}")
            raise CalendarAPIError(f"Failed to create event: {e}") from e
```

---

## OpenAI Vision Integration

### Image Processing
```python
async def extract_content_from_image(image_file: bytes) -> str:
    """
    Extracts text content from image using OpenAI Vision.
    
    Args:
        image_file: Image bytes (JPEG/PNG)
        
    Returns:
        Extracted text content
    """
    try:
        # Validate image
        if len(image_file) > 20 * 1024 * 1024:  # 20MB limit
            raise ValidationError("Image too large")
            
        base64_image = base64.b64encode(image_file).decode('utf-8')
        
        response = await openai_client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all text content from this image."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=1000
        )
        
        extracted_text = response.choices[0].message.content
        logger.info(f"Extracted {len(extracted_text)} characters")
        return extracted_text
        
    except Exception as e:
        logger.error(f"Vision extraction failed: {e}")
        raise VisionServiceError("Failed to extract content") from e
```

---

## Key Patterns to Follow

### 1. Dependency Injection
```python
class CalendarAgent:
    def __init__(
        self,
        openai_client: OpenAI,
        calendar_service: CalendarService,
        logger: logging.Logger
    ):
        self.client = openai_client
        self.calendar = calendar_service
        self.logger = logger
```

### 2. Service Layer Pattern
Separate concerns: Controllers handle HTTP, Services handle business logic

### 3. Repository Pattern
Abstract external APIs behind interfaces for testability

### 4. Error Handling Hierarchy
```python
# Custom exception hierarchy
class CalendarAssistantError(Exception):
    """Base exception"""
    pass

class VisionServiceError(CalendarAssistantError):
    """Vision extraction errors"""
    pass

class CalendarServiceError(CalendarAssistantError):
    """Calendar operation errors"""
    pass
```

---

## Testing Requirements
- **Unit tests**: All business logic functions
- **Integration tests**: API endpoints, external service clients
- **Mocking**: Mock OpenAI and Google Calendar APIs
- **Coverage**: Aim for 80%+
- **Frameworks**: pytest (Python), Jest (TypeScript)

---

## Security Checklist
- [ ] API keys in environment variables only
- [ ] Input validation on all endpoints
- [ ] File upload validation (type, size, content)
- [ ] CORS configured properly
- [ ] HTTPS for all API calls
- [ ] OAuth tokens stored securely
- [ ] Rate limiting implemented
- [ ] Sanitize extracted text before processing

---

## Configuration Files

### backend/requirements.txt
```
openai>=1.0.0
google-api-python-client>=2.0.0
google-auth-httplib2>=0.2.0
google-auth-oauthlib>=1.0.0
pydantic>=2.0.0
fastapi>=0.100.0
uvicorn>=0.20.0
python-dotenv>=1.0.0
pillow>=10.0.0
```

### frontend/package.json
```json
{
  "dependencies": {
    "react": "^18.0.0",
    "typescript": "^5.0.0",
    "axios": "^1.0.0"
  }
}
```

---

**Remember**: Readable, reusable, robust. Every function should have one clear purpose. Every error should be handled explicitly. Every API call should have retry logic.
