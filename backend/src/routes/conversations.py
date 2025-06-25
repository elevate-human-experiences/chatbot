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

"""Conversation CRUDL routes."""

import falcon
import logging
from datetime import datetime, timezone
from pydantic import ValidationError
from helpers.db import DatabaseHelper
from helpers.schemas import ConversationModel
import uuid

logger = logging.getLogger(__name__)


class ConversationResource:
    """CRUDL operations for conversations."""

    async def on_options(self, req, resp, project_id: str, conversation_id: str | None = None) -> None:
        """Handle OPTIONS requests for CORS preflight."""
        resp.status = falcon.HTTP_200

    async def on_get(self, req, resp, project_id: str, conversation_id: str | None = None) -> None:
        """Get a single conversation by ID or list all conversations within a project."""
        try:
            collection = DatabaseHelper.get_collection("conversations")

            if conversation_id:
                # Get single conversation within the specified project
                conversation_doc = await collection.find_one({"id": conversation_id, "project_id": project_id})
                if not conversation_doc:
                    resp.status = falcon.HTTP_404
                    resp.media = {"error": "Conversation not found"}
                    return

                # Remove MongoDB's _id field
                conversation_doc.pop("_id", None)
                conversation = ConversationModel.model_validate(conversation_doc)
                resp.media = conversation.model_dump()
            else:
                # List conversations within the specified project with filtering and pagination
                page = int(req.get_param("page", default=1))
                limit = int(req.get_param("limit", default=20))
                skip = (page - 1) * limit

                # Filter parameters
                user_id = req.get_param("user_id")
                agent_profile_id = req.get_param("agent_profile_id")

                # Build query - always filter by project_id
                query = {"project_id": project_id}
                if user_id:
                    query["user_id"] = user_id
                if agent_profile_id:
                    query["agent_profile_id"] = agent_profile_id

                cursor = collection.find(query).skip(skip).limit(limit).sort("started_at", -1)
                conversations = []
                async for conversation_doc in cursor:
                    conversation_doc.pop("_id", None)
                    conversation = ConversationModel.model_validate(conversation_doc)
                    conversations.append(conversation.model_dump())

                # Get total count for pagination
                total = await collection.count_documents(query)

                resp.media = {
                    "conversations": conversations,
                    "pagination": {"page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit},
                    "filters": {"project_id": project_id, "user_id": user_id, "agent_profile_id": agent_profile_id},
                }

        except Exception as e:
            logger.error("Error retrieving conversation(s): %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_post(self, req, resp, project_id: str) -> None:
        """Create a new conversation within a project."""
        try:
            data = await req.get_media()

            # Generate ID if not provided
            if "id" not in data:
                data["id"] = str(uuid.uuid4())

            # Set project_id from URL parameter
            data["project_id"] = project_id

            # Set start timestamp
            data["started_at"] = datetime.now(timezone.utc)

            # Initialize empty messages list if not provided
            if "messages" not in data:
                data["messages"] = []

            # Validate with Pydantic
            conversation = ConversationModel.model_validate(data)
            collection = DatabaseHelper.get_collection("conversations")

            # Check if conversation with this ID already exists
            existing_conversation = await collection.find_one({"id": conversation.id})
            if existing_conversation:
                resp.status = falcon.HTTP_409
                resp.media = {"error": "Conversation with this ID already exists"}
                return

            # Insert into database
            await collection.insert_one(conversation.model_dump())

            resp.status = falcon.HTTP_201
            resp.media = conversation.model_dump()

        except ValidationError as e:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Validation failed", "details": e.errors()}
        except Exception as e:
            logger.error("Error creating conversation: %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_put(self, req, resp, project_id: str, conversation_id: str) -> None:
        """Update an existing conversation within a project."""
        try:
            data = await req.get_media()
            collection = DatabaseHelper.get_collection("conversations")

            # Check if conversation exists within the specified project
            existing_conversation = await collection.find_one({"id": conversation_id, "project_id": project_id})
            if not existing_conversation:
                resp.status = falcon.HTTP_404
                resp.media = {"error": "Conversation not found"}
                return

            # Preserve original ID, project_id, and start timestamp
            data["id"] = conversation_id
            data["project_id"] = project_id
            data["started_at"] = existing_conversation["started_at"]

            # Validate with Pydantic
            conversation = ConversationModel.model_validate(data)

            # Update in database - filter by both id and project_id
            await collection.replace_one({"id": conversation_id, "project_id": project_id}, conversation.model_dump())

            resp.media = conversation.model_dump()

        except ValidationError as e:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Validation failed", "details": e.errors()}
        except Exception as e:
            logger.error("Error updating conversation: %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_delete(self, req, resp, project_id: str, conversation_id: str) -> None:
        """Delete a conversation within a project."""
        try:
            collection = DatabaseHelper.get_collection("conversations")

            # Check if conversation exists within the specified project
            existing_conversation = await collection.find_one({"id": conversation_id, "project_id": project_id})
            if not existing_conversation:
                resp.status = falcon.HTTP_404
                resp.media = {"error": "Conversation not found"}
                return

            # Delete the conversation
            await collection.delete_one({"id": conversation_id, "project_id": project_id})

            resp.status = falcon.HTTP_204

        except Exception as e:
            logger.error("Error deleting conversation: %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}


class ConversationMessageResource:
    """Resource for adding messages to conversations."""

    async def on_options(self, req, resp, project_id: str, conversation_id: str) -> None:
        """Handle OPTIONS requests for CORS preflight."""
        resp.status = falcon.HTTP_200

    async def on_post(self, req, resp, project_id: str, conversation_id: str) -> None:
        """Add a message to an existing conversation within a project."""
        try:
            data = await req.get_media()
            collection = DatabaseHelper.get_collection("conversations")

            # Check if conversation exists within the specified project
            existing_conversation = await collection.find_one({"id": conversation_id, "project_id": project_id})
            if not existing_conversation:
                resp.status = falcon.HTTP_404
                resp.media = {"error": "Conversation not found"}
                return

            # Validate the message data
            from helpers.schemas import MessageModel

            message = MessageModel.model_validate(data)

            # Add message to conversation
            await collection.update_one(
                {"id": conversation_id, "project_id": project_id}, {"$push": {"messages": message.model_dump()}}
            )

            # Return the updated conversation
            updated_conversation = await collection.find_one({"id": conversation_id, "project_id": project_id})
            updated_conversation.pop("_id", None)
            conversation = ConversationModel.model_validate(updated_conversation)

            resp.status = falcon.HTTP_201
            resp.media = conversation.model_dump()

        except ValidationError as e:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Validation failed", "details": e.errors()}
        except Exception as e:
            logger.error("Error adding message to conversation: %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}
