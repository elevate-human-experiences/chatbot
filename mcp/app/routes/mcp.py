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

"""MCP route for Falcon API."""

import falcon
from typing import Any, Dict, Callable
from helpers.registry import discover_tools, get_tool_registry
from helpers.schemas import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
)


class JSONRPCException(Exception):
    """Exception class for JSON-RPC errors."""

    def __init__(self, code: int, message: str, data: str | None = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class MCPResource:
    """Falcon resource that implements a JSON-RPC 2.0 over HTTP endpoint."""

    def __init__(self) -> None:
        """Initialize MCPResource."""
        # discover_tools returns a list of ToolDefinition instances
        self._tool_defs = discover_tools()
        # build a mapping: method name → (group_name, handler_callable, input_model, output_model)
        self._methods: Dict[str, Dict[str, Any]] = {}
        registry = get_tool_registry()
        for td in self._tool_defs:
            # Handle case where annotations might be None
            annotations = td.annotations or {}
            group = annotations.get("group")
            if not group:
                continue  # Skip tools without a group

            tool_name = td.name
            if group not in registry:
                continue  # Skip if group not found in registry

            group_info = registry[group]
            cls = group_info["cls"]
            tool_meta = group_info["tools"][tool_name]
            method_fn = getattr(cls(), tool_name.split(".")[-1], None)
            self._methods[tool_name] = {
                "callable": method_fn,
                "input_model": tool_meta["input_model"],
                "output_model": tool_meta["output_model"],
            }

    async def list_tools(self) -> list[Any]:
        """GET /mcp/tools: Returns an array of tool definitions."""
        # Serialize each ToolDefinition to dict
        tools_json = [td.model_dump() for td in self._tool_defs]
        return tools_json

    def _parse_json_body(self, req: falcon.Request) -> Any:
        """Parse JSON body from request."""
        try:
            return req.media
        except Exception as e:
            raise JSONRPCException(
                code=-32700, message="Parse error", data=f"Invalid JSON: {e}"
            )

    def _validate_jsonrpc_request(self, raw: dict[str, Any]) -> JSONRPCRequest:
        """Validate JSON-RPC request."""
        if not raw.get("id"):
            raise JSONRPCException(
                code=-32600,
                message="Invalid Request",
                data="Missing 'id' field for notification",
            )
        try:
            return JSONRPCRequest.model_validate(raw)
        except Exception as e:
            raise JSONRPCException(code=-32600, message="Invalid Request", data=str(e))

    async def _handle_special_methods(
        self, method: str, req: falcon.Request, rpc_req: Any
    ) -> dict[str, Any] | None:
        """Handle special methods like list_tools, ping, whoami. Returns result dict or None."""
        if method == "list_tools":
            return {"result": await self.list_tools()}
        if method == "ping":
            return {"result": rpc_req.params or {"message": "pong"}}
        if method == "whoami":
            if req.context.get("user"):
                return {"result": {"message": f"You are {req.context.user['email']}"}}
            return {"result": {"message": "You are not authenticated"}}
        return None

    def _error_response(
        self, code: int, message: str, data: str | None, id: Any
    ) -> Any:
        error = JSONRPCError(code=code, message=message, data=data)
        return JSONRPCResponse(jsonrpc="2.0", id=id, error=error).model_dump()

    async def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        """POST /mcp: Expects a JSON-RPC 2.0 request in the body."""
        # --- 1. Parse JSON body & validate JSON-RPC request ---
        try:
            raw = await req.media
        except Exception as e:
            resp.media = self._error_response(
                -32700, "Parse error", f"Invalid JSON: {e}", None
            )
            resp.status = falcon.HTTP_200
            return

        try:
            rpc_req = self._validate_jsonrpc_request(raw)
        except JSONRPCException as err:
            resp.media = self._error_response(
                err.code, err.message, err.data, raw.get("id")
            )
            resp.status = falcon.HTTP_200
            return

        # --- 2. Special methods ---
        special = await self._handle_special_methods(rpc_req.method, req, rpc_req)
        if special is not None:
            resp.media = JSONRPCResponse(
                jsonrpc="2.0", id=rpc_req.id, **special
            ).model_dump()
            resp.status = falcon.HTTP_200
            return

        # --- 3. Method lookup ---
        method = rpc_req.method
        if method not in self._methods:
            resp.media = self._error_response(
                -32601, "Method not found", f"Unknown method: {method}", rpc_req.id
            )
            resp.status = falcon.HTTP_200
            return

        method_info = self._methods[method]
        input_model = method_info["input_model"]
        output_model = method_info["output_model"]
        handler: Callable[..., Any] = method_info["callable"]

        # --- 4. Validate params ---
        params = rpc_req.params or {}
        try:
            validated_input = input_model.model_validate(params)
        except Exception as e:
            resp.media = self._error_response(
                -32602, "Invalid params", str(e), rpc_req.id
            )
            resp.status = falcon.HTTP_200
            return

        # Set _context.user if available
        setattr(validated_input, "_context", {})
        if hasattr(req.context, "user") and req.context.user:
            validated_input._context["user"] = req.context.user

        # --- 5. Invoke the tool ---
        try:
            result = (
                await handler(validated_input)
                if callable(handler)
                and hasattr(handler, "__call__")
                and hasattr(handler, "__await__")
                else handler(validated_input)
            )
        except Exception as e:
            resp.media = self._error_response(
                -32603, "Internal error", str(e), rpc_req.id
            )
            resp.status = falcon.HTTP_200
            return

        # --- 6. Build successful JSON-RPC response ---
        rpc_resp = JSONRPCResponse(
            jsonrpc="2.0",
            id=rpc_req.id,
            result=result.model_dump()
            if output_model and hasattr(result, "model_dump")
            else result or {},
        )
        resp.media = rpc_resp.model_dump()
        resp.status = falcon.HTTP_200
