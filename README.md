# Claude Reasoning Chatbot

A full-stack chatbot application featuring Claude's reasoning models with streaming support, tool calling, and a modern React frontend. Includes local MongoDB and Redis for data persistence and caching.

## Architecture

### Backend (Python/Falcon)

- **Framework**: Falcon ASGI with Uvicorn server
- **Database**: MongoDB with Motor (async driver)
- **Cache**: Redis for session and response caching
- **LLM Integration**: LiteLLM for unified access to Claude models
- **Features**:
  - Streaming chat completions
  - Claude reasoning model support
  - Tool calling capabilities
  - CORS middleware
  - Database connectivity health checks
  - Proper error handling and logging

### Frontend (React/TypeScript)

- **Framework**: React 19 with Vite
- **UI Components**: shadcn/ui (Radix UI + Tailwind CSS)
- **Features**:
  - Real-time streaming chat interface
  - Reasoning and thinking process display
  - Modern, responsive design
  - Message history with timestamps

### Infrastructure

- **Orchestration**: Docker Compose with multi-service setup
- **Database**: MongoDB 7 with persistent volumes
- **Cache**: Redis 7 with persistent storage
- **Networking**: Isolated Docker network for service communication

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Anthropic API key (for Claude models)

### Initial Setup After Clone

After cloning the repository, set up pre-commit hooks for code quality:

1. **Install pre-commit** (if not already installed):

   ```bash
   # macOS (recommended)
   brew install pre-commit

   # or via pip
   pip install pre-commit
   ```

2. **Install pre-commit hooks**:

   ```bash
   pre-commit install
   ```

   This sets up automatic code quality checks (linting, formatting, type checking) that run before each commit.

3. **Test the hooks** (optional):

   ```bash
   pre-commit run --all-files
   ```

### Setup and Run

1. **Initial Setup**:

   ```bash
   cp .env.template .emv
   ```

   This copies the `.env.template` file from the template and builds the containers.

2. **Configure Environment Variables**:

   Edit the `.env` file and add your API keys:

   ```bash
   # Add your API keys
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

3. **Start Services**:

   ```bash
   make run
   ```

   This starts all services in the background. You'll see:
   - Frontend: <http://localhost:3000>
   - Backend API: <http://localhost:8080>
   - MongoDB: localhost:27017
   - Redis: localhost:6379

4. **Check Health**:

   ```bash
   make health
   ```

### Development Commands

```bash
make build         # Build all containers
make run          # Run in development mode
make logs         # View all service logs
make logs-backend # View backend logs only
make stop         # Stop all services
make clean        # Stop and remove everything
```
