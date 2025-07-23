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

"""User CRUDL routes."""

import falcon
import logging
import uuid
from datetime import datetime, timezone
from pydantic import ValidationError
from helpers.db import DatabaseHelper
from helpers.schemas import UserModel, ProjectModel, AgentProfileModel

logger = logging.getLogger(__name__)


class UserResource:
    """CRUDL operations for users."""

    async def _ensure_user_defaults(self, user_id: str) -> dict[str, str]:
        """
        Ensure a user has default project and agent profile.

        Creates a default project and a default agent profile if they don't exist.
        This function is idempotent - it can be called multiple times safely.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Dictionary containing the IDs of created/existing resources:
            {
                "project_id": str,
                "agent_profile_id": str
            }
        """
        try:
            # Get existing project and agent profile IDs
            projects_collection = DatabaseHelper.get_collection("projects")
            agent_profiles_collection = DatabaseHelper.get_collection("agent_profiles")

            # Find default project for this user
            default_project = await projects_collection.find_one({"name": "Default Project", "user_id": user_id})

            # Find default agent profile for this user
            default_agent_profile = await agent_profiles_collection.find_one(
                {"name": "Default Assistant", "user_id": user_id}
            )

            # Create missing resources if needed
            project_id = default_project["id"] if default_project else await self._create_default_project(user_id)
            agent_profile_id = (
                default_agent_profile["id"]
                if default_agent_profile
                else await self._create_default_agent_profile(user_id, project_id)
            )

            return {"project_id": project_id, "agent_profile_id": agent_profile_id}

        except Exception as e:
            logger.error("Failed to ensure user defaults for %s: %s", user_id, e)
            raise

    async def _create_default_project(self, user_id: str) -> str:
        """Create a default project for the user."""
        project_id = str(uuid.uuid4())
        logger.info("Creating default project %s for user %s", project_id, user_id)

        project_model = ProjectModel(
            id=project_id,
            name="Default Project",
            description="Your default workspace for conversations",
            created_at=datetime.now(timezone.utc),
        )

        # Add user_id to the project document for easier querying
        project_data = project_model.model_dump()
        project_data["user_id"] = user_id

        projects_collection = DatabaseHelper.get_collection("projects")
        await projects_collection.insert_one(project_data)

        logger.info("Created default project %s for user %s", project_id, user_id)
        return project_id

    async def _create_default_agent_profile(self, user_id: str, project_id: str) -> str:
        """Create a default agent profile for the user."""
        agent_profile_id = str(uuid.uuid4())
        logger.info("Creating default agent profile %s for user %s", agent_profile_id, user_id)

        agent_profile_model = AgentProfileModel(
            id=agent_profile_id,
            name="Default Assistant",
            description="A helpful AI assistant",
            project_id=project_id,
            instructions=["You are an assistant"],
            created_at=datetime.now(timezone.utc),
        )

        # Add user_id to the agent profile document for easier querying
        agent_profile_data = agent_profile_model.model_dump()
        agent_profile_data["user_id"] = user_id

        agent_profiles_collection = DatabaseHelper.get_collection("agent_profiles")
        await agent_profiles_collection.insert_one(agent_profile_data)

        logger.info("Created default agent profile %s for user %s", agent_profile_id, user_id)
        return agent_profile_id

    async def on_options(self, req, resp) -> None:
        """Handle OPTIONS requests for CORS preflight."""
        resp.status = falcon.HTTP_200

    async def on_get(self, req, resp, user_id: str | None = None) -> None:
        """Get a single user by ID or list all users."""
        try:
            collection = DatabaseHelper.get_collection("users")

            if user_id:
                # Get single user
                user_doc = await collection.find_one({"id": user_id})
                if not user_doc:
                    resp.status = falcon.HTTP_404
                    resp.media = {"error": "User not found"}
                    return

                # Remove MongoDB's _id field
                user_doc.pop("_id", None)
                user = UserModel.model_validate(user_doc)
                resp.media = user.model_dump()
            else:
                # List all users with pagination
                page = int(req.get_param("page", default=1))
                limit = int(req.get_param("limit", default=20))
                skip = (page - 1) * limit

                cursor = collection.find({}).skip(skip).limit(limit)
                users = []
                async for user_doc in cursor:
                    user_doc.pop("_id", None)
                    user = UserModel.model_validate(user_doc)
                    users.append(user.model_dump())

                # Get total count for pagination
                total = await collection.count_documents({})

                resp.media = {
                    "users": users,
                    "pagination": {"page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit},
                }

        except Exception as e:
            logger.error("Error retrieving user(s): %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_post(self, req, resp) -> None:
        """Create a new user."""
        logger.info("Starting user creation...")
        try:
            data = await req.get_media()

            # Generate ID if not provided
            if "id" not in data:
                data["id"] = str(uuid.uuid4())

            # Set creation timestamp
            data["created_at"] = datetime.now(timezone.utc)

            # Validate with Pydantic
            user = UserModel.model_validate(data)
            collection = DatabaseHelper.get_collection("users")

            # Check if user with this ID or email already exists
            existing_user = await collection.find_one({"$or": [{"id": user.id}, {"email": user.email}]})
            if existing_user:
                resp.status = falcon.HTTP_409
                resp.media = {"error": "User with this ID or email already exists"}
                return

            # Insert into database
            await collection.insert_one(user.model_dump())
            logger.info("Created user %s with email %s", user.id, user.email)

            # Ensure default project and agent profile are created
            try:
                defaults = await self._ensure_user_defaults(user.id)
                logger.info("Created defaults for user %s: %s", user.id, defaults)
            except Exception as e:
                logger.error("Failed to create defaults for user %s: %s", user.id, e)
                # Don't fail the user creation, but log the error

            resp.status = falcon.HTTP_201
            resp.media = user.model_dump()

        except ValidationError as e:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Validation failed", "details": e.errors()}
        except Exception as e:
            logger.error("Error creating user: %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_put(self, req, resp, user_id: str) -> None:
        """Update an existing user."""
        try:
            data = await req.get_media()
            collection = DatabaseHelper.get_collection("users")

            # Check if user exists
            existing_user = await collection.find_one({"id": user_id})
            if not existing_user:
                resp.status = falcon.HTTP_404
                resp.media = {"error": "User not found"}
                return

            # Preserve original ID and creation timestamp
            data["id"] = user_id
            data["created_at"] = existing_user["created_at"]

            # Validate with Pydantic
            user = UserModel.model_validate(data)

            # Update in database
            await collection.replace_one({"id": user_id}, user.model_dump())

            resp.media = user.model_dump()

        except ValidationError as e:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Validation failed", "details": e.errors()}
        except Exception as e:
            logger.error("Error updating user: %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_delete(self, req, resp, user_id: str) -> None:
        """Delete a user."""
        try:
            collection = DatabaseHelper.get_collection("users")

            # Check if user exists
            existing_user = await collection.find_one({"id": user_id})
            if not existing_user:
                resp.status = falcon.HTTP_404
                resp.media = {"error": "User not found"}
                return

            # Delete the user
            await collection.delete_one({"id": user_id})

            resp.status = falcon.HTTP_204

        except Exception as e:
            logger.error("Error deleting user: %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}
