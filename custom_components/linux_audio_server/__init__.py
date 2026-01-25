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
SERVICE_MOVE_ALL_STREAMS = "move_all_streams"
SERVICE_SET_STREAM_VOLUME = "set_stream_volume"
SERVICE_SET_STREAM_MUTE = "set_stream_mute"
SERVICE_ADD_RADIO_STREAM = "add_radio_stream"
SERVICE_DELETE_RADIO_STREAM = "delete_radio_stream"
SERVICE_UPDATE_RADIO_STREAM = "update_radio_stream"
SERVICE_PLAY_RADIO_STREAM = "play_radio_stream"
SERVICE_PLAY_RADIO_URL = "play_radio_url"
SERVICE_BLUETOOTH_PAIR = "bluetooth_pair"
SERVICE_BLUETOOTH_CONNECT = "bluetooth_connect"
SERVICE_BLUETOOTH_DISCONNECT = "bluetooth_disconnect"
SERVICE_BLUETOOTH_CONNECT_AND_SET_DEFAULT = "bluetooth_connect_and_set_default"
SERVICE_TTS_SPEAK = "tts_speak"
SERVICE_GET_TTS_SETTINGS = "get_tts_settings"
SERVICE_SET_TTS_SETTINGS = "set_tts_settings"
SERVICE_KEEP_ALIVE_START = "keep_alive_start"
SERVICE_KEEP_ALIVE_STOP = "keep_alive_stop"
SERVICE_KEEP_ALIVE_SET_INTERVAL = "keep_alive_set_interval"
SERVICE_KEEP_ALIVE_ENABLE_SINK = "keep_alive_enable_sink"
SERVICE_KEEP_ALIVE_DISABLE_SINK = "keep_alive_disable_sink"
SERVICE_CLEANUP_STALE_BLUETOOTH = "cleanup_stale_bluetooth"
SERVICE_PAUSE_ALL = "pause_all"
SERVICE_STOP_ALL = "stop_all"
SERVICE_BLUETOOTH_SCAN = "bluetooth_scan"
SERVICE_ASSIGN_PLAYER = "assign_player"

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.BUTTON,
    Platform.DEVICE_TRACKER,
    Platform.NUMBER,
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

    async def handle_move_all_streams(call: ServiceCall) -> None:
        """Handle moving all streams to different output (follow me)."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            sink_name = call.data["sink_name"]
            result = await coordinator.client.move_all_streams(sink_name)
            await coordinator.async_request_refresh()
            moved_count = result.get("moved_count", 0)
            _LOGGER.info("Moved %s stream(s) to sink '%s'", moved_count, sink_name)
        except ApiClientError as err:
            _LOGGER.error("Failed to move all streams: %s", err)
            raise HomeAssistantError(f"Failed to move all streams: {err}") from err

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

    async def handle_set_stream_mute(call: ServiceCall) -> None:
        """Handle muting/unmuting a stream."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            stream_index = call.data["stream_index"]
            mute = call.data["mute"]
            await coordinator.client.set_stream_mute(stream_index, mute)
            await coordinator.async_request_refresh()
            _LOGGER.info("Set stream %s mute to %s", stream_index, mute)
        except ApiClientError as err:
            _LOGGER.error("Failed to set stream mute: %s", err)
            raise HomeAssistantError(f"Failed to set stream mute: {err}") from err

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

    async def handle_update_radio_stream(call: ServiceCall) -> None:
        """Handle updating a radio stream."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            name = call.data["name"]
            url = call.data["url"]
            await coordinator.client.update_radio_stream(name, url)
            await coordinator.async_request_refresh()
            _LOGGER.info("Updated radio stream '%s'", name)
        except ApiClientError as err:
            _LOGGER.error("Failed to update radio stream: %s", err)
            raise HomeAssistantError(f"Failed to update radio stream: {err}") from err

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
            sinks = call.data.get("sinks")
            await coordinator.client.speak_tts(message, language, sinks)
            _LOGGER.info("Playing TTS message: %s (language: %s, sinks: %s)", message, language, sinks)
        except ApiClientError as err:
            _LOGGER.error("Failed to play TTS message: %s", err)
            raise HomeAssistantError(f"Failed to play TTS message: {err}") from err

    async def handle_get_tts_settings(call: ServiceCall) -> None:
        """Handle getting TTS settings."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            settings = await coordinator.client.get_tts_settings()
            _LOGGER.info("TTS settings: %s", settings)
            # Return data will be available in service response
            return settings
        except ApiClientError as err:
            _LOGGER.error("Failed to get TTS settings: %s", err)
            raise HomeAssistantError(f"Failed to get TTS settings: {err}") from err

    async def handle_set_tts_settings(call: ServiceCall) -> None:
        """Handle setting TTS default speaker."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            default_sinks = call.data["default_sinks"]
            await coordinator.client.set_tts_settings(default_sinks)
            _LOGGER.info("Set TTS default sinks to: %s", default_sinks)
        except ApiClientError as err:
            _LOGGER.error("Failed to set TTS settings: %s", err)
            raise HomeAssistantError(f"Failed to set TTS settings: {err}") from err

    async def handle_keep_alive_start(call: ServiceCall) -> None:
        """Handle starting Bluetooth keep-alive."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            await coordinator.client.start_keep_alive()
            await coordinator.async_request_refresh()
            _LOGGER.info("Started Bluetooth keep-alive")
        except ApiClientError as err:
            _LOGGER.error("Failed to start keep-alive: %s", err)
            raise HomeAssistantError(f"Failed to start keep-alive: {err}") from err

    async def handle_keep_alive_stop(call: ServiceCall) -> None:
        """Handle stopping Bluetooth keep-alive."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            await coordinator.client.stop_keep_alive()
            await coordinator.async_request_refresh()
            _LOGGER.info("Stopped Bluetooth keep-alive")
        except ApiClientError as err:
            _LOGGER.error("Failed to stop keep-alive: %s", err)
            raise HomeAssistantError(f"Failed to stop keep-alive: {err}") from err

    async def handle_keep_alive_set_interval(call: ServiceCall) -> None:
        """Handle setting keep-alive interval."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            interval = call.data["interval"]
            await coordinator.client.set_keep_alive_interval(interval)
            await coordinator.async_request_refresh()
            _LOGGER.info("Set keep-alive interval to %s seconds", interval)
        except ApiClientError as err:
            _LOGGER.error("Failed to set keep-alive interval: %s", err)
            raise HomeAssistantError(f"Failed to set keep-alive interval: {err}") from err

    async def handle_keep_alive_enable_sink(call: ServiceCall) -> None:
        """Handle enabling keep-alive for a sink."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            sink_name = call.data["sink_name"]
            await coordinator.client.enable_keep_alive_for_sink(sink_name)
            await coordinator.async_request_refresh()
            _LOGGER.info("Enabled keep-alive for sink: %s", sink_name)
        except ApiClientError as err:
            _LOGGER.error("Failed to enable keep-alive for sink: %s", err)
            raise HomeAssistantError(f"Failed to enable keep-alive for sink: {err}") from err

    async def handle_keep_alive_disable_sink(call: ServiceCall) -> None:
        """Handle disabling keep-alive for a sink."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            sink_name = call.data["sink_name"]
            await coordinator.client.disable_keep_alive_for_sink(sink_name)
            await coordinator.async_request_refresh()
            _LOGGER.info("Disabled keep-alive for sink: %s", sink_name)
        except ApiClientError as err:
            _LOGGER.error("Failed to disable keep-alive for sink: %s", err)
            raise HomeAssistantError(f"Failed to disable keep-alive for sink: {err}") from err

    async def handle_cleanup_stale_bluetooth(call: ServiceCall) -> None:
        """Handle cleanup of stale Bluetooth speaker entities."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        # Trigger a coordinator refresh which will run the cleanup logic
        await coordinator.async_request_refresh()
        _LOGGER.info("Triggered cleanup of stale Bluetooth speaker entities")

    async def handle_pause_all(call: ServiceCall) -> None:
        """Handle pausing all Mopidy players."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            await coordinator.client.pause_all()
            await coordinator.async_request_refresh()
            _LOGGER.info("Paused all Mopidy players")
        except ApiClientError as err:
            _LOGGER.error("Failed to pause all players: %s", err)
            raise HomeAssistantError(f"Failed to pause all players: {err}") from err

    async def handle_stop_all(call: ServiceCall) -> None:
        """Handle stopping all Mopidy players."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            await coordinator.client.stop_all()
            await coordinator.async_request_refresh()
            _LOGGER.info("Stopped all Mopidy players")
        except ApiClientError as err:
            _LOGGER.error("Failed to stop all players: %s", err)
            raise HomeAssistantError(f"Failed to stop all players: {err}") from err

    async def handle_bluetooth_scan(call: ServiceCall) -> None:
        """Handle Bluetooth device scan."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            duration = call.data.get("duration", 10)
            await coordinator.client.scan_bluetooth(duration)
            _LOGGER.info("Started Bluetooth scan for %s seconds", duration)
            # Note: coordinator refresh will happen automatically after scan duration
        except ApiClientError as err:
            _LOGGER.error("Failed to start Bluetooth scan: %s", err)
            raise HomeAssistantError(f"Failed to start Bluetooth scan: {err}") from err

    async def handle_assign_player(call: ServiceCall) -> None:
        """Handle assigning a Mopidy player to a sink."""
        coordinator = get_coordinator()
        if not coordinator:
            raise HomeAssistantError("No Linux Audio Server instance available")

        try:
            player_name = call.data["player_name"]
            sink_name = call.data["sink_name"]
            await coordinator.client.assign_player(player_name, sink_name)
            await coordinator.async_request_refresh()
            _LOGGER.info("Assigned player '%s' to sink '%s'", player_name, sink_name)
        except ApiClientError as err:
            _LOGGER.error("Failed to assign player: %s", err)
            raise HomeAssistantError(f"Failed to assign player: {err}") from err

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

    set_stream_mute_schema = vol.Schema({
        vol.Required("stream_index"): vol.All(int, vol.Range(min=0)),
        vol.Required("mute"): cv.boolean,
    })

    add_radio_stream_schema = vol.Schema({
        vol.Required("name"): cv.string,
        vol.Required("url"): cv.string,
    })

    delete_radio_stream_schema = vol.Schema({
        vol.Required("name"): cv.string,
    })

    update_radio_stream_schema = vol.Schema({
        vol.Required("name"): cv.string,
        vol.Required("url"): cv.string,
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
        vol.Optional("sinks"): [cv.string],
    })

    set_tts_settings_schema = vol.Schema({
        vol.Required("default_sinks"): [cv.string],
    })

    move_all_streams_schema = vol.Schema({
        vol.Required("sink_name"): cv.string,
    })

    keep_alive_interval_schema = vol.Schema({
        vol.Required("interval"): vol.All(vol.Coerce(int), vol.Range(min=30, max=600)),
    })

    keep_alive_sink_schema = vol.Schema({
        vol.Required("sink_name"): cv.string,
    })

    bluetooth_scan_schema = vol.Schema({
        vol.Optional("duration", default=10): vol.All(vol.Coerce(int), vol.Range(min=5, max=30)),
    })

    assign_player_schema = vol.Schema({
        vol.Required("player_name"): cv.string,
        vol.Required("sink_name"): cv.string,
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
        SERVICE_MOVE_ALL_STREAMS,
        handle_move_all_streams,
        schema=move_all_streams_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_STREAM_VOLUME,
        handle_set_stream_volume,
        schema=set_stream_volume_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_STREAM_MUTE,
        handle_set_stream_mute,
        schema=set_stream_mute_schema,
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
        SERVICE_UPDATE_RADIO_STREAM,
        handle_update_radio_stream,
        schema=update_radio_stream_schema,
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
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_TTS_SETTINGS,
        handle_get_tts_settings,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TTS_SETTINGS,
        handle_set_tts_settings,
        schema=set_tts_settings_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_KEEP_ALIVE_START,
        handle_keep_alive_start,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_KEEP_ALIVE_STOP,
        handle_keep_alive_stop,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_KEEP_ALIVE_SET_INTERVAL,
        handle_keep_alive_set_interval,
        schema=keep_alive_interval_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_KEEP_ALIVE_ENABLE_SINK,
        handle_keep_alive_enable_sink,
        schema=keep_alive_sink_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_KEEP_ALIVE_DISABLE_SINK,
        handle_keep_alive_disable_sink,
        schema=keep_alive_sink_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEANUP_STALE_BLUETOOTH,
        handle_cleanup_stale_bluetooth,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PAUSE_ALL,
        handle_pause_all,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_ALL,
        handle_stop_all,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_BLUETOOTH_SCAN,
        handle_bluetooth_scan,
        schema=bluetooth_scan_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ASSIGN_PLAYER,
        handle_assign_player,
        schema=assign_player_schema,
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
            hass.services.async_remove(DOMAIN, SERVICE_MOVE_ALL_STREAMS)
            hass.services.async_remove(DOMAIN, SERVICE_SET_STREAM_VOLUME)
            hass.services.async_remove(DOMAIN, SERVICE_SET_STREAM_MUTE)
            hass.services.async_remove(DOMAIN, SERVICE_ADD_RADIO_STREAM)
            hass.services.async_remove(DOMAIN, SERVICE_DELETE_RADIO_STREAM)
            hass.services.async_remove(DOMAIN, SERVICE_UPDATE_RADIO_STREAM)
            hass.services.async_remove(DOMAIN, SERVICE_PLAY_RADIO_STREAM)
            hass.services.async_remove(DOMAIN, SERVICE_PLAY_RADIO_URL)
            hass.services.async_remove(DOMAIN, SERVICE_BLUETOOTH_PAIR)
            hass.services.async_remove(DOMAIN, SERVICE_BLUETOOTH_CONNECT)
            hass.services.async_remove(DOMAIN, SERVICE_BLUETOOTH_DISCONNECT)
            hass.services.async_remove(DOMAIN, SERVICE_BLUETOOTH_CONNECT_AND_SET_DEFAULT)
            hass.services.async_remove(DOMAIN, SERVICE_TTS_SPEAK)
            hass.services.async_remove(DOMAIN, SERVICE_GET_TTS_SETTINGS)
            hass.services.async_remove(DOMAIN, SERVICE_SET_TTS_SETTINGS)
            hass.services.async_remove(DOMAIN, SERVICE_KEEP_ALIVE_START)
            hass.services.async_remove(DOMAIN, SERVICE_KEEP_ALIVE_STOP)
            hass.services.async_remove(DOMAIN, SERVICE_KEEP_ALIVE_SET_INTERVAL)
            hass.services.async_remove(DOMAIN, SERVICE_KEEP_ALIVE_ENABLE_SINK)
            hass.services.async_remove(DOMAIN, SERVICE_KEEP_ALIVE_DISABLE_SINK)
            hass.services.async_remove(DOMAIN, SERVICE_CLEANUP_STALE_BLUETOOTH)
            hass.services.async_remove(DOMAIN, SERVICE_PAUSE_ALL)
            hass.services.async_remove(DOMAIN, SERVICE_STOP_ALL)
            hass.services.async_remove(DOMAIN, SERVICE_BLUETOOTH_SCAN)
            hass.services.async_remove(DOMAIN, SERVICE_ASSIGN_PLAYER)

    return unload_ok
