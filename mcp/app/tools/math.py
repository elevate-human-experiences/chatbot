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

"""Math tools for Merlin server.

This module provides basic math operations including addition, subtraction,
multiplication, and division. Each operation is available as a tool with
specified input and output models.
"""

from helpers.registry import tool_group, tool
from pydantic import BaseModel


class AddInput(BaseModel):
    """Input model for addition and subtraction operations."""

    a: int
    b: int


class AddOutput(BaseModel):
    """Output model for math operations."""

    result: int


@tool_group(name="math", description="Basic math operations")
class MathTools:
    """Class containing basic math tools."""

    @tool(
        name="math.add",
        description="Add two integers",
        input_model=AddInput,
        output_model=AddOutput,
    )  # type: ignore[misc]
    def add(self, inp: AddInput) -> AddOutput:
        """Return the sum of two integers."""
        return AddOutput(result=inp.a + inp.b)

    @tool(
        name="math.subtract",
        description="Subtract two integers",
        input_model=AddInput,
        output_model=AddOutput,
    )  # type: ignore[misc]
    def subtract(self, inp: AddInput) -> AddOutput:
        """Return the difference of two integers."""
        return AddOutput(result=inp.a - inp.b)

    @tool(
        name="math.multiply",
        description="Multiply two integers",
        input_model=AddInput,
        output_model=AddOutput,
    )  # type: ignore[misc]
    def multiply(self, inp: AddInput) -> AddOutput:
        """Return the product of two integers."""
        return AddOutput(result=inp.a * inp.b)

    @tool(
        name="math.divide",
        description="Divide two integers",
        input_model=AddInput,
        output_model=AddOutput,
    )  # type: ignore[misc]
    def divide(self, inp: AddInput) -> AddOutput:
        """Return the quotient of two integers, if the divisor is not zero."""
        if inp.b == 0:
            raise ValueError("Division by zero is not allowed")
        return AddOutput(result=inp.a // inp.b)
