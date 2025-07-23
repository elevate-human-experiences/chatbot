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

"""User setup helper functions."""

import logging
import uuid
from datetime import datetime, timezone
from helpers.db import DatabaseHelper
from helpers.schemas import UserModel, ProjectModel, AgentProfileModel

logger = logging.getLogger(__name__)


async def ensure_user(user_id: str, name: str, email: str) -> dict[str, str]:
    """
    Ensure a user exists with default project and agent profile.

    Creates the user, a default project, and a default agent profile if they don't exist.
    This function is idempotent - it can be called multiple times safely.

    Args:
        user_id: Unique identifier for the user
        name: Full name of the user
        email: Email address of the user

    Returns:
        Dictionary containing the IDs of created/existing resources:
        {
            "user_id": str,
            "project_id": str,
            "agent_profile_id": str
        }
    """
    try:
        # Check if user already exists
        users_collection = DatabaseHelper.get_collection("users")
        existing_user = await users_collection.find_one({"id": user_id})

        if existing_user:
            logger.info("User %s already exists, checking default resources", user_id)

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
            project_id = default_project["id"] if default_project else await _create_default_project(user_id)
            agent_profile_id = (
                default_agent_profile["id"]
                if default_agent_profile
                else await _create_default_agent_profile(user_id, project_id)
            )

            return {"user_id": user_id, "project_id": project_id, "agent_profile_id": agent_profile_id}

        # Create new user
        logger.info("Creating new user %s", user_id)
        user_model = UserModel(id=user_id, name=name, email=email, created_at=datetime.now(timezone.utc))

        await users_collection.insert_one(user_model.model_dump())

        # Create default project
        project_id = await _create_default_project(user_id)

        # Create default agent profile
        agent_profile_id = await _create_default_agent_profile(user_id, project_id)

        logger.info("Successfully created user %s with default resources", user_id)

        return {"user_id": user_id, "project_id": project_id, "agent_profile_id": agent_profile_id}

    except Exception as e:
        logger.error("Failed to ensure user %s: %s", user_id, e)
        raise


async def _create_default_project(user_id: str) -> str:
    """Create a default project for the user."""
    project_id = str(uuid.uuid4())

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


async def _create_default_agent_profile(user_id: str, project_id: str) -> str:
    """Create a default agent profile for the user."""
    agent_profile_id = str(uuid.uuid4())

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
