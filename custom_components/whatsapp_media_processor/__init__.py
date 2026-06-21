from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .client import WhatsAppMediaProcessorClient
from .const import (
    ATTR_CODE,
    ATTR_FILENAME,
    ATTR_FFMPEG,
    ATTR_IMAGE_MODE,
    ATTR_MEDIA_TYPE,
    ATTR_SAVE_DIR,
    ATTR_TEXT,
    ATTR_TIMEOUT,
    ATTR_URL,
    ATTR_USER_ID,
    CONF_BASE_URL,
    DATA_SERVICES_REGISTERED,
    DEFAULT_AUDIO_TIMEOUT,
    DEFAULT_DOCUMENT_TIMEOUT,
    DEFAULT_IMAGE_TIMEOUT,
    DEFAULT_VIDEO_TIMEOUT,
    DOMAIN,
    SERVICE_PROCESS_AUDIO,
    SERVICE_PROCESS_DOCUMENT,
    SERVICE_PROCESS_IMAGE,
    SERVICE_PROCESS_VIDEO,
)

TIMEOUT_SCHEMA = vol.All(vol.Coerce(int), vol.Range(min=1, max=600))

AUDIO_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CODE): cv.string,
        vol.Required(ATTR_URL): cv.string,
        vol.Optional(ATTR_TIMEOUT, default=DEFAULT_AUDIO_TIMEOUT): TIMEOUT_SCHEMA,
    }
)

DOCUMENT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CODE): cv.string,
        vol.Required(ATTR_URL): cv.string,
        vol.Required(ATTR_FILENAME): cv.string,
        vol.Optional(ATTR_SAVE_DIR): cv.string,
        vol.Optional(ATTR_TIMEOUT, default=DEFAULT_DOCUMENT_TIMEOUT): TIMEOUT_SCHEMA,
    }
)

IMAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CODE): cv.string,
        vol.Required(ATTR_URL): cv.string,
        vol.Required(ATTR_TEXT): cv.string,
        vol.Optional(ATTR_MEDIA_TYPE, default="image"): vol.In(["image", "sticker"]),
        vol.Optional(ATTR_IMAGE_MODE, default="auto"): vol.In(
            ["auto", "strict_ocr", "visual_analysis"]
        ),
        vol.Optional(ATTR_TIMEOUT, default=DEFAULT_IMAGE_TIMEOUT): TIMEOUT_SCHEMA,
    }
)

VIDEO_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_FFMPEG): cv.string,
        vol.Optional(ATTR_USER_ID): cv.string,
        vol.Optional(ATTR_TIMEOUT, default=DEFAULT_VIDEO_TIMEOUT): TIMEOUT_SCHEMA,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WhatsApp Media Processor integration."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(DATA_SERVICES_REGISTERED):
        return True

    async def process_audio(call: ServiceCall) -> ServiceResponse | None:
        client = _get_client(hass)
        response = await client.async_process_audio(
            code=call.data[ATTR_CODE],
            url=call.data[ATTR_URL],
            timeout=call.data[ATTR_TIMEOUT],
        )
        return _service_response(call, response)

    async def process_document(call: ServiceCall) -> ServiceResponse | None:
        client = _get_client(hass)
        response = await client.async_process_document(
            code=call.data[ATTR_CODE],
            url=call.data[ATTR_URL],
            filename=call.data[ATTR_FILENAME],
            save_dir=call.data.get(ATTR_SAVE_DIR),
            timeout=call.data[ATTR_TIMEOUT],
        )
        return _service_response(call, response)

    async def process_image(call: ServiceCall) -> ServiceResponse | None:
        client = _get_client(hass)
        response = await client.async_process_image(
            code=call.data[ATTR_CODE],
            url=call.data[ATTR_URL],
            text=call.data[ATTR_TEXT],
            media_type=call.data[ATTR_MEDIA_TYPE],
            image_mode=call.data[ATTR_IMAGE_MODE],
            timeout=call.data[ATTR_TIMEOUT],
        )
        return _service_response(call, response)

    async def process_video(call: ServiceCall) -> ServiceResponse | None:
        client = _get_client(hass)
        response = await client.async_process_video(
            ffmpeg=call.data[ATTR_FFMPEG],
            user_id=call.data.get(ATTR_USER_ID),
            timeout=call.data[ATTR_TIMEOUT],
        )
        return _service_response(call, response)

    hass.services.async_register(
        DOMAIN,
        SERVICE_PROCESS_AUDIO,
        process_audio,
        schema=AUDIO_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PROCESS_DOCUMENT,
        process_document,
        schema=DOCUMENT_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PROCESS_IMAGE,
        process_image,
        schema=IMAGE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PROCESS_VIDEO,
        process_video,
        schema=VIDEO_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    domain_data[DATA_SERVICES_REGISTERED] = True
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WhatsApp Media Processor from a config entry."""
    client = WhatsAppMediaProcessorClient(hass, entry.data[CONF_BASE_URL])
    await client.async_health_check()
    entry.runtime_data = client
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a WhatsApp Media Processor config entry."""
    entry.runtime_data = None
    return True


def _get_client(hass: HomeAssistant) -> WhatsAppMediaProcessorClient:
    """Return the loaded add-on client."""
    entries = hass.config_entries.async_entries(DOMAIN)
    for entry in entries:
        client = getattr(entry, "runtime_data", None)
        if isinstance(client, WhatsAppMediaProcessorClient):
            return client

    raise HomeAssistantError(
        "Set up the WhatsApp Media Processor integration before calling this action"
    )


def _service_response(call: ServiceCall, response: dict[str, Any]) -> ServiceResponse | None:
    """Return service response data only when the caller asked for it."""
    if call.return_response:
        return response
    return None
