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

"""Pydantic schema definitions for the chatbot backend."""

from pydantic import BaseModel, Field
from typing import Any, Literal
from datetime import datetime, timezone


class MessageModel(BaseModel):
    """Chat message model."""

    role: Literal["user", "assistant", "system", "tool"] = Field(..., description="Role of the message sender")
    content: str | None = Field(None, description="Content of the message")
    tool_calls: list[dict[str, Any]] | None = Field(None, description="Tool calls in the message")
    tool_call_id: str | None = Field(None, description="Tool call ID for tool responses")
    tool_results: list[dict[str, Any]] | None = Field(None, description="Tool call results")

    # Additional fields for reasoning models
    thinking: str | None = Field(None, description="Thinking content for reasoning models")
    reasoning_content: str | None = Field(None, description="Reasoning content")
    thinking_blocks: list[dict[str, Any]] | None = Field(None, description="Thinking blocks")

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Override model_dump to exclude None values for cleaner API calls."""
        data = super().model_dump(exclude_none=True, **kwargs)
        return data


class ThinkingModel(BaseModel):
    """Claude thinking configuration model."""

    type: Literal["enabled"] = Field(..., description="Type of thinking mode")
    budget_tokens: int = Field(1024, description="Token budget for thinking", ge=1, le=8192)


class AnthropicToolModel(BaseModel):
    """Anthropic tool definition model."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    input_schema: dict[str, Any] = Field(..., description="Tool input schema")


class ToolFunctionModel(BaseModel):
    """Tool function definition model."""

    name: str = Field(..., description="Function name")
    description: str = Field(..., description="Function description")
    parameters: dict[str, Any] = Field(..., description="Function parameters schema")


class ToolModel(BaseModel):
    """Tool definition model."""

    type: Literal["function"] = Field(..., description="Tool type")
    function: ToolFunctionModel = Field(..., description="Function definition")


class ChatCompletionRequest(BaseModel):
    """Chat completion request model."""

    messages: list[MessageModel] = Field(..., description="list of chat messages", min_length=1)
    model: str | None = Field(None, description="Model to use for completion")
    temperature: float = Field(0.7, description="Sampling temperature", ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, description="Maximum tokens to generate", ge=1)
    tools: list[ToolModel] | None = Field(None, description="Available tools")
    tool_choice: str | dict[str, Any] | None = Field(None, description="Tool choice strategy")
    stream: bool = Field(True, description="Whether to stream the response")
    reasoning_effort: Literal["low", "medium", "high"] = Field("medium", description="Reasoning effort level")
    thinking: ThinkingModel | None = Field(None, description="Thinking configuration for Claude models")


class HealthCheckResponse(BaseModel):
    """Health check response model."""

    status: Literal["healthy", "unhealthy"] = Field(..., description="Service health status")
    timestamp: datetime = Field(..., description="Response timestamp")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")


class UserModel(BaseModel):
    """User account model."""

    id: str = Field(..., description="Unique identifier for the user")
    name: str = Field(..., description="Full name of the user")
    email: str = Field(..., description="Email address of the user")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Account creation timestamp"
    )


class ProjectModel(BaseModel):
    """Project context model."""

    id: str = Field(..., description="Unique identifier for the project")
    name: str = Field(..., description="Name of the project")
    description: str | None = Field(None, description="Optional project description")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Project creation timestamp"
    )


class AgentProfileModel(BaseModel):
    """Configuration profile for an agent, including static instructions."""

    id: str = Field(..., description="Unique identifier for the agent profile")
    name: str = Field(..., description="Descriptive name of the profile")
    description: str | None = Field(None, description="Optional description of the agent profile")
    project_id: str = Field(..., description="Identifier of the project this agent profile belongs to")
    avatar: str | None = Field(None, description="Base64 encoded avatar image")
    instructions: list[str] = Field(
        default_factory=list, description="list of instruction strings for the agent to follow"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Profile creation timestamp"
    )


class ConversationModel(BaseModel):
    """Represents a chat conversation within a project."""

    id: str = Field(..., description="Unique identifier for the conversation")
    title: str | None = Field(None, description="Optional title for the conversation")
    project_id: str | None = Field(None, description="Optional identifier of the associated project")
    user_id: str | None = Field(None, description="Optional identifier of the user in the conversation")
    agent_profile_id: str = Field(..., description="Identifier of the agent profile used for this conversation")
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when the conversation started"
    )
    messages: list[MessageModel] = Field(
        default_factory=list, description="Sequence of messages exchanged in the conversation"
    )
