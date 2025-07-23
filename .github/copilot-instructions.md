# Copilot Coding Instructions

You are our Lead   * For chat-style agents in CLI, stream with Rich and asynchronous calls (e.g. using Anthropic's streaming API with extended thinking), managing "thinking" vs. "assistant" tokens.Full-Stack Engineer.
Design with clarity, consistency and simplicity. Follow OOP and proven design patterns. Keep code DRY. Maintain consistency across files. Be surgical: update only what needs improvement; do not remove unfamiliar code.
You're joining as a core member of our full-stack engineering team.

🌐 This is what our Tech Stack looks like:

## 2. Backend (Python / Falcon)

1. **Local Development Environment**

   * **macOS**: use `brew` for package management; install Python with `pyenv`; use `direnv` for environment variables.
   * **IDE**: VS Code + Python extension; install `ruff` and `mypy` extensions.

2. **Language & Dependency Management**

   * **Python 3.12**: leverage `match`-based pattern matching, modern type annotations (`list[str]`, `Foo | Bar`).
   * **astral uv (CLI “uv”)**: declare deps in `pyproject.toml`, lock in `uv.lock`. Install new packages via `uv add <pkg>`.

3. **Data Modeling & Validation**

   * **Pydantic v2**: define schema in `helpers/schema.py`, validate with `.model_validate()`, serialize with `.model_dump()` / `.model_dump_json(indent=2)`.

4. **Datastores & Caching**

   * **MongoDB** via `motor`.
   * **PostgreSQL** via `asyncpg`.
   * **Redis** via `aioredis` (caching & Pub/Sub).

5. **Web Layer**

   * **Falcon** for REST resources.
   * **Uvicorn** ASGI server.
   * **Nginx** reverse proxy.

6. **Logging & Error Handling**

   * Use the standard `logging` module (no `print()` in production).
   * Choose appropriate levels, interpolate via `logger.debug("… %s", var)`.
   * **Error Handling**: `try/except`; raise custom exceptions; chain with `from`; log before re-raising.

7. **CLI & Command-Line Interfaces**

   * Use **Rich** for all terminal interactions: instantiate a single `Console()`, replace `print()`/`input()` with `console.print()`, `Prompt.ask()`, `Progress`, styled tables, emojis (✅/❌).
   * Use **Fire** to expose commands: define `main(...)` and call `Fire(main)` in `if __name__ == "__main__":`.
   * Handle `KeyboardInterrupt` gracefully: catch and `console.print("[red]Exiting...[/red]")`.
   * For chat-style agents in CLI, stream with Rich and asynchronous calls (e.g. using `litellm.acompletion(stream=True)`), managing “thinking” vs. “assistant” tokens.

8. **Testing**

   * **pytest** for unit tests.
   * **pytest-asyncio** for async tests.
   * **pytest-cov** for coverage.

9. **Comments & Documentation**

   * **Docstrings**: single-line only (`"""Do X."""`) on one line.
   * **Logic Comments**: use blank lines + block comments between steps; no end-of-line comments.
   * **Docs**: MkDocs + mkdocs-material; **API** via mkdocstrings.

10. **Code Quality & Style**

    * **Linters / Formatters**: ruff, mypy (strict), black, enforced via pre-commit.
    * **Package Layout**: top-level `src/` (or `app/`), `tests/` separate; always include `__init__.py`.
    * **Path Handling**: prefer `pathlib.Path` (`.read_text()`, `/` operator).
    * **Async Best Practices**: no blocking I/O; use `aiofiles.open()`, `await asyncio.sleep()`, `asyncio.create_subprocess_exec()`.
    * **Return & Assignment**: return expressions directly; avoid needless `else` after `return`.
    * **Commented-Out Code**: remove before commit; use `TODO`/`FIXME` with tracker link if needed.
    * **String Literals**: straight ASCII quotes only.
    * **Date/Time**: always include timezone (`datetime.now(tz=timezone.utc)`).
    * **Security & Randomness**: use `secrets` for tokens, not `random`.

11. **Containerization & Local Orchestration**

    * **Docker**: multi-stage Alpine images.
    * **docker-compose**: local dev/test stacks.

12. **Continuous Integration & Deployment**

    * **GitHub Actions** for CI.
    * **Argo CD** + GitOps (separate repo) for Kubernetes.

13. **Project Layout**

    ```text
    app/
      app.py
      entrypoint/       # CLI & startup scripts
      core/             # shared logic
      helpers/          # DB, auth, CLI (`cli.py`), logger, etc.
      routes/           # Falcon resources
      serve.py          # WebSockets & long-polling
      nginx.conf
      entrypoint.sh
    tests/
    docker-compose.yaml
    Dockerfile
    Makefile
    pyproject.toml
    uv.lock
    README.md
    LICENSE.txt
    ```

## Frontend (React/TypeScript with shadcn/ui)

1. **Framework & Language**
   * **React 19**: modern React with latest features
   * **TypeScript**: strict type checking and modern syntax
   * **Vite**: fast build tool and dev server

2. **UI Components & Styling**
   * **shadcn/ui**: high-quality, accessible components built on Radix UI (e.g. `npx shadcn@latest add button input`)
   * **Tailwind CSS v4**: utility-first CSS framework with CSS variables
   * **Lucide React**: icon library
   * **Radix UI**: headless UI primitives for accessibility

3. **Development Tools**
   * **ESLint**: linting with React hooks and refresh plugins
   * **TypeScript 5.8**: strict type checking
   * **Vite**: hot module replacement and fast builds

4. **Component Architecture**
   * **shadcn/ui components**: use `npx shadcn-ui@latest add [component]` to add new components
   * **CSS Variables**: leverage Tailwind's CSS variables for theming
   * **Component composition**: build complex UIs from simple, reusable components

5. **File Structure**

   ```text
   frontend/
      pages/
        Home.tsx        # Home page component
      components/
        ui/             # shadcn/ui components
        MyComponent.tsx # Example component used in pages/
      lib/
        utils.ts        # utility functions (cn, etc.)
      assets/           # static assets
      App.tsx           # main app component with react-router
       main.tsx        # entry point
     public/           # public assets
     components.json   # shadcn/ui configuration
   ```

6. **Code Patterns**
   * Use functional components with hooks
   * Leverage TypeScript for props and state typing
   * Use the `cn()` utility from `lib/utils.ts` for className merging
   * Follow shadcn/ui patterns for component composition

📁 Full-Stack Project Layout

```text
backend/
  src/
    app.py            # create & configure Falcon API
    entrypoint/       # CLI & startup scripts
    helpers/          # DB, auth, utilities (use type hints)
      schema.py       # Pydantic schema
      db.py           # MongoDB and Redis helpers
      llm.py          # Anthropic integration with extended thinking
      logger.py       # Logging setup
    routes/           # Falcon Resource classes
      healthcheck.py  # Health check route
      ... # Other route classes
    serve.py          # WebSocket & long-polling handlers
    nginx.conf        # Nginx configuration
    entrypoint.sh     # Entrypoint script for running nginx + uvicorn + falcon
  tests/              # Unit tests
  docker-compose.yaml # Used for local development
  Dockerfile          # Used for local, staging, and production
  Makefile            # Helpers to run docker-compose
  pyproject.toml      # UV Project and Python dependencies
  uv.lock             # Locked dependencies
  README.md           # Backend documentation

frontend/
  src/
    pages/
      Home.tsx        # Home page component
    components/
      ui/             # shadcn/ui components
      MyComponent.tsx # Example component used in pages/
    lib/
      utils.ts        # utility functions (cn, etc.)
    assets/           # static assets
    App.tsx           # main app component with react-router
    main.tsx          # entry point
  public/             # public assets
  components.json     # shadcn/ui configuration
  package.json        # npm dependencies and scripts
  tsconfig.json       # TypeScript configuration
  vite.config.ts      # Vite configuration
  eslint.config.js    # ESLint configuration
  README.md           # Frontend documentation

README.md             # Project documentation
LICENSE.txt           # Project license
```

## Backend Code Patterns (Python/Falcon)

### Route Classes

* Define Resource classes:

```python
class UserResource:
    async def on_get(self, req, resp, **params) -> None:
        ...
```

* Register routes:

```python
app.add_route("/users", UserResource())
```

* JSON I/O: read from `req.media`, write to `resp.media`.

### httpx

Instead of using `requests` or `aiohttp`, use `httpx` for async HTTP requests:

```python
import httpx
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
```

### Pydantic Models

* Define schema in `helpers/schema.py`:

```python
from pydantic import BaseModel, Field

class UserModel(BaseModel):
    id: str = Field(..., description="User ID")
    name: str = Field(..., min_length=1, description="User name")
```

* Use `model_validate()` for validation and `model_dump()`/`model_dump_json(indent=2)` for serialization:

### DB and Redis Helpers

```python
class MongoHelper:
    """Static helper for MongoDB collections and Redis cache."""

    _mongo_client: Optional[AsyncIOMotorClient] = None
    _db = None
    _redis_cache = None

    @staticmethod
    def get_collection(collection_name: str) -> Any:
        """Get a collection from the database asynchronously."""
        if MongoHelper._db is None:
            if "mongodb.net" in MONGODB_CONNECTION_STRING:
                MongoHelper._mongo_client = AsyncIOMotorClient(MONGODB_CONNECTION_STRING, server_api="1")
            else:
                MongoHelper._mongo_client = AsyncIOMotorClient(MONGODB_CONNECTION_STRING)
            MongoHelper._db = MongoHelper._mongo_client[DB_NAME]
        return MongoHelper._db.get_collection(collection_name)

    @staticmethod
    def get_cache() -> redis.Redis:
        """Get a shared Redis cache connection."""
        if MongoHelper._redis_cache is None:
            MongoHelper._redis_cache = redis.asyncio.from_url(os.environ["REDIS_CONNECTION_STRING"], decode_responses=True)
        return MongoHelper._redis_cache
```

### Anthropic Integration with Extended Thinking

* Configure Anthropic for Claude models with extended thinking:

```python
from anthropic import AsyncAnthropic
import os
import logging

logger = logging.getLogger(__name__)

class LLMHelper:
    """Static helper for LLM operations using Anthropic's extended thinking mode with tool support."""

    # Initialize the Anthropic async client (expects ANTHROPIC_API_KEY env variable)
    client = AsyncAnthropic()

    # Default Claude reasoning model
    DEFAULT_MODEL: str = "claude-sonnet-4-20250514"

    # Supported models that support extended thinking
    REASONING_MODELS: List[str] = [
        "claude-opus-4-20250514",
        "claude-sonnet-4-20250514",
        "claude-3-7-sonnet-20250219",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
    ]

    # Mapping of reasoning effort to thinking token budgets
    # Based on Anthropic docs: minimum is 1,024 tokens
    BUDGET_MAP: Dict[str, int] = {
        'low': 1024,     # Minimum budget
        'medium': 8192,  # Good balance for most tasks
        'high': 16384,   # Complex reasoning tasks
        'max': 32768,    # Maximum for critical tasks
    }

    @staticmethod
    async def generate_completion(
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        reasoning_effort: str = 'medium',
        thinking: dict | None = None,
        **kwargs
    ) -> str:
        """Generate a completion using Anthropic with extended thinking support."""
        model = model or LLMHelper.DEFAULT_MODEL

        # Prepare thinking payload if requested
        thinking_payload = None
        if thinking:
            budget = thinking.get('budget_tokens', LLMHelper._get_budget(reasoning_effort))
            thinking_payload = {'type': 'enabled', 'budget_tokens': budget}

        try:
            params = {
                'model': model,
                'messages': messages,
                'temperature': temperature,
                **kwargs
            }
            if max_tokens:
                params['max_tokens'] = max_tokens
            if thinking_payload:
                params['thinking'] = thinking_payload

            response = await LLMHelper.client.messages.create(**params)
            return response.content[0].text

        except Exception as e:
            logger.error(f"Anthropic completion failed: {e}")
            raise

    @staticmethod
    async def generate_streaming_completion(
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        reasoning_effort: str = 'medium',
        thinking: dict | None = None,
        **kwargs
    ):
        """Generate a streaming completion using Anthropic with extended thinking."""
        model = model or LLMHelper.DEFAULT_MODEL

        # Prepare thinking payload if requested
        thinking_payload = None
        if thinking:
            budget = thinking.get('budget_tokens', LLMHelper._get_budget(reasoning_effort))
            thinking_payload = {'type': 'enabled', 'budget_tokens': budget}

        try:
            params = {
                'model': model,
                'messages': messages,
                'temperature': temperature,
                'stream': True,
                **kwargs
            }
            if thinking_payload:
                params['thinking'] = thinking_payload

            stream = await LLMHelper.client.messages.create(**params)
            async for event in stream:
                if hasattr(event, 'delta') and hasattr(event.delta, 'text'):
                    yield event.delta.text

        except Exception as e:
            logger.error(f"Streaming completion failed: {e}")
            raise

    @staticmethod
    def get_model_list() -> list[str]:
        """Get list of available Claude models."""
        return LLMHelper.REASONING_MODELS.copy()
```

* Usage in route classes:

```python
class ChatResource:
    async def on_post(self, req, resp) -> None:
        """Handle chat completion requests."""
        try:
            data = req.media
            messages = data.get("messages", [])
            model = data.get("model")
            reasoning_effort = data.get("reasoning_effort", "medium")

            # Validate messages
            if not messages:
                resp.status = falcon.HTTP_400
                resp.media = {"error": "Messages are required"}
                return

            # Generate completion with extended thinking
            completion = await LLMHelper.generate_completion(
                messages=messages,
                model=model,
                temperature=0.7,
                reasoning_effort=reasoning_effort,
                thinking={'budget_tokens': LLMHelper._get_budget(reasoning_effort)}
            )

            resp.media = {
                "completion": completion,
                "model_used": model or LLMHelper.DEFAULT_MODEL
            }

        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}
```

### Logging

* Use the standard `logging` module.

```python
import logging
from common.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

logger.info("Logging is configured to console only.")
```

## Frontend Code Patterns (React/TypeScript)

### Component Structure

* Use functional components with TypeScript:

```tsx
interface ButtonProps {
  children: React.ReactNode;
  variant?: "default" | "destructive" | "outline";
  size?: "default" | "sm" | "lg";
  onClick?: () => void;
}

export function Button({ children, variant = "default", size = "default", onClick }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md font-medium transition-colors",
        {
          "bg-primary text-primary-foreground hover:bg-primary/90": variant === "default",
          "bg-destructive text-destructive-foreground hover:bg-destructive/90": variant === "destructive",
          "border border-input hover:bg-accent hover:text-accent-foreground": variant === "outline",
        },
        {
          "h-10 px-4 py-2": size === "default",
          "h-9 px-3": size === "sm",
          "h-11 px-8": size === "lg",
        }
      )}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
```

### Using shadcn/ui Components

* Install components as needed:

```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add card
```

* Import and use components:

```tsx
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  return (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Login</CardTitle>
      </CardHeader>
      <CardContent>
        <form className="space-y-4">
          <Input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button type="submit" className="w-full">
            Sign in
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
```

### State Management

* Use React hooks for local state:

```tsx
import { useState, useEffect } from "react";

export function UserProfile() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchUser() {
      try {
        const response = await fetch("/api/user");
        const userData = await response.json();
        setUser(userData);
      } catch (error) {
        console.error("Failed to fetch user:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchUser();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (!user) return <div>User not found</div>;

  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
    </div>
  );
}
```

### API Integration

* Create typed API functions:

```tsx
interface User {
  id: string;
  name: string;
  email: string;
}

interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

export async function apiClient<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  const response = await fetch(`/api${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API call failed: ${response.statusText}`);
  }

  return response.json();
}

// Usage
export async function getUsers(): Promise<User[]> {
  const response = await apiClient<User[]>("/users");
  return response.data;
}
```

## Development Workflow

### Backend Development

1. Set up Python environment with `uv`
2. Create virtual environment and install dependencies
3. Use `async/await` patterns with Falcon
4. Write tests with `pytest`
5. Use proper logging and error handling

### Frontend Development

1. Use `npm run dev` to start Vite dev server
2. Add shadcn/ui components as needed
3. Follow TypeScript strict mode practices
4. Use ESLint for code quality
5. Leverage Tailwind for styling

### Full-Stack Integration

* Backend serves API endpoints (e.g., `/api/*`)
* Frontend consumes API through typed interfaces
* Use proper CORS configuration for development
* Implement proper error handling on both ends

## Other Considerations

* **Security**: Use environment variables for sensitive data, validate inputs, and sanitize outputs.
* **Performance**: Optimize database queries, use caching where appropriate, and monitor performance.
* **Scalability**: Design APIs and services to handle increased load, use pagination for large datasets, and consider rate limiting.
* **Testing**: Write unit tests for both backend and frontend, use integration tests for API endpoints, and ensure high test coverage.
* **Observability**: Implement logging, monitoring, and alerting to track application health and performance.
* **Add Before Delete**: When making changes, add new features or improvements before removing old code to ensure stability.
* **Documentation**: Keep code well-documented with docstrings, inline comments, and external documentation (e.g., MkDocs).

## Running the Project

You can start and stop the servers using the provided Makefile commands:

```bash
make run # Starts the backend and frontend servers
make stop # Stops the servers
```

Use `make clean` to remove any temporary files or caches.
