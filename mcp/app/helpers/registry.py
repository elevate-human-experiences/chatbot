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

from typing import Callable, Type, Dict, Any
from pydantic import BaseModel
import pkgutil
import importlib
import inspect
from pathlib import Path
from helpers.schemas import ToolDefinition, ToolInputSchema, ToolOutputSchema


# In-memory registry of tool groups and their tools
_TOOL_GROUPS: Dict[str, Dict[str, Any]] = {}


def tool_group(name: str, description: str) -> Callable[[Type[Any]], Type[Any]]:
    """
    Class decorator to mark a class as a tool group.
    Registers the class and any of its methods decorated with @tool.
    """

    def decorator(cls: Type[Any]) -> Type[Any]:
        if name in _TOOL_GROUPS:
            raise ValueError(f"Tool group '{name}' is already registered")
        # Initialize group entry
        _TOOL_GROUPS[name] = {"cls": cls, "description": description, "tools": {}}
        # Scan for methods already decorated with @tool
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if callable(attr) and hasattr(attr, "__tool_meta__"):
                meta = getattr(attr, "__tool_meta__")
                _TOOL_GROUPS[name]["tools"][meta["name"]] = meta
        return cls

    return decorator


def tool(
    *,
    name: str,
    description: str,
    input_model: Type[BaseModel],
    output_model: Type[BaseModel],
) -> Callable[[Any], Any]:
    """
    Method decorator to mark a function as a tool.
    Attaches Pydantic input/output models and metadata for later registration.
    """

    def decorator(fn: Any) -> Any:
        fn.__tool_meta__ = {
            "name": name,
            "description": description,
            "input_model": input_model,
            "output_model": output_model,
        }
        return fn

    return decorator


def get_tool_registry() -> Dict[str, Dict[str, Any]]:
    """
    Returns the full registry of tool groups and their tools.
    """
    if not _TOOL_GROUPS:
        # If registry is empty, discover tools
        print("Tool registry is empty, discovering tools...")
        discover_tools()
    return _TOOL_GROUPS


def discover_tools(tools_pkg: str = "tools") -> list[ToolDefinition]:
    # now registry is populated
    definitions: list[ToolDefinition] = []
    if (Path(__file__).parent.parent / tools_pkg).exists():
        pkg_path = (Path(__file__).parent.parent / tools_pkg).as_posix()
        print(f"Discovering tools in package: {tools_pkg} at {pkg_path}")
        for finder, mod_name, ispkg in pkgutil.walk_packages([str(pkg_path)]):
            importlib.import_module(f"{tools_pkg}.{mod_name}")

        for group_name, info in _TOOL_GROUPS.items():
            cls = info["cls"]
            for _, method in inspect.getmembers(cls, inspect.isfunction):
                if hasattr(method, "__tool_meta__"):
                    td = make_tool_definition(group_name, method, info)
                    definitions.append(td)
    else:
        print(f"Warning: No tools found in tools folder '{tools_pkg}'")

    print(f"Discovered {len(definitions)} tool definitions in total.")
    for td in definitions:
        print(
            f" - {td.name}: {td.description} (Group: {td.annotations.get('group', 'N/A')})"
        )

    return definitions


def make_tool_definition(
    group_name: str,
    fn: Any,
    cls_meta: Dict[str, Any],
) -> ToolDefinition:
    meta = getattr(fn, "__tool_meta__")
    in_model: Type[BaseModel] = meta["input_model"]
    out_model: Type[BaseModel] = meta["output_model"]

    input_schema = ToolInputSchema(
        properties=in_model.schema(by_alias=True)["properties"],
        required=in_model.schema(by_alias=True).get("required", []),
        description=in_model.__doc__,
    )
    output_schema = ToolOutputSchema(
        properties=out_model.schema(by_alias=True)["properties"],
        required=out_model.schema(by_alias=True).get("required", []),
        description=out_model.__doc__,
    )

    return ToolDefinition(
        name=meta["name"],
        title=None,
        description=meta["description"],
        input_schema=input_schema,
        output_schema=output_schema,
        annotations={"group": group_name},
    )
