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

"""OAuth authentication helpers."""

import falcon
import httpx
from typing import Dict, Any

WELL_KNOWN_PATH = "/.well-known/oauth-protected-resource"


class WellKnownOAuthResource:
    """
    A minimal RFC 8414–stycdle metadata document for an OAuth2/OpenID Connect server.
    Mount at /.well-known/oauth-protected-resource
    """

    async def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        """Handle GET requests."""
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        resp.media = {
            "issuer": "https://accounts.google.com",
            "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_endpoint": "https://oauth2.googleapis.com/token",
            "jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
            "userinfo_endpoint": "https://openidconnect.googleapis.com/v1/userinfo",
            "response_types_supported": ["code"],
            "scopes_supported": ["openid", "email", "profile"],
        }


class OAuthResourceMiddleware:
    """
    Falcon middleware to protect your API routes as an OAuth2 Resource Server,
    per RFC 9728: https://datatracker.ietf.org/doc/html/rfc9728
    """

    def __init__(self, base_url: str):
        """Initialize with the base URL for resource metadata."""
        # Base URL for your own resource metadata
        self.meta_url = f"{base_url}/{WELL_KNOWN_PATH[1:]}"
        self._metadata: Dict[str, Any] = {}
        self._jwks: Dict[str, Any] = {}

    async def _load_metadata(self) -> None:
        """Load metadata from the well-known URL and cache it."""
        async with httpx.AsyncClient() as client:
            r = await client.get(self.meta_url, timeout=2.0)
            try:
                r.raise_for_status()
                self._metadata = r.json()
                jwks_uri = self._metadata["jwks_uri"]
                jwks_resp = await client.get(jwks_uri, timeout=2.0)
                jwks_resp.raise_for_status()
                self._jwks = jwks_resp.json()
            except httpx.HTTPStatusError as e:
                print(f"Failed to fetch metadata: {e}")
            self._metadata = {"foo": "bar"}  # Placeholder for actual metadata

    async def process_request(self, req: falcon.Request, resp: falcon.Response) -> None:
        """Process incoming requests and validate the access token."""
        if req.path == WELL_KNOWN_PATH:
            return
        if not self._metadata:
            await self._load_metadata()

        token = await self._extract_token(req)
        if token is None:
            raise self._unauthorized()

        # ─── introspect the opaque access token ────────────────────────────────────
        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(
                    "https://oauth2.googleapis.com/tokeninfo",
                    params={"access_token": token},
                    timeout=2.0,
                )
                r.raise_for_status()
            except httpx.HTTPError:
                # invalid or expired token
                raise self._unauthorized(error="invalid_token")

            info = r.json()
            # info contains fields like "audience", "expires_in", "scope", "email", "user_id", etc.

        # ─── basic validation ──────────────────────────────────────────────────────
        # 1) confirm the token was issued to your API
        expected_aud = self._metadata.get("resource") or self._metadata.get("audience")
        if expected_aud and info.get("audience") != expected_aud:
            raise self._unauthorized(error="invalid_token")

        # 2) check scopes
        required = getattr(req.context, "required_scope", None)
        if required:
            scopes = info.get("scope", "").split()
            if required not in scopes:
                raise self._unauthorized(error="insufficient_scope")

        # ─── attach the token info to the request for your handlers ─────────────────
        req.context.user = {
            "sub": info.get("sub") or info.get("aud"),
            "email": info.get("email"),
            "scope": info.get("scope").split(),
        }

    async def _extract_token(self, req: falcon.Request) -> str | None:
        """Extract the access token from the request."""
        # 1) Authorization header
        hdr = req.get_header("Authorization")
        if hdr and hdr.lower().startswith("bearer "):
            token = hdr.split(None, 1)[1]
            if isinstance(token, str):
                return token
            return None
        # 2) POST body
        if req.method.upper() == "POST":
            media = await req.get_media()
            if isinstance(media, dict) and "access_token" in media:
                token = media["access_token"]
                if isinstance(token, str):
                    return token
                return None
        # 3) Query param
        param = req.get_param("access_token")
        if isinstance(param, str):
            return param
        return None

    def _unauthorized(self, error: str | None = None) -> falcon.HTTPUnauthorized:
        """Return an HTTP 401 Unauthorized response."""
        # Tell client where to find your resource metadata
        challenge = f'Bearer resource_metadata="{self.meta_url}"'
        if error:
            challenge += f', error="{error}"'
        return falcon.HTTPUnauthorized(
            title="Unauthorized",
            description="Access token is missing or invalid.",
            challenges=[challenge],
        )
