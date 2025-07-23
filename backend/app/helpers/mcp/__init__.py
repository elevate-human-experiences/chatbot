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

"""Client for interacting with the Merlin API."""

import os
import re
import uuid
import asyncio
from typing import Optional, Dict, Any
from urllib.parse import urlparse

import httpx
from aiohttp import web
from authlib.integrations.httpx_client import AsyncOAuth2Client

from .schemas import JSONRPCRequest, JSONRPCResponse, JSONRPCError


class MCPClient:
    """Client for Merlin API operations."""

    def __init__(self, server_url: str | None = None):
        self.mcp_url = server_url or os.getenv("MCP_SERVER_URL", "http://mcp:8080/mcp")
        self.client_id = os.getenv("OAUTH_CLIENT_ID")
        self.client_secret = os.getenv("OAUTH_CLIENT_SECRET")
        self.redirect_uri = os.getenv("OAUTH_REDIRECT_URI", "http://mcp:8765/oauth2callback")

        # The AsyncOAuth2Client will handle PKCE (code_challenge + method) for us
        self.client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope="openid email profile",
            code_challenge_method="S256",
        )
        self.token: Optional[Dict[str, Any]] = None
        print(f"[MCPClient] Initialized with MCP_SERVER_URL={self.mcp_url}")

    async def _discover_metadata(self) -> Dict[str, str]:
        """Discover metadata for OAuth2 authentication."""
        print("[MCPClient] Discovering metadata via 401 challenge...")
        async with httpx.AsyncClient() as tmp:
            resp = await tmp.get(self.mcp_url)
        www_auth = resp.headers.get("www-authenticate", "")
        m = re.search(r'metadata="([^"]+)"', www_auth)
        if not m:
            raise RuntimeError("Missing metadata URL in WWW-Authenticate header")
        metadata_url = m.group(1)
        print(f"[MCPClient] Metadata URL found: {metadata_url}")

        async with httpx.AsyncClient() as tmp:
            meta = (await tmp.get(metadata_url)).json()

        auth_endpoint = meta["authorization_endpoint"]
        token_endpoint = meta["token_endpoint"]
        resource = meta.get("resource", self.mcp_url)
        print(
            f"[MCPClient] Fetched metadata: authorization_endpoint={auth_endpoint}, token_endpoint={token_endpoint}, resource={resource}"
        )

        return {
            "authorization_endpoint": auth_endpoint,
            "token_endpoint": token_endpoint,
            "resource": resource,
        }

    async def _fetch_token(self):
        """Fetch OAuth2 token using PKCE flow."""
        print("[MCPClient] Starting OAuth2 PKCE flow to fetch token...")
        meta = await self._discover_metadata()

        # Let Authlib auto-generate and send PKCE parameters (challenge + method)
        uri, state = self.client.create_authorization_url(
            meta["authorization_endpoint"],
            resource=meta["resource"],
            prompt="consent",
            scope=["openid", "email", "profile"],
        )
        print(f"[MCPClient] Open this URL in your browser:\n    {uri}")

        parsed = urlparse(self.redirect_uri)
        host, port = parsed.hostname, parsed.port or 80

        # Prepare an asyncio Future for the callback code
        loop = asyncio.get_event_loop()
        code_future: asyncio.Future[str] = loop.create_future()

        async def callback(request: web.Request):
            params = request.rel_url.query
            if params.get("state") != state or not params.get("code"):
                return web.Response(status=400, text="Invalid state or missing code")
            code_future.set_result(params["code"])
            return web.Response(text="Authorization complete — you can close this tab.")

        # Start a temporary aiohttp server to receive the callback
        app = web.Application()
        app.router.add_get(parsed.path, callback)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        # Wait for the OAuth2 redirect with the code
        code = await code_future

        # Tear down the server
        await runner.cleanup()

        # Exchange the authorization code for a token
        print("[MCPClient] Exchanging code for token...")
        self.token = await self.client.fetch_token(
            meta["token_endpoint"],
            code=code,
            resource=meta["resource"],
        )
        print(f"[MCPClient] Token acquired (expires_in={self.token.get('expires_in') if self.token else 'None'})")

    async def _request(self, payload: Dict[str, Any]) -> Any:
        """Send a JSON-RPC request to the MCP server."""
        # Try request without token first
        tried_auth = False
        while True:
            headers = {}
            if self.token:
                # Add Authorization header if token is present
                headers["Authorization"] = f"Bearer {self.token['access_token']}"
                client = self.client
            else:
                # Use plain httpx client if no token
                client = httpx.AsyncClient()

            print(
                f"[MCPClient] Sending JSON-RPC request to {self.mcp_url}: method={payload.get('method')} id={payload.get('id')}"
            )
            if self.token:
                resp = await client.post(self.mcp_url, json=payload, headers=headers)
            else:
                async with client as tmp_client:
                    resp = await tmp_client.post(self.mcp_url, json=payload, headers=headers)
            if resp.status_code == 401 and not tried_auth:
                print("[MCPClient] 401 Unauthorized, attempting authentication...")
                await self._fetch_token()
                tried_auth = True
                continue
            resp.raise_for_status()
            data = resp.json()
            print(f"[MCPClient] Received response: {data}")
            return data

    async def healthz(self) -> dict:
        """Check MCP server health via /healthz endpoint."""
        print(f"[MCPClient] Server {self.mcp_url} ")
        # Safely construct healthz URL using urlparse
        parsed = urlparse(self.mcp_url)
        hostname = parsed.hostname.decode() if isinstance(parsed.hostname, bytes) else parsed.hostname
        scheme = parsed.scheme.decode() if isinstance(parsed.scheme, bytes) else parsed.scheme
        healthz_url = f"{scheme}://{hostname}:{parsed.port}/healthz"
        print(f"[MCPClient] Checking health at {healthz_url}")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(healthz_url)
            resp.raise_for_status()
            data = resp.json()
            print(f"[MCPClient] /healthz response: {data}")
            return data
        except Exception as e:
            print(f"[MCPClient] /healthz error: {e}")
            raise Exception(f"healthz check failed: {e}")

    async def list_tools(self) -> Any:
        """List available tools from the MCP server."""
        print("[MCPClient] Calling list_tools()")
        request_id = str(uuid.uuid4())
        payload = JSONRPCRequest(
            jsonrpc="2.0",
            method="list_tools",
            params=None,
            id=request_id,
        ).dict()

        data = await self._request(payload)
        rpc = JSONRPCResponse(**data)
        if rpc.error:
            err: JSONRPCError = rpc.error
            print(f"[MCPClient] list_tools error: code={err.code}, message={err.message}")
            raise Exception(f"list_tools failed (code={err.code}): {err.message}")

        print(f"[MCPClient] list_tools result: {rpc.result}")
        return rpc.result

    async def invoke_tool(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        request_id: Optional[Any] = None,
    ) -> Any:
        """Invoke a tool on the MCP server."""
        print(f"[MCPClient] Calling invoke_tool(method={method})")
        if request_id is None:
            request_id = str(uuid.uuid4())

        payload = JSONRPCRequest(
            jsonrpc="2.0",
            method=method,
            params=params,
            id=request_id,
        ).dict()

        data = await self._request(payload)
        rpc = JSONRPCResponse(**data)
        if rpc.error:
            err: JSONRPCError = rpc.error
            print(f"[MCPClient] invoke_tool error: code={err.code}, message={err.message}")
            raise Exception(f"invoke_tool failed (code={err.code}): {err.message}")

        print(f"[MCPClient] invoke_tool result: {rpc.result}")
        return rpc.result
