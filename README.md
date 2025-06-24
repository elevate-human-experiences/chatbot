# Claude Reasoning Chatbot

A full-stack chatbot application featuring Claude's reasoning models with streaming support, tool calling, and a modern React frontend.

## Architecture

### Backend (Python/Falcon)

- **Framework**: Falcon ASGI with Uvicorn server
- **LLM Integration**: LiteLLM for unified access to Claude models
- **Features**:
  - Streaming chat completions
  - Claude reasoning model support
  - Tool calling capabilities
  - CORS middleware
  - Proper error handling and logging

### Frontend (React/TypeScript)

- **Framework**: React 19 with Vite
- **UI Components**: shadcn/ui (Radix UI + Tailwind CSS)
- **Features**:
  - Real-time streaming chat interface
  - Reasoning and thinking process display
  - Modern, responsive design
  - Message history with timestamps

## Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- Anthropic API key (for Claude models)

### Backend Setup

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Install dependencies with uv:

   ```bash
   uv sync
   ```

3. Set up environment variables:

   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

4. Start the development server:

   ```bash
   uv run python src/app.py
   ```

   The backend will be available at `http://localhost:8080`

### Frontend Setup

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Start the development server:

   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

## API Endpoints

### Health Check

- **GET** `/health` - Check server status

### Chat Completions

- **POST** `/chat/completions` - Stream chat completions with Claude reasoning models

#### Request Format

```json
{
  "messages": [
    {"role": "user", "content": "Your message here"}
  ],
  "model": "anthropic/claude-sonnet-4-20250514",
  "stream": true,
  "reasoning_effort": "medium",
  "thinking": {"type": "enabled", "budget_tokens": 2048},
  "temperature": 1.0
}
```

#### Response Format

Server-sent events (SSE) with chunks containing:

- `content`: Regular response content
- `thinking`: Claude's thinking process
- `reasoning`: Reasoning steps
- `tool_calls`: Function calls (if applicable)

## Features

### Backend Improvements

1. **Enhanced Streaming**: Fixed duplicate content and improved chunk processing
2. **CORS Support**: Proper async CORS middleware for cross-origin requests
3. **Error Handling**: Robust error handling with proper HTTP status codes
4. **Logging**: Structured logging with configurable levels
5. **Claude Integration**: Optimized for Claude's reasoning models and thinking process

### Frontend Improvements

1. **Modern Chat UI**: Clean, responsive chat interface with shadcn/ui components
2. **Streaming Display**: Real-time message streaming with typing indicator
3. **Reasoning Visibility**: Expandable sections for thinking and reasoning processes
4. **Message History**: Persistent chat history with timestamps
5. **Error Handling**: User-friendly error messages and connection status

### Testing

Use the test script to verify the API:

```bash
cd backend
uv run test_api.py
```

## Development

### VS Code Tasks

- **Backend Dev Server**: Starts the Python backend with auto-reload
- **Frontend Dev Server**: Starts the React development server

### Code Quality

- Backend: Uses ruff for linting, mypy for type checking
- Frontend: Uses ESLint and TypeScript for code quality

## Environment Variables

### Backend (.env)

```env
PORT=8080
HOST=0.0.0.0
DEBUG=true
ANTHROPIC_API_KEY=your_anthropic_key_here
LOG_LEVEL=INFO
```

## Tech Stack

### Backend

- **Falcon ASGI**: High-performance Python web framework
- **LiteLLM**: Unified interface for multiple LLM providers
- **Uvicorn**: Lightning-fast ASGI server
- **Python 3.12**: Latest Python with modern features

### Frontend

- **React 19**: Latest React with modern hooks and features
- **TypeScript**: Strong typing for better development experience
- **Vite**: Fast build tool and development server
- **shadcn/ui**: High-quality, accessible UI components
- **Tailwind CSS**: Utility-first CSS framework

## Key Improvements Made

1. **Fixed Streaming Issues**: Resolved duplicate content and improved response formatting
2. **Added CORS Support**: Enabled cross-origin requests for frontend-backend communication
3. **Enhanced Error Handling**: Better error messages and graceful failure handling
4. **Improved UI**: Complete redesign with modern chat interface
5. **Reasoning Display**: Show Claude's thinking and reasoning processes
6. **Real-time Updates**: Streaming messages with live updates
7. **Better Logging**: Structured logging with appropriate levels
8. **Type Safety**: Full TypeScript support throughout the application
