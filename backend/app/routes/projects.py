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

"""Project CRUDL routes."""

import falcon
import logging
from datetime import datetime, timezone
from pydantic import ValidationError
from helpers.db import DatabaseHelper
from helpers.schemas import ProjectModel
import uuid

logger = logging.getLogger(__name__)


class ProjectResource:
    """CRUDL operations for projects."""

    async def on_options(self, req, resp) -> None:
        """Handle OPTIONS requests for CORS preflight."""
        resp.status = falcon.HTTP_200

    async def on_get(self, req, resp, project_id: str | None = None) -> None:
        """Get a single project by ID or list all projects."""
        try:
            collection = DatabaseHelper.get_collection("projects")

            if project_id:
                # Get single project
                project_doc = await collection.find_one({"id": project_id})
                if not project_doc:
                    resp.status = falcon.HTTP_404
                    resp.media = {"error": "Project not found"}
                    return

                # Remove MongoDB's _id field
                project_doc.pop("_id", None)
                project = ProjectModel.model_validate(project_doc)
                resp.media = project.model_dump()
            else:
                # List projects with optional filtering
                page = int(req.get_param("page", default=1))
                limit = int(req.get_param("limit", default=20))
                skip = (page - 1) * limit

                # Build filter query
                filter_query = {}
                user_id = req.get_param("user_id")
                if user_id:
                    filter_query["user_id"] = user_id

                cursor = collection.find(filter_query).skip(skip).limit(limit)
                projects = []
                async for project_doc in cursor:
                    project_doc.pop("_id", None)
                    project = ProjectModel.model_validate(project_doc)
                    projects.append(project.model_dump())

                # Get total count for pagination
                total = await collection.count_documents(filter_query)

                resp.media = {
                    "projects": projects,
                    "pagination": {"page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit},
                }

        except Exception as e:
            logger.error("Error retrieving project(s): %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_post(self, req, resp) -> None:
        """Create a new project."""
        try:
            data = await req.get_media()

            # Generate ID if not provided
            if "id" not in data:
                data["id"] = str(uuid.uuid4())

            # Set creation timestamp
            data["created_at"] = datetime.now(timezone.utc)

            # Validate with Pydantic
            project = ProjectModel.model_validate(data)
            collection = DatabaseHelper.get_collection("projects")

            # Check if project with this ID already exists
            existing_project = await collection.find_one({"id": project.id})
            if existing_project:
                resp.status = falcon.HTTP_409
                resp.media = {"error": "Project with this ID already exists"}
                return

            # Insert into database
            await collection.insert_one(project.model_dump())

            resp.status = falcon.HTTP_201
            resp.media = project.model_dump()

        except ValidationError as e:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Validation failed", "details": e.errors()}
        except Exception as e:
            logger.error("Error creating project: %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_put(self, req, resp, project_id: str) -> None:
        """Update an existing project."""
        try:
            data = await req.get_media()
            collection = DatabaseHelper.get_collection("projects")

            # Check if project exists
            existing_project = await collection.find_one({"id": project_id})
            if not existing_project:
                resp.status = falcon.HTTP_404
                resp.media = {"error": "Project not found"}
                return

            # Preserve original ID and creation timestamp
            data["id"] = project_id
            data["created_at"] = existing_project["created_at"]

            # Validate with Pydantic
            project = ProjectModel.model_validate(data)

            # Update in database
            await collection.replace_one({"id": project_id}, project.model_dump())

            resp.media = project.model_dump()

        except ValidationError as e:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Validation failed", "details": e.errors()}
        except Exception as e:
            logger.error("Error updating project: %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_delete(self, req, resp, project_id: str) -> None:
        """Delete a project."""
        try:
            collection = DatabaseHelper.get_collection("projects")

            # Check if project exists
            existing_project = await collection.find_one({"id": project_id})
            if not existing_project:
                resp.status = falcon.HTTP_404
                resp.media = {"error": "Project not found"}
                return

            # Delete the project
            await collection.delete_one({"id": project_id})

            resp.status = falcon.HTTP_204

        except Exception as e:
            logger.error("Error deleting project: %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}
