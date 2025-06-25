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

"""Agent Profile CRUDL routes."""

import falcon
import logging
from datetime import datetime, timezone
from pydantic import ValidationError
from helpers.db import DatabaseHelper
from helpers.schemas import AgentProfileModel
import uuid

logger = logging.getLogger(__name__)


class AgentProfileResource:
    """CRUDL operations for agent profiles."""

    async def on_options(self, req, resp) -> None:
        """Handle OPTIONS requests for CORS preflight."""
        resp.status = falcon.HTTP_200

    async def on_get(self, req, resp, project_id: str, profile_id: str | None = None) -> None:
        """Get a single agent profile by ID or list all agent profiles within a project."""
        try:
            collection = DatabaseHelper.get_collection("agent_profiles")

            if profile_id:
                # Get single agent profile within the specified project
                profile_doc = await collection.find_one({"id": profile_id, "project_id": project_id})
                if not profile_doc:
                    resp.status = falcon.HTTP_404
                    resp.media = {"error": "Agent profile not found"}
                    return

                # Remove MongoDB's _id field
                profile_doc.pop("_id", None)
                profile = AgentProfileModel.model_validate(profile_doc)
                resp.media = profile.model_dump()
            else:
                # List agent profiles within the specified project
                page = int(req.get_param("page", default=1))
                limit = int(req.get_param("limit", default=20))
                skip = (page - 1) * limit

                # Build filter query - always filter by project_id
                filter_query = {"project_id": project_id}
                user_id = req.get_param("user_id")
                if user_id:
                    filter_query["user_id"] = user_id

                cursor = collection.find(filter_query).skip(skip).limit(limit)
                profiles = []
                async for profile_doc in cursor:
                    profile_doc.pop("_id", None)
                    profile = AgentProfileModel.model_validate(profile_doc)
                    profiles.append(profile.model_dump())

                # Get total count for pagination
                total = await collection.count_documents(filter_query)

                resp.media = {
                    "agent_profiles": profiles,
                    "pagination": {"page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit},
                }

        except Exception as e:
            logger.error("Error retrieving agent profile(s): %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_post(self, req, resp, project_id: str) -> None:
        """Create a new agent profile within a project."""
        try:
            data = await req.get_media()

            # Generate ID if not provided
            if "id" not in data:
                data["id"] = str(uuid.uuid4())

            # Set project_id from URL parameter
            data["project_id"] = project_id

            # Set creation timestamp
            data["created_at"] = datetime.now(timezone.utc)

            # Validate with Pydantic
            profile = AgentProfileModel.model_validate(data)
            collection = DatabaseHelper.get_collection("agent_profiles")

            # Check if agent profile with this ID already exists
            existing_profile = await collection.find_one({"id": profile.id})
            if existing_profile:
                resp.status = falcon.HTTP_409
                resp.media = {"error": "Agent profile with this ID already exists"}
                return

            # Insert into database
            await collection.insert_one(profile.model_dump())

            resp.status = falcon.HTTP_201
            resp.media = profile.model_dump()

        except ValidationError as e:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Validation failed", "details": e.errors()}
        except Exception as e:
            logger.error("Error creating agent profile: %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_put(self, req, resp, project_id: str, profile_id: str) -> None:
        """Update an existing agent profile within a project."""
        try:
            data = await req.get_media()
            collection = DatabaseHelper.get_collection("agent_profiles")

            # Check if agent profile exists within the specified project
            existing_profile = await collection.find_one({"id": profile_id, "project_id": project_id})
            if not existing_profile:
                resp.status = falcon.HTTP_404
                resp.media = {"error": "Agent profile not found"}
                return

            # Preserve original ID, project_id, and creation timestamp
            data["id"] = profile_id
            data["project_id"] = project_id
            data["created_at"] = existing_profile["created_at"]

            # Validate with Pydantic
            profile = AgentProfileModel.model_validate(data)

            # Update in database - filter by both id and project_id
            await collection.replace_one({"id": profile_id, "project_id": project_id}, profile.model_dump())

            resp.media = profile.model_dump()

        except ValidationError as e:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Validation failed", "details": e.errors()}
        except Exception as e:
            logger.error("Error updating agent profile: %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_delete(self, req, resp, project_id: str, profile_id: str) -> None:
        """Delete an agent profile within a project."""
        try:
            collection = DatabaseHelper.get_collection("agent_profiles")

            # Check if agent profile exists within the specified project
            existing_profile = await collection.find_one({"id": profile_id, "project_id": project_id})
            if not existing_profile:
                resp.status = falcon.HTTP_404
                resp.media = {"error": "Agent profile not found"}
                return

            # Delete the agent profile
            await collection.delete_one({"id": profile_id, "project_id": project_id})

            resp.status = falcon.HTTP_204

        except Exception as e:
            logger.error("Error deleting agent profile: %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}
