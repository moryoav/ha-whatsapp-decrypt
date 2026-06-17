from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlparse

from aiohttp import ClientError, ClientTimeout

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    ATTR_CODE,
    ATTR_FILENAME,
    ATTR_FFMPEG,
    ATTR_MEDIA_TYPE,
    ATTR_TEXT,
    ATTR_URL,
    ATTR_USER_ID,
)


class InvalidURL(HomeAssistantError):
    """Raised when the configured add-on URL is invalid."""


class CannotConnect(HomeAssistantError):
    """Raised when the add-on cannot be reached."""


def normalize_base_url(base_url: str) -> str:
    """Return a normalized add-on base URL."""
    base_url = base_url.strip().rstrip("/")
    parsed = urlparse(base_url)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise InvalidURL("Add-on URL must be an absolute http or https URL")

    return base_url


class WhatsAppMediaProcessorClient:
    """Client for the WhatsApp Media Processor add-on HTTP API."""

    def __init__(self, hass: HomeAssistant, base_url: str) -> None:
        self._hass = hass
        self.base_url = normalize_base_url(base_url)

    async def async_health_check(self) -> None:
        """Verify that the add-on is reachable."""
        try:
            await self._request("health", {}, timeout=10)
        except HomeAssistantError as exc:
            raise CannotConnect(
                f"Could not reach WhatsApp Media Processor at {self.base_url}"
            ) from exc

    async def async_process_audio(
        self,
        code: str,
        url: str,
        timeout: int,
    ) -> dict[str, Any]:
        """Process a WhatsApp audio message."""
        return await self._request(
            "",
            {
                ATTR_CODE: code,
                ATTR_URL: url,
                ATTR_MEDIA_TYPE: "audio",
            },
            timeout=timeout,
        )

    async def async_process_document(
        self,
        code: str,
        url: str,
        filename: str,
        timeout: int,
    ) -> dict[str, Any]:
        """Process a WhatsApp document message."""
        return await self._request(
            "",
            {
                ATTR_CODE: code,
                ATTR_URL: url,
                ATTR_FILENAME: filename,
                ATTR_MEDIA_TYPE: "document",
            },
            timeout=timeout,
        )

    async def async_process_image(
        self,
        code: str,
        url: str,
        text: str,
        media_type: str,
        timeout: int,
    ) -> dict[str, Any]:
        """Process a WhatsApp image or sticker message."""
        return await self._request(
            "",
            {
                ATTR_CODE: code,
                ATTR_URL: url,
                ATTR_TEXT: text,
                ATTR_MEDIA_TYPE: media_type,
            },
            timeout=timeout,
        )

    async def async_process_video(
        self,
        ffmpeg: str,
        user_id: str | None,
        timeout: int,
    ) -> dict[str, Any]:
        """Process a WhatsApp video ffmpeg request."""
        params: dict[str, str] = {ATTR_FFMPEG: ffmpeg}
        if user_id:
            params["userId"] = user_id

        return await self._request("", params, timeout=timeout)

    async def _request(
        self,
        path: str,
        params: dict[str, str],
        timeout: int,
    ) -> dict[str, Any]:
        """Call the add-on and return JSON-serializable response data."""
        session = async_get_clientsession(self._hass)
        url = f"{self.base_url}/{path.lstrip('/')}" if path else f"{self.base_url}/"

        try:
            async with session.get(
                url,
                params=params,
                timeout=ClientTimeout(total=timeout),
            ) as response:
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    payload: Any = await response.json(content_type=None)
                else:
                    payload = await response.text()

                if response.status >= 400:
                    detail = payload.get("error") if isinstance(payload, dict) else payload
                    raise HomeAssistantError(
                        f"WhatsApp Media Processor returned HTTP {response.status}: {detail}"
                    )

                return self._format_response(payload, response.status, content_type)
        except (asyncio.TimeoutError, ClientError) as exc:
            raise CannotConnect(f"Could not reach WhatsApp Media Processor at {url}") from exc

    @staticmethod
    def _format_response(
        payload: Any,
        status: int,
        content_type: str,
    ) -> dict[str, Any]:
        """Normalize add-on responses for Home Assistant service response data."""
        if isinstance(payload, dict):
            response = dict(payload)
        else:
            response = {"text": payload}

        response["http_status"] = status
        response["content_type"] = content_type
        return response
