#!/usr/bin/env python3
"""
Simple Anthropic Streaming Demo

This script demonstrates the key streaming features:
1. Basic text streaming
2. Extended thinking with streaming
3. Tool use with streaming

Uses python-dotenv for environment variable management.
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Any

from dotenv import load_dotenv
from anthropic import AsyncAnthropic

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleAnthropicStreaming:
    """Simple demonstration of Anthropic streaming capabilities."""

    def __init__(self):
        """Initialize the Anthropic client."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        logger.info("Initialized Anthropic client")

    async def demo_basic_streaming(self):
        """Demonstrate basic streaming."""
        print("\n" + "="*50)
        print("🚀 BASIC STREAMING DEMO")
        print("="*50)

        messages = [
            {
                "role": "user",
                "content": "Explain quantum computing in simple terms."
            }
        ]

        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=1024,
                messages=messages,
                temperature=0.7
            ) as stream:
                print("🤖 Claude Response:")
                async for chunk in stream:
                    if chunk.type == "content_block_delta" and hasattr(chunk.delta, 'text'):
                        print(chunk.delta.text, end="", flush=True)
                print("\n")

        except Exception as e:
            logger.error("Basic streaming failed: %s", e)

    async def demo_thinking_streaming(self):
        """Demonstrate streaming with extended thinking."""
        print("\n" + "="*50)
        print("🧠 THINKING STREAMING DEMO")
        print("="*50)

        messages = [
            {
                "role": "user",
                "content": """
                I'm trying to decide between two investment options:
                Option A: 8% annual return, but high volatility
                Option B: 5% annual return, but stable

                I'm 30 years old and want to retire at 65. I can invest $1000/month.
                Which option should I choose and why?
                """
            }
        ]

        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=16384,  # Must be larger than thinking budget
                messages=messages,
                temperature=1.0,  # Required for thinking
                thinking={
                    "type": "enabled",
                    "budget_tokens": 8192
                }
            ) as stream:
                print("🧠 Claude's Thinking Process:")
                thinking_words = 0

                async for chunk in stream:
                    if chunk.type == "content_block_delta":
                        if hasattr(chunk.delta, 'thinking'):
                            # This is thinking content
                            thinking_words += len(chunk.delta.thinking.split())
                            print("💭", end="", flush=True)  # Show thinking progress
                        elif hasattr(chunk.delta, 'text'):
                            # This is regular response text
                            print(chunk.delta.text, end="", flush=True)

                print(f"\n\n💡 Used approximately {thinking_words} thinking words")

        except Exception as e:
            logger.error("Thinking streaming failed: %s", e)

    async def demo_tool_streaming(self):
        """Demonstrate streaming with tool use."""
        print("\n" + "="*50)
        print("🛠️ TOOL STREAMING DEMO")
        print("="*50)

        # Simple math tools
        tools = [
            {
                "name": "calculate",
                "description": "Perform basic mathematical calculations",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate"
                        }
                    },
                    "required": ["expression"]
                }
            }
        ]

        messages = [
            {
                "role": "user",
                "content": "Calculate the compound interest on $10,000 invested at 7% annually for 20 years. Use the formula A = P(1 + r)^t"
            }
        ]

        try:
            # Stream the initial response
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=1024,
                messages=messages,
                tools=tools,
                tool_choice={"type": "auto"},
                temperature=0.7
            ) as stream:
                print("🤖 Claude's Response:")

                tool_calls = []
                response_text = ""
                current_tool = None
                current_json = ""

                async for chunk in stream:
                    if chunk.type == "content_block_start":
                        if chunk.content_block.type == "tool_use":
                            current_tool = {
                                "id": chunk.content_block.id,
                                "name": chunk.content_block.name,
                                "input": ""
                            }
                            print(f"\n🔧 Using tool: {chunk.content_block.name}")

                    elif chunk.type == "content_block_delta":
                        if hasattr(chunk.delta, 'text'):
                            response_text += chunk.delta.text
                            print(chunk.delta.text, end="", flush=True)
                        elif hasattr(chunk.delta, 'partial_json') and current_tool:
                            current_json += chunk.delta.partial_json

                    elif chunk.type == "content_block_stop" and current_tool:
                        if current_json:
                            try:
                                current_tool["input"] = json.loads(current_json)
                                tool_calls.append(current_tool)
                                print(f"\n📊 Tool input: {current_tool['input']}")
                            except json.JSONDecodeError:
                                logger.warning("Failed to parse tool JSON")
                        current_tool = None
                        current_json = ""

                # Execute tool calls (mock implementation)
                for tool_call in tool_calls:
                    if tool_call["name"] == "calculate":
                        expression = tool_call["input"].get("expression", "")
                        print(f"🧮 Calculating: {expression}")
                        try:
                            # Calculate compound interest: A = P(1 + r)^t
                            # A = 10000 * (1.07)^20
                            result = 10000 * (1.07 ** 20)
                            print(f"✅ Result: ${result:,.2f}")
                            print(f"💰 Interest earned: ${result - 10000:,.2f}")
                            print(f"� Nearly {result/10000:.1f}x growth over 20 years!")
                        except Exception as e:
                            print(f"❌ Calculation error: {e}")
                    else:
                        print("🔍 Tool execution simulated")

                print()

        except Exception as e:
            logger.error("Tool streaming failed: %s", e)

    async def run_all_demos(self):
        """Run all streaming demonstrations."""
        print("🎭 ANTHROPIC STREAMING DEMONSTRATIONS")
        print("=" * 60)

        try:
            await self.demo_basic_streaming()
            await self.demo_thinking_streaming()
            await self.demo_tool_streaming()

            print("\n" + "="*60)
            print("🎉 ALL DEMONSTRATIONS COMPLETED!")
            print("="*60)

        except Exception as e:
            logger.error("Demo suite failed: %s", e)
            print(f"\n❌ Demo suite failed: {e}")


async def main():
    """Main function to run the demonstrations."""
    try:
        # Verify environment setup
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("❌ Error: ANTHROPIC_API_KEY not found in environment variables.")
            print("Please create a .env file with your Anthropic API key:")
            print("ANTHROPIC_API_KEY=your_api_key_here")
            return

        print("✅ Environment variables loaded successfully")
        print(f"✅ API Key found: {os.getenv('ANTHROPIC_API_KEY')[:10]}...")

        # Run demonstrations
        demo = SimpleAnthropicStreaming()
        await demo.run_all_demos()

    except Exception as e:
        logger.error("Main execution failed: %s", e)
        print(f"❌ Failed to run demonstrations: {e}")


if __name__ == "__main__":
    # Run the async demonstration suite
    asyncio.run(main())
