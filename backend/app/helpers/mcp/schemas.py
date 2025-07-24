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

"""Pydantic schemas for Merlin Python client."""

from typing import Dict, Any, Union, Optional
from pydantic import BaseModel, Field


class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 Request (notifications when id is None)."""

    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    # Make 'id' truly optional for notifications:
    id: Optional[Union[int, str]] = Field(
        default=None,
        description="Request ID. If omitted or null, this is considered a notification.",
    )


class JSONRPCError(BaseModel):
    """JSON-RPC Error structure."""

    code: int
    message: str
    data: Optional[Any] = None


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 Response (one of result or error must be present)."""

    jsonrpc: str = "2.0"
    id: Union[int, str, None]
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None

    class Config:
        validate_assignment = True

    def __init__(self, **data: Any) -> None:
        """Initialize and enforce result/error exclusivity."""
        super().__init__(**data)
        # Enforce JSON-RPC result/error exclusivity
        if (self.result is None) == (self.error is None):
            raise ValueError("Response must have exactly one of 'result' or 'error'.")


class ToolInputSchema(BaseModel):
    """JSON Schema for tool input parameters."""

    type: str = "object"
    properties: dict[str, Any]
    required: list[str] = Field(default_factory=list)
    description: Optional[str] = None


class ToolOutputSchema(BaseModel):
    """Optional JSON Schema for tool output."""

    type: str = "object"
    properties: dict[str, Any]
    required: list[str] = Field(default_factory=list)
    description: Optional[str] = None


class ToolDefinition(BaseModel):
    """Definition of a tool as per MCP spec."""

    name: str
    title: Optional[str] = None
    description: str
    input_schema: ToolInputSchema
    output_schema: Optional[ToolOutputSchema] = None
    annotations: Optional[dict[str, Any]] = None


class ToolContentText(BaseModel):
    """Tool content of type text."""

    type: str = "text"
    text: str


class ToolContentImage(BaseModel):
    """Tool content of type image."""

    type: str = "image"
    data: str  # base64-encoded
    mimeType: str


class ToolContentAudio(BaseModel):
    """Tool content of type audio."""

    type: str = "audio"
    data: str  # base64-encoded
    mimeType: str


class ToolContentResourceLink(BaseModel):
    """Tool content linking to an external resource."""

    type: str = "resource_link"
    uri: str
    name: Optional[str] = None
    description: Optional[str] = None
    mimeType: Optional[str] = None


class ToolContentResource(BaseModel):
    """Tool content containing a resource."""

    type: str = "resource"
    resource: dict[str, Any]


ToolContent = Union[
    ToolContentText,
    ToolContentImage,
    ToolContentAudio,
    ToolContentResourceLink,
    ToolContentResource,
]


class ToolResult(BaseModel):
    """Result returned by a tool invocation."""

    content: list[dict[str, Any]] = Field(default_factory=list)
    structuredContent: Optional[dict[str, Any]] = None
    isError: Optional[bool] = False
