#!/usr/bin/env python3
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

"""API test script for the Claude Anthropic reasoning model chat backend."""

import asyncio
import json
import sys
from typing import Any

import httpx


class ChatAPITester:
    """Test client for the chat completions API with Claude Anthropic models."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url

    async def test_health_check(self) -> None:
        """Test the health check endpoint."""
        print("Testing Health Check:")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/health")
                status = response.status_code
                text = response.text
                print(f"Status: {status}")
                print(f"Response: {text}")

            except httpx.RequestError as e:
                print(f"Error: {e}")

    async def test_chat_completions_streaming(self) -> None:
        """Test chat completions with tool calling, reasoning content, and streaming using Claude Anthropic."""
        print("\n\nTesting Chat Completions with Tool Calling and Reasoning Content (streaming):")

        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": "What is the weather like in San Francisco and what time is it there? Please think through this step by step.",
                }
            ],
            "model": "anthropic/claude-sonnet-4-20250514",
            "stream": True,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get current weather for a location",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "string", "description": "City name"},
                                "unit": {
                                    "type": "string",
                                    "enum": ["celsius", "fahrenheit"],
                                    "description": "Temperature unit",
                                },
                            },
                            "required": ["location"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_time",
                        "description": "Get current time for a location",
                        "parameters": {
                            "type": "object",
                            "properties": {"location": {"type": "string", "description": "City name"}},
                            "required": ["location"],
                        },
                    },
                },
            ],
            "tool_choice": "auto",
            "reasoning_effort": "low",
            "thinking": {"type": "enabled", "budget_tokens": 1024},
            "temperature": 1.0,
        }

        await self._make_streaming_request(payload)

    async def test_chat_completions_reasoning_only(self) -> None:
        """Test chat completions with reasoning content only (no tools) using Claude Anthropic."""
        print("\n\nTesting Chat Completions with Reasoning Content Only:")

        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": "Explain the concept of quantum entanglement in simple terms. Think through this carefully and show your reasoning process.",
                }
            ],
            "model": "anthropic/claude-sonnet-4-20250514",
            "stream": True,
            "reasoning_effort": "medium",
            "thinking": {"type": "enabled", "budget_tokens": 2048},
            "temperature": 1.0,
        }

        await self._make_streaming_request(payload)

    async def _make_streaming_request(self, payload: dict[str, Any]) -> None:
        """Make a streaming request to the chat completions endpoint."""
        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST", f"{self.base_url}/chat/completions", json=payload, headers=headers
                ) as response:
                    print(f"Status: {response.status_code}")
                    print("Streaming response:")

                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            line_str = line.strip()
                            if line_str:
                                # Handle SSE format
                                if line_str.startswith("data: "):
                                    data = line_str[6:]  # Remove 'data: ' prefix
                                    if data == "[DONE]":
                                        print("\n✅ Stream completed.")
                                        break
                                    try:
                                        chunk = json.loads(data)

                                        # Extract different types of content
                                        if "choices" in chunk and len(chunk["choices"]) > 0:
                                            delta = chunk["choices"][0].get("delta", {})

                                            # Display regular content
                                            if delta.get("content"):
                                                print(delta["content"], end="", flush=True)

                                            # Display thinking content (Claude reasoning)
                                            if delta.get("thinking"):
                                                print(f"\n🤔 [THINKING]: {delta['thinking']}")

                                            # Display reasoning content (LiteLLM standard)
                                            if delta.get("reasoning_content"):
                                                print(f"\n💭 [REASONING]: {delta['reasoning_content']}")

                                            # Display thinking blocks (Anthropic format)
                                            if delta.get("thinking_blocks"):
                                                for block in delta["thinking_blocks"]:
                                                    print(f"\n🧠 [THINKING BLOCK]: {block.get('thinking', block)}")

                                            # Also check for legacy 'reasoning' field
                                            if delta.get("reasoning"):
                                                print(f"\n💭 [REASONING (legacy)]: {delta['reasoning']}")

                                            # Display tool calls
                                            if delta.get("tool_calls"):
                                                print(f"\n🔧 [TOOL CALLS]: {json.dumps(delta['tool_calls'], indent=2)}")

                                            # Check for finish reason
                                            if chunk["choices"][0].get("finish_reason"):
                                                print(f"\n✅ [FINISH]: {chunk['choices'][0]['finish_reason']}")

                                    except json.JSONDecodeError:
                                        print(f"Raw line: {line_str}")
                                else:
                                    print(f"Raw line: {line_str}")
                    else:
                        error_text = await response.aread()
                        print(f"Error response: {error_text.decode()}")

            except httpx.RequestError as e:
                print(f"Request error: {e}")

    async def run_all_tests(self) -> None:
        """Run all test cases."""
        await self.test_health_check()
        await self.test_chat_completions_streaming()
        await self.test_chat_completions_reasoning_only()


async def main(base_url: str = "http://localhost:8080"):
    """Main entry point for the test script."""
    print(f"Testing API at: {base_url}")
    print("=" * 50)

    tester = ChatAPITester(base_url)
    await tester.run_all_tests()


if __name__ == "__main__":
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    asyncio.run(main(base_url))
