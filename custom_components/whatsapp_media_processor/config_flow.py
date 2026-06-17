from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

try:
    from homeassistant.components.hassio import HassioServiceInfo
except ImportError:  # pragma: no cover - Home Assistant installations provide hassio.
    HassioServiceInfo = Any

from .client import CannotConnect, InvalidURL
from .const import CONF_BASE_URL, DOMAIN
from .discovery import async_detect_addon_url, url_from_discovery_config


def schema() -> vol.Schema:
    """Return an empty discovery form schema."""
    return vol.Schema({})


class WhatsAppMediaProcessorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WhatsApp Media Processor."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        try:
            base_url = await self._async_detect_entry_url()
        except CannotConnect:
            errors["base"] = "cannot_connect" if user_input is not None else ""
        else:
            return await self._async_create_or_update_entry(base_url)

        return self.async_show_form(
            step_id="user",
            data_schema=schema(),
            errors={key: value for key, value in errors.items() if value},
        )

    async def async_step_hassio(self, discovery_info: HassioServiceInfo) -> FlowResult:
        """Handle Supervisor add-on discovery."""
        urls = []
        discovery_config = getattr(discovery_info, "config", {})
        try:
            url = url_from_discovery_config(discovery_config)
        except InvalidURL:
            url = None

        if url:
            urls.append(url)

        try:
            base_url = await self._async_detect_entry_url(urls)
        except CannotConnect:
            return self.async_abort(reason="cannot_connect")

        return await self._async_create_or_update_entry(
            base_url,
            title=getattr(discovery_info, "name", "WhatsApp Media Processor"),
        )

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        """Handle YAML import by discovering the local add-on."""
        try:
            base_url = await self._async_detect_entry_url()
        except CannotConnect:
            return self.async_abort(reason="cannot_connect")

        return await self._async_create_or_update_entry(base_url)

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle reconfiguration by rediscovering the add-on URL."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                base_url = await self._async_detect_entry_url()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data_updates={CONF_BASE_URL: base_url},
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema(),
            errors=errors,
        )

    async def _async_detect_entry_url(
        self,
        preferred_urls: list[str] | None = None,
    ) -> str:
        """Discover the add-on URL."""
        return await async_detect_addon_url(self.hass, preferred_urls or [])

    async def _async_create_or_update_entry(
        self,
        base_url: str,
        *,
        title: str = "WhatsApp Media Processor",
    ) -> FlowResult:
        """Create the single config entry or update the existing one."""
        await self.async_set_unique_id(DOMAIN)

        for entry in self._async_current_entries():
            self.hass.config_entries.async_update_entry(
                entry,
                data={**entry.data, CONF_BASE_URL: base_url},
            )
            return self.async_abort(reason="already_configured")

        return self.async_create_entry(
            title=title,
            data={CONF_BASE_URL: base_url},
        )
