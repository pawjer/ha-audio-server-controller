"""Data update coordinator for Linux Audio Server."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
import time
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApiClientError, LinuxAudioServerApiClient

_LOGGER = logging.getLogger(__name__)


class LinuxAudioServerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Linux Audio Server data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: LinuxAudioServerApiClient,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Linux Audio Server",
            update_interval=timedelta(seconds=15),  # Reduced polling frequency (WebSocket is primary)
        )
        self.client = client
        self._ws_task = None
        self._ws_reconnect_delay = 5

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        poll_start = time.time()
        _LOGGER.debug("Starting data update poll cycle")

        try:
            # Fetch core data in parallel
            # Note: sinks_data already contains default_sink AND combined sinks
            core_start = time.time()
            sinks_data, sink_inputs_data = await asyncio.gather(
                self.client.get_sinks(),
                self.client.get_sink_inputs(),
            )
            core_time = time.time() - core_start
            _LOGGER.debug("Core data fetched in %.3fs", core_time)

            playback_data = {}
            try:
                playback_data = await self.client.get_playback_status()
            except ApiClientError as err:
                _LOGGER.debug("Failed to fetch playback status: %s", err)

            # Gracefully fetch optional features (radio and Bluetooth)
            # If these fail, the integration continues to work
            radio_data = {}
            try:
                radio_data = await self.client.get_radio_streams()
            except ApiClientError as err:
                _LOGGER.debug("Failed to fetch radio streams: %s", err)
                radio_data = {"streams": {}}

            bluetooth_data = {}
            try:
                bluetooth_data = await self.client.get_bluetooth_devices()
                # Check if Bluetooth is available (new field from backend)
                if not bluetooth_data.get("available", True):
                    _LOGGER.debug("Bluetooth service not yet available, will retry on next update")
            except ApiClientError as err:
                _LOGGER.debug("Failed to fetch Bluetooth devices: %s", err)
                bluetooth_data = {"devices": [], "available": False}

            keep_alive_data = {}
            try:
                keep_alive_data = await self.client.get_keep_alive_status()
            except ApiClientError as err:
                _LOGGER.debug("Failed to fetch keep-alive status: %s", err)
                keep_alive_data = {"enabled": False, "interval": 240, "enabled_sinks": []}

            # Fetch multi-player data (optional feature)
            players_data = {}
            player_assignments_data = {}
            try:
                players_data = await self.client.get_players()
                player_assignments_data = await self.client.get_player_assignments()
            except ApiClientError as err:
                _LOGGER.debug("Failed to fetch player data: %s", err)
                players_data = {"players": []}
                player_assignments_data = {"assignments": {}}

            source_defaults_data = {}
            try:
                source_defaults_data = await self.client.get_source_defaults()
            except ApiClientError as err:
                _LOGGER.debug("Failed to fetch source defaults: %s", err)
                source_defaults_data = {"source_defaults": {}}

            # Fetch latency offsets for all BT sinks in parallel
            bt_sink_names = [
                sink.get("name", "")
                for sink in sinks_data.get("sinks", [])
                if sink.get("name", "").startswith("bluez_output.")
            ]
            latency_offsets: dict[str, int] = {}
            if bt_sink_names:
                async def _fetch_offset(sink_name):
                    try:
                        data = await self.client.get_sink_latency_offset(sink_name)
                        return sink_name, data.get("offset_ms", 0)
                    except ApiClientError:
                        return sink_name, 0

                offset_results = await asyncio.gather(*(_fetch_offset(n) for n in bt_sink_names))
                latency_offsets = {name: offset for name, offset in offset_results if offset}

            result = {
                "sinks": sinks_data.get("sinks", []),
                "default_sink": sinks_data.get("default_sink"),
                "sink_inputs": sink_inputs_data.get("sink_inputs", []),
                "playback": playback_data,
                "radio_streams": radio_data.get("streams", {}),
                "bluetooth_devices": bluetooth_data.get("devices", []),
                "keep_alive": keep_alive_data,
                "players": players_data.get("players", []),
                "player_assignments": player_assignments_data.get("assignments", {}),
                "source_defaults": source_defaults_data.get("source_defaults", {}),
                "latency_offsets": latency_offsets,
            }

            total_time = time.time() - poll_start
            _LOGGER.debug("Data update poll cycle completed in %.3fs", total_time)
            return result

        except ApiClientError as err:
            elapsed = time.time() - poll_start
            _LOGGER.error("Data update poll cycle failed after %.3fs: %s", elapsed, err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def async_start_websocket(self):
        """Start WebSocket listener for real-time updates."""
        if self._ws_task and not self._ws_task.done():
            _LOGGER.warning("WebSocket task already running")
            return

        _LOGGER.info("Starting WebSocket listener for real-time updates")
        self._ws_task = asyncio.create_task(self._websocket_listener())

    async def async_stop_websocket(self):
        """Stop WebSocket listener."""
        if self._ws_task and not self._ws_task.done():
            _LOGGER.info("Stopping WebSocket listener")
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass

    async def _websocket_listener(self):
        """Listen to WebSocket events and trigger updates."""
        while True:
            try:
                _LOGGER.info("Connecting to WebSocket event stream...")
                await self.client.connect_websocket(self._handle_websocket_event)

            except ApiClientError as err:
                _LOGGER.error(f"WebSocket connection failed: {err}")

            except asyncio.CancelledError:
                _LOGGER.info("WebSocket listener cancelled")
                raise

            except Exception as err:
                _LOGGER.error(f"Unexpected WebSocket error: {err}")

            # Wait before reconnecting
            _LOGGER.info(f"Reconnecting WebSocket in {self._ws_reconnect_delay} seconds...")
            await asyncio.sleep(self._ws_reconnect_delay)

    async def _handle_websocket_event(self, event_data: dict):
        """Handle incoming WebSocket event."""
        event_source = event_data.get("source")

        # PulseAudio uses 'event_type', Mopidy uses 'event'
        event_type = event_data.get("event_type") or event_data.get("event")
        event_facility = event_data.get("facility")

        _LOGGER.debug(f"WebSocket event: {event_source}.{event_type} (facility: {event_facility})")

        # For any relevant event, trigger a data refresh
        if event_source in ("mopidy", "pulseaudio"):
            _LOGGER.info(
                f"Triggering update from WebSocket event: {event_source}.{event_type} "
                f"(facility: {event_facility})"
            )

            # Add small delay for sink creation events to ensure PulseAudio has fully initialized
            # This prevents race conditions where the WebSocket event arrives before sink data is available
            if event_source == "pulseaudio" and event_facility == "sink" and event_type == "new":
                _LOGGER.debug("New sink detected, waiting 0.5s for PulseAudio initialization")
                await asyncio.sleep(0.5)

            await self.async_request_refresh()
            try:
                _LOGGER.debug(f"Data refresh completed, notifying {len(self._listeners)} listeners")
            except AttributeError:
                _LOGGER.debug("Data refresh completed, notifying listeners")
