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

"""Chat completions route handler using LiteLLM with Claude Anthropic reasoning models, tool calling, and streaming support."""

import falcon
import json
import logging
from pydantic import ValidationError
from src.helpers.llm import LLMHelper
from src.helpers.schema import ChatCompletionRequest, ErrorResponse

logger = logging.getLogger(__name__)


class ChatCompletionsResource:
    """Chat completions route handler with Claude Anthropic reasoning models, tool calling, and streaming support."""

    async def on_options(self, req, resp) -> None:
        """Handle OPTIONS requests for CORS preflight."""
        resp.status = falcon.HTTP_200
        resp.set_header("Access-Control-Allow-Origin", "*")
        resp.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        resp.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    async def on_post(self, req, resp) -> None:
        """Handle streaming chat completion requests with Claude Anthropic reasoning models and tool calling support."""
        try:
            data = await req.get_media()

            # Validate request using Pydantic model
            try:
                request_model = ChatCompletionRequest.model_validate(data)
            except ValidationError as e:
                error_response = ErrorResponse(
                    error="Invalid request format", details={"validation_errors": e.errors()}
                )
                resp.status = falcon.HTTP_400
                resp.media = error_response.model_dump()
                return

            # Extract validated data
            messages = [msg.model_dump() for msg in request_model.messages]
            model = request_model.model
            temperature = request_model.temperature
            max_tokens = request_model.max_tokens
            tools = [tool.model_dump() for tool in request_model.tools] if request_model.tools else None
            tool_choice = request_model.tool_choice
            reasoning_effort = request_model.reasoning_effort
            thinking = request_model.thinking.model_dump() if request_model.thinking else None

            # Ensure Claude Anthropic reasoning model is used
            if model and not LLMHelper.is_reasoning_model(model):
                logger.warning("Non-reasoning model %s requested, switching to Claude Anthropic reasoning model", model)
                model = LLMHelper.DEFAULT_MODEL

            # Claude requires temperature=1.0 when thinking is enabled
            if thinking and temperature != 1.0:
                logger.info("Setting temperature to 1.0 for Claude thinking mode (was %s)", temperature)
                temperature = 1.0

            # Handle streaming response with tool calling and reasoning content
            await self._handle_streaming_response_with_tools(
                req, resp, messages, model, temperature, max_tokens, tools, tool_choice, reasoning_effort, thinking
            )

        except Exception as e:
            logger.error("Chat completion error: %s", e)
            error_response = ErrorResponse(error="Internal server error")
            resp.status = falcon.HTTP_500
            resp.media = error_response.model_dump()

    async def _handle_streaming_response_with_tools(
        self,
        req,
        resp,
        messages: list[dict],
        model: str | None,
        temperature: float,
        max_tokens: int | None,
        tools: list[dict] | None,
        tool_choice: str | dict | None,
        reasoning_effort: str,
        thinking: dict | None = None,
    ) -> None:
        """Handle streaming completion response with tool calling and reasoning content support."""
        try:
            resp.content_type = "text/event-stream"
            resp.cache_control = ["no-cache"]
            resp.headers["Connection"] = "keep-alive"
            resp.headers["Access-Control-Allow-Origin"] = "*"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type"

            async def event_stream():
                """Generate server-sent events for streaming response with tool calling and reasoning content."""
                try:
                    chunk_count = 0

                    async for chunk in LLMHelper.generate_streaming_completion_with_tools(
                        messages=messages,
                        tools=tools,
                        tool_choice=tool_choice,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        reasoning_effort=reasoning_effort,
                        thinking=thinking,
                    ):
                        chunk_count += 1
                        yield f"data: {json.dumps(chunk)}\n\n".encode()

                    # Send final chunk to indicate completion
                    final_chunk = {
                        "id": f"chatcmpl-{hash(str(messages))}",
                        "object": "chat.completion.chunk",
                        "model": model or LLMHelper.DEFAULT_MODEL,
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    }
                    yield f"data: {json.dumps(final_chunk)}\n\n".encode()
                    yield b"data: [DONE]\n\n"

                    logger.info("Streaming completed with %s chunks", chunk_count)

                except Exception as e:
                    logger.error("Streaming error: %s", e)
                    error_chunk = {"error": {"message": str(e), "type": "server_error"}}
                    yield f"data: {json.dumps(error_chunk)}\n\n".encode()

            resp.stream = event_stream()

        except Exception as e:
            logger.error("Streaming setup error: %s", e)
            error_response = ErrorResponse(error=str(e))
            resp.status = falcon.HTTP_500
            resp.media = error_response.model_dump()
