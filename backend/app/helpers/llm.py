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

import json
import logging
import traceback
import asyncio
import os
from anthropic import AsyncAnthropic, APIStatusError
from typing import AsyncGenerator, Any, List, Dict, Optional

from .mcp import MCPClient

logger = logging.getLogger(__name__)


class LLMHelper:
    """Static helper for LLM operations using Anthropic's extended thinking mode with tool support."""

    # Initialize the Anthropic async client (expects ANTHROPIC_API_KEY env variable)
    client = AsyncAnthropic()

    # Default Claude reasoning model
    DEFAULT_MODEL: str = "claude-sonnet-4-20250514"

    # Supported models that support extended thinking
    REASONING_MODELS: List[str] = [
        "claude-opus-4-20250514",
        "claude-sonnet-4-20250514",
        "claude-3-7-sonnet-20250219",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
    ]

    # Mapping of reasoning effort to thinking token budgets
    # Based on Anthropic docs: minimum is 1,024 tokens
    BUDGET_MAP: Dict[str, int] = {
        "low": 1024,  # Minimum budget
        "medium": 8192,  # Good balance for most tasks
        "high": 16384,  # Complex reasoning tasks
        "max": 32768,  # Maximum for critical tasks
    }

    # Retry configuration (can be overridden by environment variables)
    MAX_RETRIES: int = int(os.getenv("ANTHROPIC_MAX_RETRIES", "3"))
    INITIAL_RETRY_DELAY: float = float(os.getenv("ANTHROPIC_INITIAL_RETRY_DELAY", "1.0"))  # seconds
    MAX_RETRY_DELAY: float = float(os.getenv("ANTHROPIC_MAX_RETRY_DELAY", "60.0"))  # seconds
    BACKOFF_MULTIPLIER: float = float(os.getenv("ANTHROPIC_BACKOFF_MULTIPLIER", "2.0"))

    @classmethod
    def configure_retry_settings(
        cls,
        max_retries: Optional[int] = None,
        initial_delay: Optional[float] = None,
        max_delay: Optional[float] = None,
        backoff_multiplier: Optional[float] = None,
    ) -> None:
        """
        Configure retry settings for API calls.

        Args:
            max_retries: Maximum number of retries (default: 3)
            initial_delay: Initial delay in seconds (default: 1.0)
            max_delay: Maximum delay in seconds (default: 60.0)
            backoff_multiplier: Delay multiplier between retries (default: 2.0)
        """
        if max_retries is not None:
            cls.MAX_RETRIES = max_retries
        if initial_delay is not None:
            cls.INITIAL_RETRY_DELAY = initial_delay
        if max_delay is not None:
            cls.MAX_RETRY_DELAY = max_delay
        if backoff_multiplier is not None:
            cls.BACKOFF_MULTIPLIER = backoff_multiplier

        logger.info(
            "Retry configuration: max_retries=%d, initial_delay=%.1fs, max_delay=%.1fs, backoff=%.1fx",
            cls.MAX_RETRIES,
            cls.INITIAL_RETRY_DELAY,
            cls.MAX_RETRY_DELAY,
            cls.BACKOFF_MULTIPLIER,
        )

    @staticmethod
    def _serialize_tool_calls(tool_calls: Any) -> List[Dict[str, Any]]:
        """Serialize tool_calls objects to JSON-compatible dictionaries."""
        if not tool_calls:
            return []
        try:
            serializable: List[Dict[str, Any]] = []
            items = tool_calls if isinstance(tool_calls, (list, tuple)) else [tool_calls]
            for tc in items:
                fn = getattr(tc, "function", None)
                serializable.append(
                    {
                        "id": getattr(tc, "id", None),
                        "type": getattr(tc, "type", "function"),
                        "index": getattr(tc, "index", 0),
                        "function": {
                            "name": getattr(fn, "name", None) if fn else None,
                            "arguments": getattr(fn, "arguments", None) if fn else None,
                        },
                    }
                )
            return serializable
        except Exception:
            logger.error("Serialization failed: %s", traceback.format_exc())
            return [{"error": "serialization_failed"}]

    @staticmethod
    def is_reasoning_model(model: Optional[str] = None) -> bool:
        """Check if the given model supports extended thinking."""
        m = model or LLMHelper.DEFAULT_MODEL
        model_base = m.replace("", "")
        return model_base in LLMHelper.REASONING_MODELS

    @staticmethod
    def _get_budget(reasoning_effort: str) -> int:
        """Map reasoning effort to a thinking token budget."""
        return LLMHelper.BUDGET_MAP.get(reasoning_effort, LLMHelper.BUDGET_MAP["medium"])

    @staticmethod
    async def stream_chat_completion(
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Any = None,
        thinking: Optional[Dict[str, Any]] = None,
        reasoning_effort: str = "medium",
        **kwargs,
    ) -> AsyncGenerator[Any, None]:
        """
        Stream chat completion using Anthropic API with thinking support.

        This method follows the pattern from the streaming demo and provides
        a clean interface for streaming responses with optional thinking.
        """
        mdl = model or LLMHelper.DEFAULT_MODEL

        # Ensure we're using a reasoning model if thinking is requested
        if thinking and not LLMHelper.is_reasoning_model(mdl):
            logger.warning(
                "Non-reasoning model %s requested with thinking, switching to %s", mdl, LLMHelper.DEFAULT_MODEL
            )
            mdl = LLMHelper.DEFAULT_MODEL

        # Prepare thinking configuration
        thinking_config = None
        if thinking:
            budget = thinking.get("budget_tokens", LLMHelper._get_budget(reasoning_effort))
            effective_max = max_tokens or 4096

            # Ensure thinking budget doesn't exceed max_tokens
            if budget >= effective_max:
                budget = max(1024, effective_max - 1024)  # Leave room for response
                logger.warning("Thinking budget clamped to %s", budget)

            thinking_config = {"type": "enabled", "budget_tokens": budget}
            logger.info("Thinking enabled with budget: %s tokens", budget)

        # Build request parameters
        params = {
            "model": mdl,
            "messages": messages,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
            **kwargs,
        }

        if system:
            params["system"] = system

        if tools:
            params["tools"] = tools
            if tool_choice:
                if isinstance(tool_choice, str):
                    if tool_choice == "auto":
                        params["tool_choice"] = {"type": "auto"}
                    elif tool_choice == "any":
                        params["tool_choice"] = {"type": "any"}
                    elif tool_choice == "none":
                        params["tool_choice"] = {"type": "none"}
                    else:
                        params["tool_choice"] = {"type": "tool", "name": tool_choice}
                else:
                    params["tool_choice"] = tool_choice
            else:
                params["tool_choice"] = {"type": "auto"}

        if thinking_config:
            params["thinking"] = thinking_config

        try:
            # Use the retry-enabled streaming method
            async for chunk in LLMHelper._stream_with_retry(params):
                yield chunk

        except Exception as e:
            logger.error("Streaming error: %s", e, exc_info=True)
            raise

    @staticmethod
    async def stream_with_tool_execution(
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Any = None,
        thinking: Optional[Dict[str, Any]] = None,
        reasoning_effort: str = "medium",
        mcp_client: Optional[MCPClient] = None,
        **kwargs,
    ) -> AsyncGenerator[Any, None]:
        """
        Stream completion with automatic tool execution via MCP.

        This handles the tool execution flow:
        1. Stream initial response and collect tool calls
        2. Execute tools via MCP
        3. Stream final response with tool results
        """
        mcp = mcp_client or MCPClient()

        # Collect tool calls from first stream
        tool_calls = []
        response_content = []
        current_tool_call = None
        current_tool_input = ""

        # First pass: stream and collect tool calls
        async for chunk in LLMHelper.stream_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system=system,
            tools=tools,
            tool_choice=tool_choice,
            thinking=None,  # Don't use thinking on first pass
            reasoning_effort=reasoning_effort,
            **kwargs,
        ):
            yield chunk

            # Parse chunks according to Anthropic's actual streaming format
            if hasattr(chunk, "type"):
                if chunk.type == "content_block_start":
                    if hasattr(chunk, "content_block"):
                        if chunk.content_block.type == "text":
                            # Text content block
                            pass
                        elif chunk.content_block.type == "tool_use":
                            # Tool use block
                            current_tool_call = {
                                "id": chunk.content_block.id,
                                "name": chunk.content_block.name,
                                "input": {},
                            }
                            current_tool_input = ""

                elif chunk.type == "content_block_delta":
                    if hasattr(chunk, "delta"):
                        if hasattr(chunk.delta, "text"):
                            # Regular text content
                            response_content.append(chunk.delta.text)
                        elif hasattr(chunk.delta, "partial_json") and current_tool_call:
                            # Tool input JSON
                            current_tool_input += chunk.delta.partial_json

                elif chunk.type == "content_block_stop":
                    if current_tool_call:
                        # Complete the tool call
                        if current_tool_input:
                            try:
                                current_tool_call["input"] = json.loads(current_tool_input)
                                tool_calls.append(current_tool_call)
                                logger.info("Collected tool call: %s", current_tool_call["name"])
                            except json.JSONDecodeError as e:
                                logger.warning("Failed to parse tool JSON: %s - %s", current_tool_input, e)
                        current_tool_call = None
                        current_tool_input = ""

        # Execute tool calls if any were collected
        if tool_calls:
            logger.info("Executing %d tool calls", len(tool_calls))

            # Create tool use content blocks for the assistant message
            assistant_content = []
            if response_content:
                assistant_content.append({"type": "text", "text": "".join(response_content)})

            for tool_call in tool_calls:
                assistant_content.append(
                    {"type": "tool_use", "id": tool_call["id"], "name": tool_call["name"], "input": tool_call["input"]}
                )

            # Add assistant message to conversation
            assistant_msg = {"role": "assistant", "content": assistant_content}
            messages.append(assistant_msg)

            # Execute each tool and collect results
            tool_results = []
            for tool_call in tool_calls:
                try:
                    tool_result = await mcp.invoke_tool(
                        method=tool_call["name"], params=tool_call["input"], request_id=tool_call["id"]
                    )

                    # Add tool result
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_call["id"],
                            "content": json.dumps(tool_result) if not isinstance(tool_result, str) else tool_result,
                        }
                    )
                    logger.info("Tool %s executed successfully", tool_call["name"])

                except Exception as e:
                    logger.error("Tool execution failed: %s", e)
                    # Add error result
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_call["id"],
                            "content": f"Error: {str(e)}",
                            "is_error": True,
                        }
                    )

            # Add tool results message
            if tool_results:
                tool_msg = {"role": "user", "content": tool_results}
                messages.append(tool_msg)

            # Stream final response with thinking enabled
            async for chunk in LLMHelper.stream_chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                system=system,
                tools=tools,
                tool_choice=tool_choice,
                thinking=thinking,  # Enable thinking for final response
                reasoning_effort=reasoning_effort,
                **kwargs,
            ):
                yield chunk

    @staticmethod
    async def generate_completion(
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        reasoning_effort: str = "medium",
        thinking: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Generate a non-streaming completion with optional extended thinking.
        """
        mdl = model or LLMHelper.DEFAULT_MODEL
        if not LLMHelper.is_reasoning_model(mdl):
            logger.warning("Non-reasoning model %s, switching to reasoning model %s", mdl, LLMHelper.DEFAULT_MODEL)
            mdl = LLMHelper.DEFAULT_MODEL

        thinking_payload = None
        if thinking:
            budget = thinking.get("budget_tokens", LLMHelper._get_budget(reasoning_effort))
            effective_max = kwargs.get("max_tokens", max_tokens) or 4096
            if budget >= effective_max:
                logger.warning(
                    "Thinking budget %s >= max_tokens %s; clamping to %s", budget, effective_max, effective_max - 1
                )
                budget = effective_max - 1
            thinking_payload = {"type": "enabled", "budget_tokens": budget}
            logger.info("Extended thinking enabled with budget_tokens=%s", budget)

        params: Dict[str, Any] = {
            "model": mdl,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            **kwargs,
        }
        if system:
            params["system"] = system
        if thinking_payload:
            params["thinking"] = thinking_payload

        try:

            async def _do_completion():
                return await LLMHelper.client.messages.create(**params)

            response = await LLMHelper._retry_with_backoff(_do_completion)
            for content in response.content:
                if content.type == "text":
                    return content.text
            return ""
        except Exception as e:
            logger.error("Error during completion: %s\n%s", e, traceback.format_exc())
            raise

    @staticmethod
    def get_model_list() -> List[str]:
        """Get list of supported reasoning models."""
        return LLMHelper.REASONING_MODELS.copy()

    @staticmethod
    def supports_reasoning(model: Optional[str] = None) -> bool:
        """Check if a model supports reasoning."""
        return LLMHelper.is_reasoning_model(model)

    # Legacy method aliases for backward compatibility
    @staticmethod
    async def generate_streaming_completion_with_tool_execution(
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Any = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        reasoning_effort: str = "medium",
        thinking: Optional[Dict[str, Any]] = None,
        mcp_client: Optional[MCPClient] = None,
        system: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[Any, None]:
        """Legacy method - use stream_with_tool_execution instead."""
        async for chunk in LLMHelper.stream_with_tool_execution(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system=system,
            tools=tools,
            tool_choice=tool_choice,
            thinking=thinking,
            reasoning_effort=reasoning_effort,
            mcp_client=mcp_client,
            **kwargs,
        ):
            yield chunk

    @staticmethod
    async def _retry_with_backoff(
        func, *args, max_retries: Optional[int] = None, initial_delay: Optional[float] = None, **kwargs
    ) -> Any:
        """
        Retry a function with exponential backoff for handling API overload errors.
        """
        max_retries = max_retries or LLMHelper.MAX_RETRIES
        delay = initial_delay or LLMHelper.INITIAL_RETRY_DELAY

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except APIStatusError as e:
                last_exception = e

                # Check if this is a retryable error
                error_data = getattr(e, "body", {})
                if isinstance(error_data, dict):
                    error_type = error_data.get("error", {}).get("type")
                    if error_type in ["overloaded_error", "rate_limit_error"]:
                        if attempt < max_retries:
                            logger.warning(
                                "API %s (attempt %d/%d), retrying in %.1fs...",
                                error_type,
                                attempt + 1,
                                max_retries + 1,
                                delay,
                            )
                            await asyncio.sleep(delay)
                            delay = min(delay * LLMHelper.BACKOFF_MULTIPLIER, LLMHelper.MAX_RETRY_DELAY)
                            continue

                # If not retryable or max retries reached, raise the error
                logger.error("API error not retryable or max retries reached: %s", e)
                raise
            except Exception as e:
                # For non-API errors, don't retry
                logger.error("Non-retryable error: %s", e)
                raise

        # This should never be reached, but just in case
        if last_exception:
            raise last_exception

        raise RuntimeError("Unexpected end of retry loop")

    @staticmethod
    async def _stream_with_retry(params: Dict[str, Any]) -> AsyncGenerator[Any, None]:
        """
        Stream with retry logic for handling overload errors.
        Now properly streams chunks in real-time instead of collecting them all first.
        """
        max_retries = LLMHelper.MAX_RETRIES
        delay = LLMHelper.INITIAL_RETRY_DELAY

        for attempt in range(max_retries + 1):
            try:
                async with LLMHelper.client.messages.stream(**params) as stream:
                    async for chunk in stream:
                        yield chunk
                # If we get here, streaming completed successfully
                return

            except APIStatusError as e:
                # Check if this is a retryable error
                error_data = getattr(e, "body", {})
                if isinstance(error_data, dict):
                    error_type = error_data.get("error", {}).get("type")
                    if error_type in ["overloaded_error", "rate_limit_error"]:
                        if attempt < max_retries:
                            logger.warning(
                                "Streaming API %s (attempt %d/%d), retrying in %.1fs...",
                                error_type,
                                attempt + 1,
                                max_retries + 1,
                                delay,
                            )
                            await asyncio.sleep(delay)
                            delay = min(delay * LLMHelper.BACKOFF_MULTIPLIER, LLMHelper.MAX_RETRY_DELAY)
                            continue

                # If not retryable or max retries reached, raise the error
                logger.error("Streaming API error not retryable or max retries reached: %s", e)
                raise
            except Exception as e:
                # For non-API errors, don't retry
                logger.error("Non-retryable streaming error: %s", e)
                raise

        raise RuntimeError("Unexpected end of streaming retry loop")
