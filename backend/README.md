# Calendar Assistant Backend

## Setup

1. Activate virtual environment:
```bash
..\calendar_agent\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
# Create .env file or set in terminal
$env:OPENAI_API_KEY="your-openai-api-key-here"
```

## Running the Server

```bash
python run.py
```

Or directly with uvicorn:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Testing with Swagger UI

Once the server is running, open your browser and go to:

- **Swagger UI (Interactive API Docs)**: http://localhost:8000/docs
- **ReDoc (Alternative Docs)**: http://localhost:8000/redoc
- **OpenAPI JSON Schema**: http://localhost:8000/openapi.json

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check

### Chat
- `POST /chat` - Main chat endpoint
  - Form parameters:
    - `message` (optional): Text message
    - `file` (optional): Image/PDF file
    - `user_id` (optional): User ID for session continuity

## Testing in Swagger

1. Go to http://localhost:8000/docs
2. Click on `/chat` endpoint
3. Click "Try it out"
4. Enter your message and/or upload a file
5. Click "Execute"
6. View the response below

## Example Requests

### Text only:
```bash
curl -X POST "http://localhost:8000/chat" \
  -F "message=Add a meeting tomorrow at 2 PM"
```

### File only:
```bash
curl -X POST "http://localhost:8000/chat" \
  -F "file=@path/to/image.png"
```

### Both:
```bash
curl -X POST "http://localhost:8000/chat" \
  -F "message=Add these events to my calendar" \
  -F "file=@path/to/schedule.pdf"
```
