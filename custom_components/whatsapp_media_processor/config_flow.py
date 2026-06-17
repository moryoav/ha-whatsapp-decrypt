from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .client import CannotConnect, InvalidURL, WhatsAppMediaProcessorClient, normalize_base_url
from .const import CONF_BASE_URL, DEFAULT_BASE_URL, DOMAIN


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> str:
    """Validate the configured add-on URL."""
    base_url = normalize_base_url(data[CONF_BASE_URL])
    client = WhatsAppMediaProcessorClient(hass, base_url)
    await client.async_health_check()
    return base_url


class WhatsAppMediaProcessorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WhatsApp Media Processor."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                base_url = await validate_input(self.hass, user_input)
            except InvalidURL:
                errors[CONF_BASE_URL] = "invalid_url"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(base_url)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="WhatsApp Media Processor",
                    data={CONF_BASE_URL: base_url},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_BASE_URL,
                        default=(user_input or {}).get(CONF_BASE_URL, DEFAULT_BASE_URL),
                    ): str,
                }
            ),
            errors=errors,
        )
