# Chatbot Backend

A Python Falcon-based backend service with Claude Anthropic reasoning models and comprehensive CRUDL APIs.

## Features

- **AI/LLM Integration**: Support for Claude Anthropic reasoning models, OpenAI GPT, and Google Gemini
- **Database**: MongoDB with Motor async driver and Redis for caching
- **API**: RESTful endpoints with Falcon ASGI framework
- **Authentication**: JWT-based authentication with bcrypt password hashing
- **CORS**: Configurable cross-origin resource sharing
- **Logging**: Structured logging with configurable levels
- **Testing**: Comprehensive test suite with pytest

## Quick Start

### Prerequisites

- Python 3.12+
- MongoDB (via Docker or local installation)
- Redis (via Docker or local installation)
- API keys for AI providers (Anthropic, OpenAI, Google)

### Environment Setup

1. **Copy the environment template:**

   ```bash
   cp .env.example .env
   ```

2. **Configure your environment variables:**
   Edit the `.env` file and update the following required fields:

   ```bash
   # Required: Anthropic API Key for Claude models
   ANTHROPIC_API_KEY=your_anthropic_api_key_here

   # Optional: Additional AI provider keys
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here

   # Security: Change in production
   JWT_SECRET_KEY=your_secure_jwt_secret_key_here
   ```

3. **Install dependencies using uv:**

   ```bash
   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install project dependencies
   uv sync
   ```

4. **Start the database services:**

   ```bash
   # From the root directory
   docker-compose up -d mongodb redis
   ```

5. **Run the development server:**

   ```bash
   uv run python src/app.py
   ```

The server will start at `http://localhost:8080` by default.

## Environment Variables Reference

### Application Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host address |
| `PORT` | `8080` | Server port |
| `DEBUG` | `true` | Enable debug mode |
| `ENVIRONMENT` | `development` | Application environment |

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_CONNECTION_STRING` | `mongodb://mongodb:27017` | MongoDB connection string |
| `DB_NAME` | `chatbot` | MongoDB database name |
| `REDIS_CONNECTION_STRING` | `redis://redis:6379` | Redis connection string |

### AI/LLM Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | - | **Required**: Anthropic API key for Claude models |
| `OPENAI_API_KEY` | - | Optional: OpenAI API key for GPT models |
| `GOOGLE_API_KEY` | - | Optional: Google API key for Gemini models |
| `DEFAULT_MODEL` | `anthropic/claude-sonnet-4-20250514` | Default LLM model |
| `LITELLM_MAX_TOKENS` | `4096` | Maximum tokens per request |
| `LITELLM_TEMPERATURE` | `0.7` | Model temperature setting |

### Security Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | - | **Required**: JWT signing secret key |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRATION_HOURS` | `24` | JWT token expiration time |
| `BCRYPT_ROUNDS` | `12` | Bcrypt hashing rounds |

### External Services

| Variable | Default | Description |
|----------|---------|-------------|
| `SENDGRID_API_KEY` | - | SendGrid API key for email |
| `SENDGRID_FROM_EMAIL` | `noreply@yourdomain.com` | Default sender email |
| `AWS_ACCESS_KEY_ID` | - | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | - | AWS secret key |
| `AWS_REGION` | `us-east-1` | AWS region |
| `AWS_S3_BUCKET` | - | S3 bucket name |

## API Endpoints

### Health Check

- `GET /health` - Service health status

### Chat Completions

- `POST /chat/completions` - AI chat completions

### Users

- `GET /users` - List users
- `POST /users` - Create user
- `GET /users/{user_id}` - Get user
- `PUT /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Delete user

### Projects

- `GET /projects` - List projects
- `POST /projects` - Create project
- `GET /projects/{project_id}` - Get project
- `PUT /projects/{project_id}` - Update project
- `DELETE /projects/{project_id}` - Delete project

### Agent Profiles

- `GET /projects/{project_id}/profiles` - List agent profiles
- `POST /projects/{project_id}/profiles` - Create agent profile
- `GET /projects/{project_id}/profiles/{profile_id}` - Get agent profile
- `PUT /projects/{project_id}/profiles/{profile_id}` - Update agent profile
- `DELETE /projects/{project_id}/profiles/{profile_id}` - Delete agent profile

### Instructions

- `GET /projects/{project_id}/profiles/{profile_id}/instructions` - List instructions
- `POST /projects/{project_id}/profiles/{profile_id}/instructions` - Create instruction
- `GET /projects/{project_id}/profiles/{profile_id}/instructions/{instruction_index}` - Get instruction
- `PUT /projects/{project_id}/profiles/{profile_id}/instructions/{instruction_index}` - Update instruction
- `DELETE /projects/{project_id}/profiles/{profile_id}/instructions/{instruction_index}` - Delete instruction

### Conversations

- `GET /projects/{project_id}/conversations` - List conversations
- `POST /projects/{project_id}/conversations` - Create conversation
- `GET /projects/{project_id}/conversations/{conversation_id}` - Get conversation
- `PUT /projects/{project_id}/conversations/{conversation_id}` - Update conversation
- `DELETE /projects/{project_id}/conversations/{conversation_id}` - Delete conversation
- `GET /projects/{project_id}/conversations/{conversation_id}/messages` - List messages
- `POST /projects/{project_id}/conversations/{conversation_id}/messages` - Create message

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/test_api.py
```

### Code Quality

```bash
# Lint code
uv run pylint src/

# Format code (if black is configured)
uv run black src/
```

### Database Management

The application uses MongoDB for primary data storage and Redis for caching. When running locally with Docker Compose, both services are automatically started.

#### MongoDB Collections

- `users` - User accounts and profiles
- `projects` - Project definitions
- `agent_profiles` - AI agent configurations
- `conversations` - Chat conversations and messages

#### Redis Usage

- Session caching
- API response caching
- Rate limiting data

## Deployment

### Docker

```bash
# Build the image
docker build -t chatbot-backend .

# Run the container
docker run -p 8080:8080 --env-file .env chatbot-backend
```

### Production Environment Variables

Make sure to update these variables for production:

```bash
# Change to production values
DEBUG=false
ENVIRONMENT=production
JWT_SECRET_KEY=your_very_secure_production_secret_key

# Use production database URLs
MONGODB_CONNECTION_STRING=mongodb://your-production-mongodb:27017
REDIS_CONNECTION_STRING=redis://your-production-redis:6379

# Configure external services
SENDGRID_API_KEY=your_production_sendgrid_key
AWS_ACCESS_KEY_ID=your_production_aws_key
```

## Architecture

The backend follows a modular architecture:

- `src/app.py` - Main application factory and configuration
- `src/routes/` - API route handlers (Falcon resources)
- `src/helpers/` - Shared utilities (database, logging, LLM, schemas)
- `tests/` - Test suite

### Key Components

1. **Falcon ASGI App** - High-performance web framework
2. **Motor** - Async MongoDB driver
3. **Redis** - Caching and session storage
4. **LiteLLM** - Unified interface for multiple AI providers
5. **Pydantic** - Data validation and serialization
6. **JWT** - Stateless authentication

## Support

For questions or issues, please refer to the project documentation or create an issue in the repository.

## License

MIT License - see LICENSE file for details.
