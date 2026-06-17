from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from urllib.parse import urlparse

try:
    from homeassistant.components.hassio import get_addons_info
except ImportError:  # pragma: no cover - Home Assistant installations provide hassio.
    get_addons_info = None
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from .client import CannotConnect, InvalidURL, WhatsAppMediaProcessorClient
from .const import (
    ADDON_FALLBACK_HOSTS,
    ADDON_NAME,
    ADDON_PORT,
    ADDON_REPOSITORY,
    ADDON_SLUG,
    CONF_URL,
)


def url_from_discovery_config(config: dict[str, Any]) -> str | None:
    """Build an add-on URL from Supervisor discovery config."""
    if url := config.get(CONF_URL):
        return normalize_url(str(url))

    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT, ADDON_PORT)
    if host:
        return normalize_url(f"http://{host}:{port}")

    return None


def normalize_url(url: str) -> str:
    """Normalize and validate an add-on URL."""
    url = url.strip().rstrip("/")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise InvalidURL("Add-on URL must be an absolute http or https URL")
    return url


async def async_detect_addon_url(
    hass: HomeAssistant,
    preferred_urls: Iterable[str] = (),
) -> str:
    """Detect the local WhatsApp Media Processor add-on URL."""
    last_error: CannotConnect | None = None

    for url in candidate_urls(hass, preferred_urls):
        try:
            await async_validate_url(hass, url)
        except CannotConnect as exc:
            last_error = exc
            continue
        return url

    raise CannotConnect("Could not detect the WhatsApp Media Processor add-on") from last_error


def candidate_urls(hass: HomeAssistant, preferred_urls: Iterable[str]) -> list[str]:
    """Return ordered candidate add-on URLs."""
    candidates: list[str] = []
    candidates.extend(preferred_urls)

    if get_addons_info is not None and (addons_info := get_addons_info(hass)):
        for slug, addon in addons_info.items():
            if addon_matches(slug, addon):
                candidates.extend(addon_info_urls(slug, addon))

    candidates.extend(f"http://{host}:{ADDON_PORT}" for host in ADDON_FALLBACK_HOSTS)
    return dedupe_urls(candidates)


def addon_matches(slug: str, addon: dict[str, Any]) -> bool:
    """Return whether Supervisor add-on metadata looks like this add-on."""
    slug_value = clean(addon.get("slug", slug))
    hostname = clean(addon.get("hostname"))
    name = clean(addon.get("name"))
    repository = clean(addon.get("repository"))
    url = clean(addon.get("url"))

    return (
        ADDON_SLUG in slug_value
        or ADDON_SLUG.replace("_", "-") in slug_value
        or ADDON_SLUG in hostname
        or ADDON_SLUG.replace("_", "-") in hostname
        or name == ADDON_NAME.casefold()
        or ADDON_REPOSITORY in repository
        or ADDON_REPOSITORY in url
    )


def addon_info_urls(slug: str, addon: dict[str, Any]) -> list[str]:
    """Return possible internal URLs from Supervisor add-on metadata."""
    hosts = [
        addon.get("hostname"),
        addon.get("host"),
        addon.get("slug", slug),
        slug,
    ]

    normalized_hosts: list[str] = []
    for host in hosts:
        if not host:
            continue
        host = str(host)
        normalized_hosts.append(host)
        normalized_hosts.append(host.replace("_", "-"))

    return [f"http://{host}:{ADDON_PORT}" for host in normalized_hosts]


def dedupe_urls(urls: Iterable[str]) -> list[str]:
    """Return normalized URLs in insertion order."""
    deduped: list[str] = []
    for url in urls:
        try:
            normalized = normalize_url(url)
        except InvalidURL:
            continue
        if normalized not in deduped:
            deduped.append(normalized)
    return deduped


def clean(value: Any) -> str:
    """Normalize metadata for matching."""
    return str(value or "").casefold()


async def async_validate_url(hass: HomeAssistant, url: str) -> None:
    """Validate that the add-on URL is reachable."""
    client = WhatsAppMediaProcessorClient(hass, url)
    await client.async_health_check()
