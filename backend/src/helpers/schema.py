# MIT License
#
# Copyright (c) 2025 elevate-human-experiences
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

"""Pydantic schema definitions for the chatbot backend."""

from pydantic import BaseModel, Field
from typing import Any, Literal
from datetime import datetime


class MessageModel(BaseModel):
    """Chat message model."""

    role: Literal["user", "assistant", "system", "tool"] = Field(..., description="Role of the message sender")
    content: str | None = Field(None, description="Content of the message")
    tool_calls: list[dict[str, Any]] | None = Field(None, description="Tool calls in the message")
    tool_call_id: str | None = Field(None, description="Tool call ID for tool responses")


class ThinkingModel(BaseModel):
    """Claude thinking configuration model."""

    type: Literal["enabled"] = Field(..., description="Type of thinking mode")
    budget_tokens: int = Field(1024, description="Token budget for thinking", ge=1, le=8192)


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

    messages: list[MessageModel] = Field(..., description="List of chat messages", min_length=1)
    model: str | None = Field(None, description="Model to use for completion")
    temperature: float = Field(0.7, description="Sampling temperature", ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, description="Maximum tokens to generate", ge=1)
    tools: list[ToolModel] | None = Field(None, description="Available tools")
    tool_choice: str | dict[str, Any] | None = Field("auto", description="Tool choice strategy")
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
