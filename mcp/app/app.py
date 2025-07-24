# MIT-0 License
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
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Application entry point for the Falcon ASGI app."""

import falcon.asgi
from routes.mcp import MCPResource
from routes.healthcheck import HealthCheckResource
from falcon import Request, Response, media
from pydantic import ValidationError
import json
import traceback
from functools import partial
from typing import Any
from helpers.logger import setup_logging
from helpers.encoder import CustomJsonEncoder, CustomJsonDecoder
import logging

# Create a custom logger
setup_logging()
logger = logging.getLogger(__name__)

# Base URL where this API is served (used by the middleware to fetch its metadata)
API_BASE_URL = "http://localhost:8080"  # ← adjust to your real public URL


async def handle_validation_error(
    req: Request, resp: Response, exception: ValidationError, params: Any
) -> None:
    """Handle Pydantic ValidationError exceptions."""
    logger.error(f"Validation error: {exception}")
    resp.status = falcon.HTTP_422
    resp.media = {
        "title": "Unprocessable Entity",
        "description": "The request contains invalid data.",
        "errors": exception.errors(),
    }


async def custom_handle_uncaught_exception(
    req: Request, resp: Response, exception: Exception, _: Any
) -> None:
    """Handle uncaught exceptions."""
    traceback.print_exc()
    resp.status = falcon.HTTP_500
    resp.media = {"title": "Internal Server Error", "message": str(exception)}


# -----------------------------------------------------------------------------
# Assemble middleware and app
# -----------------------------------------------------------------------------

middleware = [
    # Protect all routes by default (per RFC 9728 Resource Server behavior)
    # Note: OAuth middleware is commented out for now
]

# Create an async Falcon app instance
app = falcon.asgi.App(middleware=middleware, cors_enable=True)

# Register our error handlers
app.add_error_handler(ValidationError, handle_validation_error)
app.add_error_handler(Exception, custom_handle_uncaught_exception)

# Install our custom JSON encoder/decoder
json_handler = media.JSONHandler(
    dumps=partial(json.dumps, cls=CustomJsonEncoder, sort_keys=True),
    loads=partial(json.loads, cls=CustomJsonDecoder),
)
app.req_options.media_handlers.update({"application/json": json_handler})
app.resp_options.media_handlers.update({"application/json": json_handler})

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

# Health check (no auth required)
app.add_route("/healthz", HealthCheckResource())

# Your MCP endpoint
app.add_route("/mcp", MCPResource())

# -----------------------------------------------------------------------------
# Uvicorn entrypoint
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
