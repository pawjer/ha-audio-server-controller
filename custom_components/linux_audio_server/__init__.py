"""The Linux Audio Server integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ApiClientError, LinuxAudioServerApiClient
from .const import DOMAIN
from .coordinator import LinuxAudioServerCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_CREATE_COMBINED_SINK = "create_combined_sink"
SERVICE_CREATE_STEREO_PAIR = "create_stereo_pair"
SERVICE_DELETE_COMBINED_SINK = "delete_combined_sink"
SERVICE_MOVE_STREAM = "move_stream"
SERVICE_SET_STREAM_VOLUME = "set_stream_volume"
SERVICE_ADD_RADIO_STREAM = "add_radio_stream"
SERVICE_DELETE_RADIO_STREAM = "delete_radio_stream"
SERVICE_PLAY_RADIO_STREAM = "play_radio_stream"
SERVICE_PLAY_RADIO_URL = "play_radio_url"
SERVICE_BLUETOOTH_PAIR = "bluetooth_pair"
SERVICE_BLUETOOTH_CONNECT = "bluetooth_connect"
SERVICE_BLUETOOTH_DISCONNECT = "bluetooth_disconnect"
SERVICE_BLUETOOTH_CONNECT_AND_SET_DEFAULT = "bluetooth_connect_and_set_default"
SERVICE_TTS_SPEAK = "tts_speak"

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.BUTTON,
    Platform.DEVICE_TRACKER,
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

    # Register services only once (for first instance)
    if not hass.services.has_service(DOMAIN, SERVICE_CREATE_COMBINED_SINK):
        await _async_register_services(hass)

    return True


async def _async_register_services(hass: HomeAssistant) -> None:
    """Register integration services."""

    # Helper to get first available coordinator
    def get_coordinator() -> LinuxAudioServerCoordinator | None:
        """Get the first available coordinator."""
        for entry_id, coordinator in hass.data[DOMAIN].items():
            if isinstance(coordinator, LinuxAudioServerCoordinator):
                return coordinator
        return None

    async def handle_create_combined_sink(call: ServiceCall) -> None:
        """Handle creating a combined sink."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            name = call.data["name"]
            sinks = call.data["sinks"]
            await coordinator.client.create_combined_sink(name, sinks)
            await coordinator.async_request_refresh()
            _LOGGER.info("Created combined sink '%s'", name)
        except ApiClientError as err:
            _LOGGER.error("Failed to create combined sink: %s", err)
            raise HomeAssistantError(f"Failed to create combined sink: {err}") from err

    async def handle_create_stereo_pair(call: ServiceCall) -> None:
        """Handle creating a stereo pair."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            name = call.data["name"]
            left_sink = call.data["left_sink"]
            right_sink = call.data["right_sink"]
            await coordinator.client.create_stereo_pair(name, left_sink, right_sink)
            await coordinator.async_request_refresh()
            _LOGGER.info("Created stereo pair '%s'", name)
        except ApiClientError as err:
            _LOGGER.error("Failed to create stereo pair: %s", err)
            raise HomeAssistantError(f"Failed to create stereo pair: {err}") from err

    async def handle_delete_combined_sink(call: ServiceCall) -> None:
        """Handle deleting a combined sink."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            sink_name = call.data["sink_name"]
            await coordinator.client.delete_combined_sink(sink_name)
            await coordinator.async_request_refresh()
            _LOGGER.info("Deleted combined sink '%s'", sink_name)
        except ApiClientError as err:
            _LOGGER.error("Failed to delete combined sink: %s", err)
            raise HomeAssistantError(f"Failed to delete combined sink: {err}") from err

    async def handle_move_stream(call: ServiceCall) -> None:
        """Handle moving a stream to different output."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            stream_index = call.data["stream_index"]
            sink_name = call.data["sink_name"]
            await coordinator.client.move_stream(stream_index, sink_name)
            await coordinator.async_request_refresh()
            _LOGGER.info("Moved stream %s to sink '%s'", stream_index, sink_name)
        except ApiClientError as err:
            _LOGGER.error("Failed to move stream: %s", err)
            raise HomeAssistantError(f"Failed to move stream: {err}") from err

    async def handle_set_stream_volume(call: ServiceCall) -> None:
        """Handle setting stream volume."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            stream_index = call.data["stream_index"]
            volume = call.data["volume"]
            await coordinator.client.set_stream_volume(stream_index, volume)
            await coordinator.async_request_refresh()
            _LOGGER.info("Set stream %s volume to %s", stream_index, volume)
        except ApiClientError as err:
            _LOGGER.error("Failed to set stream volume: %s", err)
            raise HomeAssistantError(f"Failed to set stream volume: {err}") from err

    async def handle_add_radio_stream(call: ServiceCall) -> None:
        """Handle adding a radio stream."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            name = call.data["name"]
            url = call.data["url"]
            await coordinator.client.add_radio_stream(name, url)
            await coordinator.async_request_refresh()
            _LOGGER.info("Added radio stream '%s'", name)
        except ApiClientError as err:
            _LOGGER.error("Failed to add radio stream: %s", err)
            raise HomeAssistantError(f"Failed to add radio stream: {err}") from err

    async def handle_delete_radio_stream(call: ServiceCall) -> None:
        """Handle deleting a radio stream."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            name = call.data["name"]
            await coordinator.client.delete_radio_stream(name)
            await coordinator.async_request_refresh()
            _LOGGER.info("Deleted radio stream '%s'", name)
        except ApiClientError as err:
            _LOGGER.error("Failed to delete radio stream: %s", err)
            raise HomeAssistantError(f"Failed to delete radio stream: {err}") from err

    async def handle_play_radio_stream(call: ServiceCall) -> None:
        """Handle playing a radio stream."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            name = call.data["name"]
            await coordinator.client.play_radio_stream(name)
            await coordinator.async_request_refresh()
            _LOGGER.info("Playing radio stream '%s'", name)
        except ApiClientError as err:
            _LOGGER.error("Failed to play radio stream: %s", err)
            raise HomeAssistantError(f"Failed to play radio stream: {err}") from err

    async def handle_play_radio_url(call: ServiceCall) -> None:
        """Handle playing a radio URL."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            url = call.data["url"]
            await coordinator.client.play_radio_url(url)
            await coordinator.async_request_refresh()
            _LOGGER.info("Playing radio URL: %s", url)
        except ApiClientError as err:
            _LOGGER.error("Failed to play radio URL: %s", err)
            raise HomeAssistantError(f"Failed to play radio URL: {err}") from err

    async def handle_bluetooth_pair(call: ServiceCall) -> None:
        """Handle pairing a Bluetooth device."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            address = call.data["address"]
            await coordinator.client.pair_bluetooth(address)
            await coordinator.async_request_refresh()
            _LOGGER.info("Paired Bluetooth device %s", address)
        except ApiClientError as err:
            _LOGGER.error("Failed to pair Bluetooth device: %s", err)
            raise HomeAssistantError(f"Failed to pair Bluetooth device: {err}") from err

    async def handle_bluetooth_connect(call: ServiceCall) -> None:
        """Handle connecting a Bluetooth device."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            address = call.data["address"]
            await coordinator.client.connect_bluetooth(address)
            await coordinator.async_request_refresh()
            _LOGGER.info("Connected Bluetooth device %s", address)
        except ApiClientError as err:
            _LOGGER.error("Failed to connect Bluetooth device: %s", err)
            raise HomeAssistantError(f"Failed to connect Bluetooth device: {err}") from err

    async def handle_bluetooth_disconnect(call: ServiceCall) -> None:
        """Handle disconnecting a Bluetooth device."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            address = call.data["address"]
            await coordinator.client.disconnect_bluetooth(address)
            await coordinator.async_request_refresh()
            _LOGGER.info("Disconnected Bluetooth device %s", address)
        except ApiClientError as err:
            _LOGGER.error("Failed to disconnect Bluetooth device: %s", err)
            raise HomeAssistantError(f"Failed to disconnect Bluetooth device: {err}") from err

    async def handle_bluetooth_connect_and_set_default(call: ServiceCall) -> None:
        """Handle connecting and setting Bluetooth device as default."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            address = call.data["address"]
            await coordinator.client.connect_and_set_default_bluetooth(address)
            await coordinator.async_request_refresh()
            _LOGGER.info("Connected and set Bluetooth device %s as default", address)
        except ApiClientError as err:
            _LOGGER.error("Failed to connect and set default Bluetooth device: %s", err)
            raise HomeAssistantError(f"Failed to connect and set default Bluetooth device: {err}") from err

    async def handle_tts_speak(call: ServiceCall) -> None:
        """Handle text-to-speech playback."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            message = call.data["message"]
            language = call.data.get("language", "en")
            await coordinator.client.speak_tts(message, language)
            _LOGGER.info("Playing TTS message: %s (language: %s)", message, language)
        except ApiClientError as err:
            _LOGGER.error("Failed to play TTS message: %s", err)
            raise HomeAssistantError(f"Failed to play TTS message: {err}") from err

    # Service schemas
    create_combined_sink_schema = vol.Schema({
        vol.Required("name"): cv.string,
        vol.Required("sinks"): vol.All(cv.ensure_list, [cv.string]),
    })

    create_stereo_pair_schema = vol.Schema({
        vol.Required("name"): cv.string,
        vol.Required("left_sink"): cv.string,
        vol.Required("right_sink"): cv.string,
    })

    delete_combined_sink_schema = vol.Schema({
        vol.Required("sink_name"): cv.string,
    })

    move_stream_schema = vol.Schema({
        vol.Required("stream_index"): vol.All(int, vol.Range(min=0)),
        vol.Required("sink_name"): cv.string,
    })

    set_stream_volume_schema = vol.Schema({
        vol.Required("stream_index"): vol.All(int, vol.Range(min=0)),
        vol.Required("volume"): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
    })

    add_radio_stream_schema = vol.Schema({
        vol.Required("name"): cv.string,
        vol.Required("url"): cv.string,
    })

    delete_radio_stream_schema = vol.Schema({
        vol.Required("name"): cv.string,
    })

    play_radio_stream_schema = vol.Schema({
        vol.Required("name"): cv.string,
    })

    play_radio_url_schema = vol.Schema({
        vol.Required("url"): cv.string,
    })

    bluetooth_address_schema = vol.Schema({
        vol.Required("address"): cv.string,
    })

    tts_speak_schema = vol.Schema({
        vol.Required("message"): cv.string,
        vol.Optional("language", default="en"): cv.string,
    })

    # Register services with schemas
    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_COMBINED_SINK,
        handle_create_combined_sink,
        schema=create_combined_sink_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_STEREO_PAIR,
        handle_create_stereo_pair,
        schema=create_stereo_pair_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_COMBINED_SINK,
        handle_delete_combined_sink,
        schema=delete_combined_sink_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_MOVE_STREAM,
        handle_move_stream,
        schema=move_stream_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_STREAM_VOLUME,
        handle_set_stream_volume,
        schema=set_stream_volume_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_RADIO_STREAM,
        handle_add_radio_stream,
        schema=add_radio_stream_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_RADIO_STREAM,
        handle_delete_radio_stream,
        schema=delete_radio_stream_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PLAY_RADIO_STREAM,
        handle_play_radio_stream,
        schema=play_radio_stream_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PLAY_RADIO_URL,
        handle_play_radio_url,
        schema=play_radio_url_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_BLUETOOTH_PAIR,
        handle_bluetooth_pair,
        schema=bluetooth_address_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_BLUETOOTH_CONNECT,
        handle_bluetooth_connect,
        schema=bluetooth_address_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_BLUETOOTH_DISCONNECT,
        handle_bluetooth_disconnect,
        schema=bluetooth_address_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_BLUETOOTH_CONNECT_AND_SET_DEFAULT,
        handle_bluetooth_connect_and_set_default,
        schema=bluetooth_address_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_TTS_SPEAK,
        handle_tts_speak,
        schema=tts_speak_schema,
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

        # Unregister services if this was the last instance
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_CREATE_COMBINED_SINK)
            hass.services.async_remove(DOMAIN, SERVICE_CREATE_STEREO_PAIR)
            hass.services.async_remove(DOMAIN, SERVICE_DELETE_COMBINED_SINK)
            hass.services.async_remove(DOMAIN, SERVICE_MOVE_STREAM)
            hass.services.async_remove(DOMAIN, SERVICE_SET_STREAM_VOLUME)
            hass.services.async_remove(DOMAIN, SERVICE_ADD_RADIO_STREAM)
            hass.services.async_remove(DOMAIN, SERVICE_DELETE_RADIO_STREAM)
            hass.services.async_remove(DOMAIN, SERVICE_PLAY_RADIO_STREAM)
            hass.services.async_remove(DOMAIN, SERVICE_PLAY_RADIO_URL)
            hass.services.async_remove(DOMAIN, SERVICE_BLUETOOTH_PAIR)
            hass.services.async_remove(DOMAIN, SERVICE_BLUETOOTH_CONNECT)
            hass.services.async_remove(DOMAIN, SERVICE_BLUETOOTH_DISCONNECT)
            hass.services.async_remove(DOMAIN, SERVICE_BLUETOOTH_CONNECT_AND_SET_DEFAULT)
            hass.services.async_remove(DOMAIN, SERVICE_TTS_SPEAK)

    return unload_ok
