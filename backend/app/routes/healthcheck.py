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

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Health check route handler."""

from datetime import datetime, timezone
import logging
from helpers.schemas import HealthCheckResponse
from helpers.db import DatabaseHelper
from helpers.mcp import MCPClient

logger = logging.getLogger(__name__)


class HealthCheckResource:
    """Health check route handler."""

    async def on_get(self, req, resp) -> None:
        """Return service health status including database connectivity and MCP health."""
        try:
            # Check database connectivity
            db_health = await DatabaseHelper.health_check()

            # Check MCP health
            mcp_client = MCPClient()
            try:
                mcp_health = await mcp_client.healthz()
                mcp_status = mcp_health.get("status") == "healthy"
            except Exception as mcp_exc:
                logger.warning("MCP health check failed: %s", mcp_exc)
                mcp_status = False

            # Determine overall health status
            all_healthy = all(db_health.values()) and mcp_status
            status = "healthy" if all_healthy else "unhealthy"

            health_data = HealthCheckResponse(
                status=status, timestamp=datetime.now(tz=timezone.utc), service="chatbot-backend", version="0.5"
            )

            # Add database and MCP health details
            response_data = health_data.model_dump()
            response_data["databases"] = db_health
            response_data["mcp"] = {"healthy": mcp_status}

            resp.media = response_data

        except Exception as e:
            logger.error("Health check failed: %s", e)
            resp.status = 503  # Service Unavailable
            resp.media = {
                "status": "unhealthy",
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "service": "chatbot-backend",
                "version": "0.5",
                "error": str(e),
            }
