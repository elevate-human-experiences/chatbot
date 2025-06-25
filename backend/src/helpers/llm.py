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

"""LLM helper using LiteLLM for unified AI model access with Claude Anthropic reasoning models support."""

import litellm
from litellm import acompletion
import logging
from typing import AsyncGenerator, Any

logger = logging.getLogger(__name__)

# Configure LiteLLM
litellm.set_verbose = True  # Enable for debugging thinking content
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
                    # Enhanced debugging for all chunks when thinking is enabled
                    if thinking:
                        logger.debug("=== Processing chunk ===")
                        logger.debug("Raw chunk type: %s", type(chunk))
                        logger.debug(
                            "Raw chunk attributes: %s", [attr for attr in dir(chunk) if not attr.startswith("_")]
                        )
                        if hasattr(chunk, "__dict__"):
                            chunk_dict = {k: v for k, v in chunk.__dict__.items() if not k.startswith("_")}
                            logger.debug("Raw chunk dict: %s", str(chunk_dict)[:1000])

                    if hasattr(chunk, "choices") and chunk.choices and len(chunk.choices) > 0:
                        choice = chunk.choices[0]
                        delta = choice.delta if hasattr(choice, "delta") else {}

                        # Extract delta attributes safely
                        content = getattr(delta, "content", None)
                        role = getattr(delta, "role", None)
                        tool_calls = getattr(delta, "tool_calls", None)
                        finish_reason = getattr(choice, "finish_reason", None)

                        # Handle thinking/reasoning content with comprehensive checks
                        thinking_content = None
                        reasoning_content = None
                        thinking_blocks = None

                        # Debug delta structure when thinking is enabled
                        if thinking:
                            logger.debug("=== Delta analysis ===")
                            logger.debug("Delta type: %s", type(delta))
                            logger.debug(
                                "Delta attributes: %s", [attr for attr in dir(delta) if not attr.startswith("_")]
                            )
                            if hasattr(delta, "__dict__"):
                                delta_dict = {k: v for k, v in delta.__dict__.items() if not k.startswith("_")}
                                logger.debug("Delta dict: %s", delta_dict)

                        # Check for thinking in delta (all possible field names)
                        thinking_field_names = [
                            "thinking",
                            "thinking_content",
                            "reasoning",
                            "reasoning_content",
                            "thoughts",
                            "thought",
                            "reason",
                            "internal_thoughts",
                            "reflection",
                            "analysis",
                            "step_by_step",
                            "chain_of_thought",
                            "cot",
                        ]

                        for thinking_field in thinking_field_names:
                            if hasattr(delta, thinking_field):
                                field_value = getattr(delta, thinking_field, None)
                                if field_value:
                                    if thinking_field in [
                                        "thinking",
                                        "thinking_content",
                                        "thoughts",
                                        "thought",
                                        "internal_thoughts",
                                    ]:
                                        thinking_content = field_value
                                    else:
                                        reasoning_content = field_value
                                    logger.info("Found %s in delta: %s", thinking_field, str(field_value)[:100])

                        # Check for thinking_blocks in delta
                        if hasattr(delta, "thinking_blocks"):
                            thinking_blocks = getattr(delta, "thinking_blocks", None)
                            if thinking_blocks:
                                logger.info(
                                    "Found thinking_blocks in delta: %d blocks",
                                    len(thinking_blocks) if isinstance(thinking_blocks, list) else 1,
                                )

                        # Check for thinking in choice level (LiteLLM standard)
                        choice_message = getattr(choice, "message", None)
                        if choice_message:
                            for thinking_field in thinking_field_names:
                                if hasattr(choice_message, thinking_field):
                                    field_value = getattr(choice_message, thinking_field, None)
                                    if field_value:
                                        if thinking_field in [
                                            "thinking",
                                            "thinking_content",
                                            "thoughts",
                                            "thought",
                                            "internal_thoughts",
                                        ]:
                                            thinking_content = field_value
                                        else:
                                            reasoning_content = field_value
                                        logger.info(
                                            "Found %s in choice.message: %s", thinking_field, str(field_value)[:100]
                                        )

                            if hasattr(choice_message, "thinking_blocks"):
                                thinking_blocks = getattr(choice_message, "thinking_blocks", None)
                                if thinking_blocks:
                                    logger.info(
                                        "Found thinking_blocks in choice.message: %d blocks",
                                        len(thinking_blocks) if isinstance(thinking_blocks, list) else 1,
                                    )

                        # Check for thinking in choice level directly
                        for thinking_field in thinking_field_names:
                            if hasattr(choice, thinking_field):
                                field_value = getattr(choice, thinking_field, None)
                                if field_value:
                                    if thinking_field in [
                                        "thinking",
                                        "thinking_content",
                                        "thoughts",
                                        "thought",
                                        "internal_thoughts",
                                    ]:
                                        thinking_content = field_value
                                    else:
                                        reasoning_content = field_value
                                    logger.info("Found %s in choice: %s", thinking_field, str(field_value)[:100])

                        # Check for thinking in chunk level
                        for thinking_field in thinking_field_names + ["thinking_blocks"]:
                            if hasattr(chunk, thinking_field):
                                field_value = getattr(chunk, thinking_field, None)
                                if field_value:
                                    if thinking_field == "reasoning_content":
                                        reasoning_content = field_value
                                    elif thinking_field == "thinking_blocks":
                                        thinking_blocks = field_value
                                    elif thinking_field in [
                                        "thinking",
                                        "thinking_content",
                                        "thoughts",
                                        "thought",
                                        "internal_thoughts",
                                    ]:
                                        thinking_content = field_value
                                    else:
                                        reasoning_content = field_value
                                    logger.info("Found %s in chunk: %s", thinking_field, str(field_value)[:100])

                        # For Claude models, also check for Claude-specific thinking fields in raw data
                        if hasattr(chunk, "_raw") and isinstance(chunk._raw, dict):
                            raw_data = chunk._raw
                            for field in thinking_field_names + ["thinking_blocks"]:
                                if field in raw_data:
                                    field_value = raw_data[field]
                                    if field_value:
                                        if field in [
                                            "thinking",
                                            "thinking_content",
                                            "thoughts",
                                            "thought",
                                            "internal_thoughts",
                                        ]:
                                            thinking_content = field_value
                                        elif field == "thinking_blocks":
                                            thinking_blocks = field_value
                                        else:
                                            reasoning_content = field_value
                                        logger.info("Found %s in raw data: %s", field, str(field_value)[:100])

                        # Also check in chunk.model_extra if it exists (Pydantic models)
                        if hasattr(chunk, "model_extra") and isinstance(chunk.model_extra, dict):
                            for field in thinking_field_names + ["thinking_blocks"]:
                                if field in chunk.model_extra:
                                    field_value = chunk.model_extra[field]
                                    if field_value:
                                        if field in [
                                            "thinking",
                                            "thinking_content",
                                            "thoughts",
                                            "thought",
                                            "internal_thoughts",
                                        ]:
                                            thinking_content = field_value
                                        elif field == "thinking_blocks":
                                            thinking_blocks = field_value
                                        else:
                                            reasoning_content = field_value
                                        logger.info("Found %s in chunk.model_extra: %s", field, str(field_value)[:100])

                        # Check if chunk is a dict-like object (fallback)
                        if hasattr(chunk, "__getitem__"):
                            try:
                                for field in thinking_field_names + ["thinking_blocks"]:
                                    if field in chunk:
                                        field_value = chunk[field]
                                        if field_value:
                                            if field in [
                                                "thinking",
                                                "thinking_content",
                                                "thoughts",
                                                "thought",
                                                "internal_thoughts",
                                            ]:
                                                thinking_content = field_value
                                            elif field == "thinking_blocks":
                                                thinking_blocks = field_value
                                            else:
                                                reasoning_content = field_value
                                            logger.info(
                                                "Found %s in chunk[%s]: %s", field, field, str(field_value)[:100]
                                            )
                            except (KeyError, TypeError):
                                pass

                        # Debug log for thinking content summary
                        if thinking and (thinking_content or reasoning_content or thinking_blocks):
                            logger.info("=== Found thinking/reasoning content ===")
                            logger.info("thinking_content: %s", bool(thinking_content))
                            logger.info("reasoning_content: %s", bool(reasoning_content))
                            logger.info("thinking_blocks: %s", bool(thinking_blocks))

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
                            logger.info("Added thinking content to delta: %s", str(thinking_content)[:100])
                        if reasoning_content:
                            chunk_data["choices"][0]["delta"]["reasoning_content"] = reasoning_content
                            logger.info("Added reasoning content to delta: %s", str(reasoning_content)[:100])
                        if thinking_blocks:
                            chunk_data["choices"][0]["delta"]["thinking_blocks"] = thinking_blocks
                            logger.info(
                                "Added thinking blocks to delta: %s",
                                len(thinking_blocks) if isinstance(thinking_blocks, list) else "1",
                            )

                        # Only yield chunks with meaningful content
                        delta_obj = chunk_data["choices"][0]["delta"]
                        if (
                            delta_obj.get("content")
                            or delta_obj.get("tool_calls")
                            or delta_obj.get("thinking")
                            or delta_obj.get("reasoning_content")
                            or delta_obj.get("thinking_blocks")
                            or delta_obj.get("role")
                            or finish_reason
                        ):
                            # Log what we're yielding when thinking is enabled
                            if thinking:
                                logger.debug("=== Yielding chunk ===")
                                logger.debug("Delta keys: %s", list(delta_obj.keys()))
                                if delta_obj.get("thinking"):
                                    logger.debug("Thinking content length: %d", len(str(delta_obj.get("thinking"))))
                                if delta_obj.get("reasoning_content"):
                                    logger.debug(
                                        "Reasoning content length: %d", len(str(delta_obj.get("reasoning_content")))
                                    )
                                if delta_obj.get("thinking_blocks"):
                                    logger.debug(
                                        "Thinking blocks count: %d",
                                        len(delta_obj.get("thinking_blocks"))
                                        if isinstance(delta_obj.get("thinking_blocks"), list)
                                        else 1,
                                    )

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
