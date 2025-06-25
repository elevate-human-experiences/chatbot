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

"""Instructions management routes for agent profiles."""

import falcon
import logging
from pydantic import ValidationError, BaseModel, Field
from helpers.db import DatabaseHelper
from helpers.schemas import AgentProfileModel

logger = logging.getLogger(__name__)


class InstructionRequest(BaseModel):
    """Request model for instruction operations."""

    content: str = Field(..., description="Text content of the instruction")


class InstructionResource:
    """CRUDL operations for instructions within agent profiles."""

    async def on_options(self, req, resp) -> None:
        """Handle OPTIONS requests for CORS preflight."""
        resp.status = falcon.HTTP_200

    async def on_get(self, req, resp, project_id: str, profile_id: str, instruction_index: int | None = None) -> None:
        """Get a specific instruction by index or list all instructions for an agent profile within a project."""
        try:
            collection = DatabaseHelper.get_collection("agent_profiles")

            # Get the agent profile within the specified project
            profile_doc = await collection.find_one({"id": profile_id, "project_id": project_id})
            if not profile_doc:
                resp.status = falcon.HTTP_404
                resp.media = {"error": "Agent profile not found"}
                return

            profile_doc.pop("_id", None)
            profile = AgentProfileModel.model_validate(profile_doc)

            if instruction_index is not None:
                # Get specific instruction by index
                if instruction_index < 0 or instruction_index >= len(profile.instructions):
                    resp.status = falcon.HTTP_404
                    resp.media = {"error": "Instruction not found"}
                    return

                resp.media = {"index": instruction_index, "content": profile.instructions[instruction_index]}
            else:
                # List all instructions
                instructions = [
                    {"index": i, "content": instruction} for i, instruction in enumerate(profile.instructions)
                ]
                resp.media = {
                    "project_id": project_id,
                    "profile_id": profile_id,
                    "instructions": instructions,
                    "total": len(instructions),
                }

        except Exception as e:
            logger.error("Error retrieving instruction(s): %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_post(self, req, resp, project_id: str, profile_id: str) -> None:
        """Add a new instruction to an agent profile within a project."""
        try:
            data = await req.get_media()
            instruction_req = InstructionRequest.model_validate(data)
            collection = DatabaseHelper.get_collection("agent_profiles")

            # Check if agent profile exists within the specified project
            existing_profile = await collection.find_one({"id": profile_id, "project_id": project_id})
            if not existing_profile:
                resp.status = falcon.HTTP_404
                resp.media = {"error": "Agent profile not found"}
                return

            # Add instruction to the profile
            await collection.update_one(
                {"id": profile_id, "project_id": project_id}, {"$push": {"instructions": instruction_req.content}}
            )

            # Get updated profile
            updated_profile = await collection.find_one({"id": profile_id, "project_id": project_id})
            updated_profile.pop("_id", None)
            profile = AgentProfileModel.model_validate(updated_profile)

            # Return the new instruction with its index
            new_index = len(profile.instructions) - 1
            resp.status = falcon.HTTP_201
            resp.media = {
                "index": new_index,
                "content": instruction_req.content,
                "project_id": project_id,
                "profile_id": profile_id,
            }

        except ValidationError as e:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Validation failed", "details": e.errors()}
        except Exception as e:
            logger.error("Error adding instruction: %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_put(self, req, resp, project_id: str, profile_id: str, instruction_index: int) -> None:
        """Update an existing instruction in an agent profile within a project."""
        try:
            data = await req.get_media()
            instruction_req = InstructionRequest.model_validate(data)
            collection = DatabaseHelper.get_collection("agent_profiles")

            # Check if agent profile exists within the specified project
            existing_profile = await collection.find_one({"id": profile_id, "project_id": project_id})
            if not existing_profile:
                resp.status = falcon.HTTP_404
                resp.media = {"error": "Agent profile not found"}
                return

            existing_profile.pop("_id", None)
            profile = AgentProfileModel.model_validate(existing_profile)

            # Check if instruction index is valid
            if instruction_index < 0 or instruction_index >= len(profile.instructions):
                resp.status = falcon.HTTP_404
                resp.media = {"error": "Instruction not found"}
                return

            # Update the specific instruction
            await collection.update_one(
                {"id": profile_id, "project_id": project_id},
                {"$set": {f"instructions.{instruction_index}": instruction_req.content}},
            )

            resp.media = {
                "index": instruction_index,
                "content": instruction_req.content,
                "project_id": project_id,
                "profile_id": profile_id,
            }

        except ValidationError as e:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Validation failed", "details": e.errors()}
        except Exception as e:
            logger.error("Error updating instruction: %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def on_delete(self, req, resp, project_id: str, profile_id: str, instruction_index: int) -> None:
        """Delete an instruction from an agent profile within a project."""
        try:
            collection = DatabaseHelper.get_collection("agent_profiles")

            # Check if agent profile exists within the specified project
            existing_profile = await collection.find_one({"id": profile_id, "project_id": project_id})
            if not existing_profile:
                resp.status = falcon.HTTP_404
                resp.media = {"error": "Agent profile not found"}
                return

            existing_profile.pop("_id", None)
            profile = AgentProfileModel.model_validate(existing_profile)

            # Check if instruction index is valid
            if instruction_index < 0 or instruction_index >= len(profile.instructions):
                resp.status = falcon.HTTP_404
                resp.media = {"error": "Instruction not found"}
                return

            # Remove the instruction by index
            # First get the current instructions
            instructions = profile.instructions.copy()
            instructions.pop(instruction_index)

            # Update the entire instructions array
            await collection.update_one(
                {"id": profile_id, "project_id": project_id}, {"$set": {"instructions": instructions}}
            )

            resp.status = falcon.HTTP_204

        except Exception as e:
            logger.error("Error deleting instruction: %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}
