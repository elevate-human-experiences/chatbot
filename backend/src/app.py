# MIT License
#
# Copyright (c) 2025 Elevate Human Experiences, LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Falcon backend application with chat completions and health check."""

import falcon
import falcon.asgi
import falcon.media
import logging
import os
from dotenv import load_dotenv
from helpers.logger import setup_logging
from helpers import json_encoder
from routes.healthcheck import HealthCheckResource
from routes.chat import ChatCompletionsResource
from routes.users import UserResource
from routes.projects import ProjectResource
from routes.agent_profiles import AgentProfileResource
from routes.conversations import ConversationResource, ConversationMessageResource
from routes.instructions import InstructionResource

# Load environment variables from .env file
load_dotenv()

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


class CORSMiddleware:
    """CORS middleware to handle cross-origin requests."""

    async def process_request(self, req, resp):
        """Process the request to add CORS headers."""
        resp.set_header("Access-Control-Allow-Origin", "*")
        resp.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        resp.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        resp.set_header("Access-Control-Max-Age", "86400")

    async def process_response(self, req, resp, resource, req_succeeded):
        """Process the response to ensure CORS headers are set."""
        if not resp.get_header("Access-Control-Allow-Origin"):
            resp.set_header("Access-Control-Allow-Origin", "*")


def create_app() -> falcon.asgi.App:
    """Create and configure the Falcon ASGI application."""
    middleware = [CORSMiddleware()]
    app = falcon.asgi.App(middleware=middleware)

    # Configure custom JSON encoder for media handling
    json_handler = falcon.media.JSONHandler(dumps=json_encoder.dumps, loads=json_encoder.loads)
    app.req_options.media_handlers[falcon.MEDIA_JSON] = json_handler
    app.resp_options.media_handlers[falcon.MEDIA_JSON] = json_handler

    # Health and chat routes
    app.add_route("/health", HealthCheckResource())
    app.add_route("/chat/completions", ChatCompletionsResource())

    # CRUDL routes for core entities
    # Users
    app.add_route("/users", UserResource())
    app.add_route("/users/{user_id}", UserResource())

    # Projects
    app.add_route("/projects", ProjectResource())
    app.add_route("/projects/{project_id}", ProjectResource())

    # Agent Profiles (nested under projects)
    app.add_route("/projects/{project_id}/profiles", AgentProfileResource())
    app.add_route("/projects/{project_id}/profiles/{profile_id}", AgentProfileResource())

    # Instructions (nested under agent profiles within projects)
    app.add_route("/projects/{project_id}/profiles/{profile_id}/instructions", InstructionResource())
    app.add_route(
        "/projects/{project_id}/profiles/{profile_id}/instructions/{instruction_index:int}", InstructionResource()
    )

    # Conversations (nested under projects)
    app.add_route("/projects/{project_id}/conversations", ConversationResource())
    app.add_route("/projects/{project_id}/conversations/{conversation_id}", ConversationResource())
    app.add_route("/projects/{project_id}/conversations/{conversation_id}/messages", ConversationMessageResource())

    logger.info("Falcon app created with CORS middleware and all CRUDL routes")
    return app


# Create the application instance
app = create_app()


def main():
    """Main entry point for development."""
    import uvicorn

    port = int(os.getenv("PORT", 8080))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "false").lower() == "true"

    logger.info("Starting chatbot backend development server on %s:%s...", host, port)
    uvicorn.run("app:app", host=host, port=port, reload=debug, log_level="info")


if __name__ == "__main__":
    main()
