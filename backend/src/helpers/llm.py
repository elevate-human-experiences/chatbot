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

"""LLM helper using LiteLLM for unified AI model access with Claude Anthropic reasoning models support."""

import litellm
from litellm import acompletion
import logging
from typing import AsyncGenerator, Any

logger = logging.getLogger(__name__)

# Configure LiteLLM
litellm.set_verbose = False  # Set to True for debugging
litellm.drop_params = True  # Drop unsupported params instead of erroring
litellm.max_tokens = 4096  # Default max tokens


class LLMHelper:
    """Static helper for LLM operations using LiteLLM with Claude Anthropic reasoning models support."""

    # Default to Claude Anthropic reasoning model
    DEFAULT_MODEL = "anthropic/claude-sonnet-4-20250514"

    # Claude Anthropic reasoning models that support tool calling and thinking blocks
    REASONING_MODELS = [
        "anthropic/claude-sonnet-4-20250514",
        "anthropic/claude-3-7-sonnet-20250219",
        "anthropic/claude-3-5-sonnet-20241022",
        "anthropic/claude-3-5-haiku-20241022",
        "anthropic/claude-3-opus-20240229",
    ]

    @staticmethod
    def is_reasoning_model(model: str | None) -> bool:
        """Check if the given model is a Claude Anthropic reasoning model."""
        if not model:
            return True  # Default model is reasoning
        return any(
            reasoning_model in model for reasoning_model in LLMHelper.REASONING_MODELS
        ) or litellm.supports_reasoning(model)

    @staticmethod
    async def generate_streaming_completion_with_tools(
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = "auto",
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        reasoning_effort: str = "medium",
        thinking: dict | None = None,
        **kwargs,
    ) -> AsyncGenerator[dict, None]:
        """Generate a streaming completion with tool calling and reasoning content support using Claude Anthropic models."""
        model = model or LLMHelper.DEFAULT_MODEL

        # Ensure we're using a Claude Anthropic reasoning model
        if not LLMHelper.is_reasoning_model(model):
            logger.warning("Non-reasoning model %s provided, switching to %s", model, LLMHelper.DEFAULT_MODEL)
            model = LLMHelper.DEFAULT_MODEL

        try:
            # Claude requires temperature=1.0 when thinking is enabled
            if thinking and temperature != 1.0:
                logger.info("Setting temperature to 1.0 for Claude thinking mode (was %s)", temperature)
                temperature = 1.0

            completion_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": True,
                "reasoning_effort": reasoning_effort,
                **kwargs,
            }

            # Add tools if provided
            if tools:
                completion_params["tools"] = tools
                completion_params["tool_choice"] = tool_choice

            # Add thinking parameter for Claude models if provided
            if thinking:
                completion_params["thinking"] = thinking

            # Set max_tokens if provided
            if max_tokens:
                completion_params["max_tokens"] = max_tokens

            logger.info("Starting streaming completion with model: %s", model)
            response = await acompletion(**completion_params)

            async for chunk in response:
                try:
                    if hasattr(chunk, "choices") and chunk.choices and len(chunk.choices) > 0:
                        choice = chunk.choices[0]
                        delta = choice.delta if hasattr(choice, "delta") else {}

                        # Extract delta attributes safely
                        content = getattr(delta, "content", None)
                        role = getattr(delta, "role", None)
                        tool_calls = getattr(delta, "tool_calls", None)
                        finish_reason = getattr(choice, "finish_reason", None)

                        # Handle Claude-specific thinking content
                        thinking_content = None
                        reasoning_content = None

                        # Check for thinking in delta
                        if hasattr(delta, "thinking"):
                            thinking_content = getattr(delta, "thinking", None)

                        # Check for reasoning content in various possible formats
                        if hasattr(delta, "reasoning"):
                            reasoning_content = getattr(delta, "reasoning", None)
                        elif hasattr(chunk, "reasoning"):
                            reasoning_content = getattr(chunk, "reasoning", None)

                        # Format chunk in OpenAI-compatible format
                        chunk_data: dict[str, Any] = {
                            "id": getattr(chunk, "id", f"chatcmpl-{hash(str(messages))}"),
                            "object": getattr(chunk, "object", "chat.completion.chunk"),
                            "model": getattr(chunk, "model", model),
                            "choices": [
                                {"index": getattr(choice, "index", 0), "delta": {}, "finish_reason": finish_reason}
                            ],
                        }

                        # Add non-None delta content
                        if role:
                            chunk_data["choices"][0]["delta"]["role"] = role
                        if content:
                            chunk_data["choices"][0]["delta"]["content"] = content
                        if tool_calls:
                            chunk_data["choices"][0]["delta"]["tool_calls"] = tool_calls
                        if thinking_content:
                            chunk_data["choices"][0]["delta"]["thinking"] = thinking_content
                        if reasoning_content:
                            chunk_data["choices"][0]["delta"]["reasoning"] = reasoning_content

                        # Only yield chunks with meaningful content
                        delta_obj = chunk_data["choices"][0]["delta"]
                        if (
                            delta_obj.get("content")
                            or delta_obj.get("tool_calls")
                            or delta_obj.get("thinking")
                            or delta_obj.get("reasoning")
                            or delta_obj.get("role")
                            or finish_reason
                        ):
                            yield chunk_data

                except Exception as chunk_error:
                    logger.warning("Error processing chunk: %s", chunk_error)
                    continue

        except Exception as e:
            logger.error("Streaming completion failed: %s", e)
            # Yield error chunk
            error_chunk = {
                "id": f"chatcmpl-error-{hash(str(messages))}",
                "object": "chat.completion.chunk",
                "model": model,
                "choices": [{"index": 0, "delta": {"content": f"Error: {str(e)}"}, "finish_reason": "error"}],
            }
            yield error_chunk
            raise Exception(f"Streaming Claude completion failed: {e}") from e

    @staticmethod
    def get_model_list() -> list[str]:
        """Get list of available Claude Anthropic reasoning models for tool calling."""
        return [
            "anthropic/claude-sonnet-4-20250514",
            "anthropic/claude-3-7-sonnet-20250219",
            "anthropic/claude-3-5-sonnet-20241022",
            "anthropic/claude-3-5-haiku-20241022",
            "anthropic/claude-3-opus-20240229",
        ]

    @staticmethod
    def get_reasoning_models() -> list[str]:
        """Get list of Claude Anthropic reasoning models that support advanced reasoning and tool calling."""
        return LLMHelper.REASONING_MODELS.copy()

    @staticmethod
    def supports_reasoning(model: str | None = None) -> bool:
        """Check if the model supports reasoning using LiteLLM's built-in function."""
        model = model or LLMHelper.DEFAULT_MODEL
        return litellm.supports_reasoning(model)
