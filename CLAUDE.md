# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Full-Stack Development

- `make run` - Build and run all services (frontend, backend, MongoDB, Redis)
- `make build` - Build all Docker containers
- `make stop` - Stop all running services
- `make clean` - Stop services and remove containers, networks, and volumes
- `make logs` - Follow logs from all services
- `make logs-backend` - Follow backend logs only
- `make logs-frontend` - Follow frontend logs only
- `make health` - Check health of all services

### Frontend Development (React/TypeScript)

- Instead of `npm run dev`, use `make run`
- `npm run build` - Build for production (TypeScript compile + Vite build)
- `npm run lint` - Run ESLint linting
- `npm run lint:fix` - Run ESLint with auto-fix
- `npm run format` - Format code with Prettier
- `npm run format:check` - Check formatting with Prettier
- `npm run type-check` - Run TypeScript type checking without emitting files
- `npm run preview` - Preview production build

### Backend Development (Python/Falcon)

- Backend uses `uv` for dependency management and `pyproject.toml` for configuration
- To start backend use `make run`.
- Run `ruff` for linting and formatting
- Run `mypy` for static type checking
- Run `pytest` for running tests

## Architecture Overview

This is a full-stack chatbot application with Claude reasoning models, featuring:

### Backend (Python/Falcon)

- **Framework**: Falcon ASGI with Uvicorn server
- **Database**: MongoDB with Motor (async driver)
- **Cache**: Redis for session and response caching
- **LLM Integration**: LiteLLM for unified access to Claude models
- **Key Features**: Streaming chat completions, Claude reasoning model support, tool calling, CORS middleware

### Frontend (React/TypeScript)

- **Framework**: React 19 with Vite
- **UI Components**: shadcn/ui (Radix UI + Tailwind CSS)
- **Key Features**: Real-time streaming chat interface, reasoning and thinking process display, responsive design

### Infrastructure

- **Orchestration**: Docker Compose with multi-service setup
- **Services**: Frontend (port 3000), Backend API (port 8080), MongoDB (port 27017), Redis (port 6379)

## Code Architecture and Patterns

### Backend Structure (`backend/src/`)

- `app.py` - Main Falcon application with CORS middleware and route registration
- `routes/` - Falcon Resource classes for API endpoints:
  - `healthcheck.py` - Health check endpoint
  - `chat.py` - Chat completions with streaming support
  - `users.py`, `projects.py`, `agent_profiles.py`, `conversations.py`, `instructions.py` - CRUD resources
- `helpers/` - Shared utilities:
  - `db.py` - MongoDB and Redis connection helpers
  - `llm.py` - LiteLLM integration for Claude models
  - `logger.py` - Logging configuration
  - `schemas.py` - Pydantic models for data validation
  - `json_encoder.py` - Custom JSON encoding

### Frontend Structure (`frontend/src/`)

- `App.tsx` - Main app with React Router setup
- `pages/` - Page components (Home, About, Settings, Chat)
- `components/` - Reusable components:
  - `ui/` - shadcn/ui components (button, card, input, scroll-area, textarea)
  - `Layout.tsx`, `Navigation.tsx`, `Sidebar.tsx` - Layout components
  - `ChatArea.tsx`, `NewChat.tsx` - Chat-specific components
- `hooks/` - Custom React hooks for chat logic and context
- `lib/` - Utilities (`api.ts` for API calls, `utils.ts` for className merging)

### Key Patterns

- **Backend**: Uses async/await patterns, Pydantic for validation, Motor for MongoDB, Redis for caching
- **Frontend**: Functional components with hooks, TypeScript strict mode, shadcn/ui for components, Tailwind for styling
- **API Integration**: RESTful endpoints with JSON, streaming support for chat completions
- **Error Handling**: Proper logging and error responses, fallback LLM models

## Development Notes

### Adding shadcn/ui Components

Use `npx shadcn@latest add [component]` to add new UI components to the frontend.

### Environment Variables

Configure in `.env` file (copy from `.env.template`):

- `ANTHROPIC_API_KEY` - Required for Claude models
- Database and Redis connection strings are set for Docker Compose

### Testing and Quality

- Pre-commit hooks are configured for code quality checks
- Backend uses `ruff`, `mypy`, and `pytest`
- Frontend uses ESLint, Prettier, and TypeScript strict mode

### Docker Development

All services run in Docker containers with persistent volumes for MongoDB and Redis. The `make` commands handle the full Docker Compose lifecycle.
