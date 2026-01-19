# Calendar-Agent

An AI agent built with the Agents SDK for intelligent calendar and task management. The agent understands natural language requests, autonomously decides which tools to use, and manages your schedule efficiently. It can process text messages and extract information from images and PDFs using vision capabilities.

## Features

- **Autonomous AI Agent**: Uses the Agents SDK to intelligently orchestrate calendar operations
- **Natural Language Understanding**: Interact with your calendar using conversational language
- **Event Management**: Create, view, and delete calendar events with ease
- **Task Management**: Add tasks with deadlines, mark them complete, and track your to-dos
- **Smart Reminders**: Automatically creates reminder events 3 days before task deadlines
- **Vision Capabilities**: Extract text from images and PDFs to create calendar entries
- **Multi-File Support**: Upload screenshots, images (JPEG, PNG, GIF, WebP), or PDF documents
- **Conversation Context**: Maintains multi-turn conversation history across interactions
- **Modern UI**: Clean, responsive React-based chat interface

## Architecture

### Backend (Python FastAPI)
- **AI Agent**: Built with the Agents SDK for autonomous tool selection and execution
- **FastAPI REST API**: Handles HTTP requests and file uploads
- **Google Calendar Integration**: Direct integration with Google Calendar API
- **Vision Service**: Extracts text from images and PDFs using GPT-4 Vision
- **Chat Service**: Manages conversation flow and coordinates agent interactions
- **Structured Outputs**: Uses Pydantic models for reliable response formatting

### Frontend (React + TypeScript)
- **React UI**: Modern, responsive chat interface
- **TypeScript**: Type-safe development
- **Vite**: Fast development and build tooling
- **File Upload**: Drag-and-drop or click to upload files
- **Real-time Updates**: Instant feedback and typing indicators

## Prerequisites

- Python 3.8+
- Node.js 18+
- OpenAI API key (GPT-4 or GPT-5)
- Google Calendar API credentials (credentials.json)
- Agents SDK (`pip install agents-sdk`)

## Setup

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
Create a `.env` file in the backend directory with:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

5. Set up Google Calendar credentials:
- Follow the [Google Calendar API setup guide](https://developers.google.com/calendar/api/quickstart/python)
- Place your `credentials.json` in the backend directory
- Run the app once to authorize and generate `token.json`

6. Start the backend server:
```bash
python run.py
```
The backend will run on `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure the API URL (optional):
Create a `.env` file if you need to change the backend URL:
```env
VITE_API_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```
The frontend will run on `http://localhost:3000`

## Usage

1. Open your browser and navigate to `http://localhost:3000`
2. Chat with the AI agent in natural language:
   - "Schedule a team meeting tomorrow at 2 PM"
   - "Add a task to finish the report by Friday"
   - "Show me my events for this week"
   - "Delete my meeting on Wednesday"
3. Upload images or PDFs containing calendar information
4. The agent will autonomously select the right tools and update your Google Calendar

## How the AI Agent Works

The Calendar Agent uses the Agents SDK to:
1. **Understand Intent**: Analyzes your message to determine what you want to do
2. **Select Tools**: Autonomously chooses the appropriate calendar/task tools
3. **Execute Actions**: Calls the selected tools with the right parameters
4. **Maintain Context**: Remembers previous conversations using `result.to_input_list()`
5. **Provide Feedback**: Confirms actions and provides clear responses

## Available Tools

The AI assistant has access to the following tools:

- **add_event**: Create calendar events with title, date, time, and duration
- **list_calendar_events**: View upcoming events within a date range
- **delete_calendar_event**: Remove events from the calendar
- **add_task**: Create tasks with titles, descriptions, and deadlines
- **list_tasks**: View all tasks or filter by completion status
- **complete_task**: Mark tasks as completed
- **delete_task**: Remove tasks from the list

## Project Structure

```
Calendar-Agent/
├── backend/
│   ├── src/
│   │   ├── calendar_agents/    # Agent runner and coordination
│   │   ├── config/             # Prompts and configuration
│   │   ├── models/             # Pydantic models
│   │   ├── services/           # Business logic services
│   │   ├── tools/              # Calendar and task tools
│   │   └── main.py             # FastAPI application
│   ├── requirements.txt        # Python dependencies
│   └── run.py                  # Server entry point
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── services/           # API client
│   │   ├── types/              # TypeScript types
│   │   └── App.tsx             # Main app component
│   ├── package.json            # Node dependencies
│   └── vite.config.ts          # Vite configuration
└── README.md
```
