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

"""Conversation CRUDL routes."""

import falcon
import logging
import json
import asyncio
from datetime import datetime, timezone
from pydantic import ValidationError
from typing import Any
from helpers.db import DatabaseHelper
from helpers.schemas import ConversationModel, MessageModel
from helpers.llm import LLMHelper
from helpers.mcp import MCPClient
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
            data = await req.get_media() or {}

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

            # Ensure required fields for empty conversation
            if "agent_profile_id" not in data:
                resp.status = falcon.HTTP_400
                resp.media = {"error": "agent_profile_id is required"}
                return

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
    """Resource for adding messages to conversations with LLM streaming support."""

    async def on_options(self, req, resp, project_id: str, conversation_id: str) -> None:
        """Handle OPTIONS requests for CORS preflight."""
        resp.status = falcon.HTTP_200
        resp.set_header("Access-Control-Allow-Origin", "*")
        resp.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        resp.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    async def on_post(self, req, resp, project_id: str, conversation_id: str) -> None:
        """Add a message to an existing conversation and stream LLM response."""
        try:
            data = await req.get_media()
            collection = DatabaseHelper.get_collection("conversations")

            # Check if conversation exists within the specified project
            existing_conversation = await collection.find_one({"id": conversation_id, "project_id": project_id})
            if not existing_conversation:
                resp.status = falcon.HTTP_404
                resp.media = {"error": "Conversation not found"}
                return

            # Validate the message data - expect only basic message format
            if "role" not in data or "content" not in data:
                resp.status = falcon.HTTP_400
                resp.media = {"error": "Message must have 'role' and 'content' fields"}
                return

            user_message = MessageModel.model_validate(data)
            if user_message.role != "user":
                # System, assistant, and tool messages should not be added directly by users
                resp.status = falcon.HTTP_400
                resp.media = {"error": "Only user messages can be added directly"}
                return

            # Add user message to conversation
            await collection.update_one(
                {"id": conversation_id, "project_id": project_id}, {"$push": {"messages": user_message.model_dump()}}
            )

            # Get the updated conversation with the user message
            updated_conversation = await collection.find_one({"id": conversation_id, "project_id": project_id})
            conversation_model = ConversationModel.model_validate(updated_conversation)

            # If this is not a user message, just return the updated conversation
            if user_message.role != "user":
                resp.status = falcon.HTTP_201
                resp.media = conversation_model.model_dump()
                return

            # Get agent profile for system instructions
            agent_profile_id = conversation_model.agent_profile_id

            if agent_profile_id:
                profiles_collection = DatabaseHelper.get_collection("profiles")
                agent_profile = await profiles_collection.find_one({"id": agent_profile_id, "project_id": project_id})

            # Prepare messages for LLM (extract just role and content)
            messages = []
            for msg in conversation_model.messages:
                messages.append({"role": msg.role, "content": msg.content or ""})

            # Stream the LLM response
            await self._handle_streaming_llm_response(req, resp, messages, conversation_id, project_id, agent_profile)

        except ValidationError as e:
            resp.status = falcon.HTTP_400
            resp.media = {"error": "Validation failed", "details": e.errors()}
        except Exception as e:
            logger.error("Error adding message to conversation: %s", e)
            resp.status = falcon.HTTP_500
            resp.media = {"error": "Internal server error"}

    async def _handle_streaming_llm_response(
        self, req, resp, messages: list[dict], conversation_id: str, project_id: str, agent_profile: dict
    ) -> None:
        """Handle streaming LLM response and save the complete message."""

        def make_json_serializable(obj):
            """Recursively convert objects to JSON-serializable format."""
            if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump")):
                return obj.model_dump()
            if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
                return obj.dict()
            if isinstance(obj, list):
                return [make_json_serializable(item) for item in obj]
            if isinstance(obj, dict):
                return {k: make_json_serializable(v) for k, v in obj.items()}
            return obj

        system_prompt = "\n\n".join(agent_profile.get("instructions", ["You are a helpful assistant."]))
        try:
            # Set up SSE headers
            resp.content_type = "text/event-stream"
            resp.cache_control = ["no-cache", "no-store", "must-revalidate"]
            resp.headers["Connection"] = "keep-alive"
            resp.headers["Access-Control-Allow-Origin"] = "*"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
            resp.headers["X-Accel-Buffering"] = "no"  # Disable nginx buffering
            resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"

            mcp_client = MCPClient()
            tools = []
            tool_name_mapping = {}  # Map modified names back to original names

            try:
                raw_tools = await mcp_client.list_tools()

                for tool in raw_tools:
                    original_name = tool["name"]
                    modified_name = original_name.replace(".", "__")
                    tool_name_mapping[modified_name] = original_name

                    # Create a copy with modified name for LLM
                    tool_copy = tool.copy()
                    tool_copy["name"] = modified_name
                    tool_copy.pop("annotations", None)  # Remove annotations if not needed
                    tool_copy.pop("output_schema", None)  # Remove output schema if not needed
                    tool_copy.pop("title", None)
                    tools.append(tool_copy)

                logger.info("Successfully loaded %d tools from MCP server", len(tools))
            except Exception as e:
                logger.warning("Failed to load tools from MCP server: %s", e)
                tools = []
                tool_name_mapping = {}

            async def event_stream():
                """Generate server-sent events for streaming response."""
                try:
                    # Send initial heartbeat to establish connection
                    yield b": heartbeat\n\n"
                    await asyncio.sleep(0.001)

                    # Initialize content collectors
                    assistant_content = ""
                    assistant_thinking = ""
                    assistant_reasoning = ""
                    tool_calls = []
                    current_tool = None
                    current_json = ""
                    chunk_count = 0

                    # Stream using the updated LLM helper method
                    async for chunk in LLMHelper.stream_chat_completion(
                        messages=messages,
                        model="claude-sonnet-4-20250514",
                        temperature=1.0,
                        max_tokens=4096,
                        system=system_prompt,
                        thinking={"type": "enabled", "budget_tokens": 1024},
                        tools=tools if tools else None,
                        tool_choice={"type": "auto"} if tools else None,
                    ):
                        chunk_count += 1

                        # Debug logging
                        logger.debug(f"Processing chunk {chunk_count}: type={getattr(chunk, 'type', 'unknown')}")

                        # Handle streaming events
                        if hasattr(chunk, "type"):
                            if chunk.type == "content_block_start":
                                logger.debug(f"Content block start: {getattr(chunk, 'content_block', {})}")
                                if hasattr(chunk, "content_block") and chunk.content_block.type == "tool_use":
                                    current_tool = {
                                        "id": chunk.content_block.id,
                                        "name": chunk.content_block.name,
                                        "input": "",
                                    }
                                    # Stream tool start event
                                    tool_start_chunk = {
                                        "id": f"chatcmpl-{hash(str(messages))}",
                                        "object": "chat.completion.chunk",
                                        "model": "claude-sonnet-4-20250514",
                                        "choices": [
                                            {
                                                "index": 0,
                                                "delta": {
                                                    "tool_calls": [
                                                        {
                                                            "id": current_tool["id"],
                                                            "type": "function",
                                                            "function": {"name": current_tool["name"], "arguments": ""},
                                                        }
                                                    ]
                                                },
                                                "finish_reason": None,
                                            }
                                        ],
                                    }
                                    yield f"data: {json.dumps(tool_start_chunk)}\n\n".encode()
                                    await asyncio.sleep(0.001)  # Small delay to ensure proper streaming

                            elif chunk.type == "content_block_delta":
                                if hasattr(chunk, "delta"):
                                    # Regular text content
                                    if hasattr(chunk.delta, "text"):
                                        assistant_content += chunk.delta.text
                                        # Stream text chunk
                                        openai_chunk = {
                                            "id": f"chatcmpl-{hash(str(messages))}",
                                            "object": "chat.completion.chunk",
                                            "model": "claude-sonnet-4-20250514",
                                            "choices": [
                                                {
                                                    "index": 0,
                                                    "delta": {"content": chunk.delta.text},
                                                    "finish_reason": None,
                                                }
                                            ],
                                        }
                                        yield f"data: {json.dumps(openai_chunk)}\n\n".encode()
                                        await asyncio.sleep(0.001)  # Small delay to ensure proper streaming

                                    # Thinking content
                                    elif hasattr(chunk.delta, "thinking"):
                                        assistant_thinking += chunk.delta.thinking
                                        thinking_chunk = {
                                            "id": f"chatcmpl-{hash(str(messages))}",
                                            "object": "chat.completion.chunk",
                                            "model": "claude-sonnet-4-20250514",
                                            "choices": [
                                                {
                                                    "index": 0,
                                                    "delta": {"thinking": chunk.delta.thinking},
                                                    "finish_reason": None,
                                                }
                                            ],
                                        }
                                        yield f"data: {json.dumps(thinking_chunk)}\n\n".encode()
                                        await asyncio.sleep(0.001)  # Small delay to ensure proper streaming

                                    # Tool input streaming
                                    elif hasattr(chunk.delta, "partial_json") and current_tool:
                                        current_json += chunk.delta.partial_json
                                        # Stream tool arguments update
                                        tool_args_chunk = {
                                            "id": f"chatcmpl-{hash(str(messages))}",
                                            "object": "chat.completion.chunk",
                                            "model": "claude-sonnet-4-20250514",
                                            "choices": [
                                                {
                                                    "index": 0,
                                                    "delta": {
                                                        "tool_calls": [
                                                            {
                                                                "id": current_tool["id"],
                                                                "type": "function",
                                                                "function": {"arguments": chunk.delta.partial_json},
                                                            }
                                                        ]
                                                    },
                                                    "finish_reason": None,
                                                }
                                            ],
                                        }
                                        yield f"data: {json.dumps(tool_args_chunk)}\n\n".encode()
                                        await asyncio.sleep(0.001)  # Small delay to ensure proper streaming

                            elif chunk.type == "content_block_stop":
                                logger.debug("Content block stop")
                                if current_tool:
                                    if current_json:
                                        try:
                                            current_tool["input"] = json.loads(current_json)
                                            tool_calls.append(current_tool)
                                        except json.JSONDecodeError as e:
                                            logger.warning("Failed to parse tool JSON: %s", e)
                                    current_tool = None
                                    current_json = ""

                            elif chunk.type == "message_delta":
                                logger.debug(f"Message delta: {getattr(chunk, 'delta', {})}")
                                if hasattr(chunk, "delta") and hasattr(chunk.delta, "stop_reason"):
                                    logger.debug("Message completed with reason: %s", chunk.delta.stop_reason)

                        # Handle any other chunk types that might contain content
                        else:
                            logger.debug(f"Unhandled chunk type: {type(chunk)} - {chunk}")
                            # Try to extract any text content from unexpected chunk formats
                            if hasattr(chunk, "delta") and hasattr(chunk.delta, "text"):
                                assistant_content += chunk.delta.text
                                openai_chunk = {
                                    "id": f"chatcmpl-{hash(str(messages))}",
                                    "object": "chat.completion.chunk",
                                    "model": "claude-sonnet-4-20250514",
                                    "choices": [
                                        {"index": 0, "delta": {"content": chunk.delta.text}, "finish_reason": None}
                                    ],
                                }
                                yield f"data: {json.dumps(openai_chunk)}\n\n".encode()
                                await asyncio.sleep(0.001)  # Small delay to ensure proper streaming

                    # Execute tool calls if any
                    tool_results = []
                    if tool_calls:
                        for tool_call in tool_calls:
                            try:
                                logger.debug(
                                    f"Invoking tool: id={tool_call['id']}, name={tool_call['name']}, input={tool_call['input']}"
                                )
                                # Map modified tool name back to original name
                                original_tool_name = tool_name_mapping.get(tool_call["name"], tool_call["name"])

                                # Execute the tool via MCP client
                                tool_result = await mcp_client.invoke_tool(
                                    method="tools/call",
                                    params={"name": original_tool_name, "arguments": tool_call["input"]},
                                )
                                logger.debug(
                                    f"Tool result for id={tool_call['id']}, name={original_tool_name}: {tool_result}"
                                )

                                # Extract the content from the tool result
                                content = tool_result.get("content", [])
                                if isinstance(content, list) and content:
                                    result_text = content[0].get("text", str(tool_result))
                                else:
                                    result_text = str(tool_result)

                                tool_results.append({"tool_call_id": tool_call["id"], "content": result_text})

                                # Stream tool result
                                tool_result_chunk = {
                                    "id": f"chatcmpl-{hash(str(messages))}",
                                    "object": "chat.completion.chunk",
                                    "model": "claude-sonnet-4-20250514",
                                    "choices": [
                                        {
                                            "index": 0,
                                            "delta": {
                                                "tool_result": {"tool_call_id": tool_call["id"], "content": result_text}
                                            },
                                            "finish_reason": None,
                                        }
                                    ],
                                }
                                yield f"data: {json.dumps(tool_result_chunk)}\n\n".encode()
                                await asyncio.sleep(0.001)  # Small delay to ensure proper streaming

                            except Exception as e:
                                logger.error("Tool execution failed for %s: %s", tool_call["name"], e)
                                error_msg = f"Error executing {tool_call['name']}: {str(e)}"
                                tool_results.append({"tool_call_id": tool_call["id"], "content": error_msg})

                                # Stream error result
                                tool_error_chunk = {
                                    "id": f"chatcmpl-{hash(str(messages))}",
                                    "object": "chat.completion.chunk",
                                    "model": "claude-sonnet-4-20250514",
                                    "choices": [
                                        {
                                            "index": 0,
                                            "delta": {
                                                "tool_result": {"tool_call_id": tool_call["id"], "content": error_msg}
                                            },
                                            "finish_reason": None,
                                        }
                                    ],
                                }
                                yield f"data: {json.dumps(tool_error_chunk)}\n\n".encode()
                                await asyncio.sleep(0.001)

                        # After tool execution, we need to get the assistant's response to the tool results
                        # Add tool results to messages and get final response
                        if tool_results:
                            # Add the assistant message with tool calls
                            updated_messages = messages + [
                                {
                                    "role": "assistant",
                                    "content": assistant_content,
                                    "tool_calls": [
                                        {
                                            "id": tc["id"],
                                            "type": "function",
                                            "function": {"name": tc["name"], "arguments": json.dumps(tc["input"])},
                                        }
                                        for tc in tool_calls
                                    ],
                                }
                            ]

                            # Add tool results as tool messages
                            for result in tool_results:
                                updated_messages.append(
                                    {
                                        "role": "tool",
                                        "content": result["content"],
                                        "tool_call_id": result["tool_call_id"],
                                    }
                                )

                            # Get final assistant response
                            final_response_content = ""
                            async for chunk in LLMHelper.stream_chat_completion(
                                messages=updated_messages,
                                model="claude-sonnet-4-20250514",
                                temperature=1.0,
                                max_tokens=4096,
                                system=system_prompt,
                                tools=None,  # Don't allow more tool calls in follow-up
                                tool_choice=None,
                            ):
                                if hasattr(chunk, "type") and chunk.type == "content_block_delta":
                                    if hasattr(chunk, "delta") and hasattr(chunk.delta, "text"):
                                        final_response_content += chunk.delta.text
                                        # Stream final response
                                        final_chunk = {
                                            "id": f"chatcmpl-{hash(str(messages))}",
                                            "object": "chat.completion.chunk",
                                            "model": "claude-sonnet-4-20250514",
                                            "choices": [
                                                {
                                                    "index": 0,
                                                    "delta": {"content": chunk.delta.text},
                                                    "finish_reason": None,
                                                }
                                            ],
                                        }
                                        yield f"data: {json.dumps(final_chunk)}\n\n".encode()
                                        await asyncio.sleep(0.001)

                            # Update assistant content with final response
                            assistant_content += final_response_content

                    # If we have tool calls but no content, ensure we get a response
                    elif tool_calls and not assistant_content.strip():
                        # Create a follow-up request to get assistant response about the tool execution
                        messages_with_tool_results = messages + [
                            {
                                "role": "assistant",
                                "content": "I'll help you with that calculation.",
                                "tool_calls": [
                                    {
                                        "id": tc["id"],
                                        "type": "function",
                                        "function": {"name": tc["name"], "arguments": json.dumps(tc["input"])},
                                    }
                                    for tc in tool_calls
                                ],
                            }
                        ]

                        # Add tool results
                        for result in tool_results:
                            messages_with_tool_results.append(
                                {"role": "tool", "content": result["content"], "tool_call_id": result["tool_call_id"]}
                            )

                        # Get assistant's final response
                        async for chunk in LLMHelper.stream_chat_completion(
                            messages=messages_with_tool_results,
                            model="claude-sonnet-4-20250514",
                            temperature=1.0,
                            max_tokens=1024,
                            system=system_prompt,
                            tools=None,
                            tool_choice=None,
                        ):
                            if hasattr(chunk, "type") and chunk.type == "content_block_delta":
                                if hasattr(chunk, "delta") and hasattr(chunk.delta, "text"):
                                    assistant_content += chunk.delta.text
                                    # Stream the final response
                                    response_chunk = {
                                        "id": f"chatcmpl-{hash(str(messages))}",
                                        "object": "chat.completion.chunk",
                                        "model": "claude-sonnet-4-20250514",
                                        "choices": [
                                            {"index": 0, "delta": {"content": chunk.delta.text}, "finish_reason": None}
                                        ],
                                    }
                                    yield f"data: {json.dumps(response_chunk)}\n\n".encode()
                                    await asyncio.sleep(0.001)

                    # Send completion chunk
                    final_chunk = {
                        "id": f"chatcmpl-{hash(str(messages))}",
                        "object": "chat.completion.chunk",
                        "model": "claude-sonnet-4-20250514",
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    }
                    yield f"data: {json.dumps(final_chunk)}\n\n".encode()
                    yield b"data: [DONE]\n\n"
                    # Allow final processing
                    await asyncio.sleep(0.001)  # Small delay to ensure proper streaming

                    # Save the complete assistant message with tool calls
                    await self._save_assistant_message(
                        conversation_id=conversation_id,
                        project_id=project_id,
                        content=assistant_content,
                        thinking=assistant_thinking,
                        reasoning=assistant_reasoning,
                        tool_calls=tool_calls,
                        tool_results=tool_results,
                    )

                    logger.info("Streaming completed successfully with %d chunks", chunk_count)

                except Exception as e:
                    logger.error("Streaming error: %s", e, exc_info=True)
                    error_chunk = {"error": {"message": str(e), "type": "server_error"}}
                    yield f"data: {json.dumps(error_chunk)}\n\n".encode()

            resp.stream = event_stream()

        except Exception as e:
            logger.error("Streaming setup error: %s", e, exc_info=True)
            resp.status = falcon.HTTP_500
            resp.media = {"error": f"Streaming setup failed: {str(e)}"}

    async def _save_assistant_message(
        self,
        conversation_id: str,
        project_id: str,
        content: str,
        thinking: str = "",
        reasoning: str = "",
        tool_calls: list | None = None,
        tool_results: list | None = None,
    ) -> None:
        """Save the complete assistant message to the database."""
        if not content and not thinking and not reasoning and not tool_calls:
            logger.warning("No content to save for assistant message")
            return

        try:
            # Prepare message data
            message_data: dict[str, Any] = {
                "role": "assistant",
                "content": content,
            }

            # Add optional fields if present
            if thinking:
                message_data["thinking"] = thinking
            if reasoning:
                message_data["reasoning_content"] = reasoning
            if tool_calls:
                message_data["tool_calls"] = tool_calls
            if tool_results:
                message_data["tool_results"] = tool_results

            # Validate and save
            assistant_message = MessageModel.model_validate(message_data)
            collection = DatabaseHelper.get_collection("conversations")

            result = await collection.update_one(
                {"id": conversation_id, "project_id": project_id},
                {"$push": {"messages": assistant_message.model_dump()}},
            )

            logger.info(
                "Assistant message saved - matched: %d, modified: %d, content_length: %d, tools: %d",
                result.matched_count,
                result.modified_count,
                len(content),
                len(tool_calls or []),
            )

        except Exception as e:
            logger.error("Failed to save assistant message: %s", e, exc_info=True)
