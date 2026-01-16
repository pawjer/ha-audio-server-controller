"""The Linux Audio Server integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LinuxAudioServerApiClient
from .const import DOMAIN
from .coordinator import LinuxAudioServerCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.SWITCH,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Linux Audio Server from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create API client
    session = async_get_clientsession(hass)
    client = LinuxAudioServerApiClient(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        session=session,
    )

    # Create coordinator
    coordinator = LinuxAudioServerCoordinator(hass, client)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    async def handle_create_combined_sink(call: ServiceCall) -> None:
        """Handle creating a combined sink."""
        name = call.data.get("name")
        sinks = call.data.get("sinks")
        await coordinator.client.create_combined_sink(name, sinks)
        await coordinator.async_request_refresh()

    async def handle_create_stereo_pair(call: ServiceCall) -> None:
        """Handle creating a stereo pair."""
        name = call.data.get("name")
        left_sink = call.data.get("left_sink")
        right_sink = call.data.get("right_sink")
        await coordinator.client.create_stereo_pair(name, left_sink, right_sink)
        await coordinator.async_request_refresh()

    async def handle_delete_combined_sink(call: ServiceCall) -> None:
        """Handle deleting a combined sink."""
        sink_name = call.data.get("sink_name")
        await coordinator.client.delete_combined_sink(sink_name)
        await coordinator.async_request_refresh()

    async def handle_move_stream(call: ServiceCall) -> None:
        """Handle moving a stream to different output."""
        stream_index = call.data.get("stream_index")
        sink_name = call.data.get("sink_name")
        await coordinator.client.move_stream(stream_index, sink_name)
        await coordinator.async_request_refresh()

    async def handle_set_stream_volume(call: ServiceCall) -> None:
        """Handle setting stream volume."""
        stream_index = call.data.get("stream_index")
        volume = call.data.get("volume")
        await coordinator.client.set_stream_volume(stream_index, volume)
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN, "create_combined_sink", handle_create_combined_sink
    )
    hass.services.async_register(
        DOMAIN, "create_stereo_pair", handle_create_stereo_pair
    )
    hass.services.async_register(
        DOMAIN, "delete_combined_sink", handle_delete_combined_sink
    )
    hass.services.async_register(DOMAIN, "move_stream", handle_move_stream)
    hass.services.async_register(
        DOMAIN, "set_stream_volume", handle_set_stream_volume
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
