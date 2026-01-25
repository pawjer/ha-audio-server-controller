"""Data update coordinator for Linux Audio Server."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
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
            update_interval=timedelta(seconds=5),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # Fetch core data in parallel
            # Note: sinks_data already contains default_sink AND combined sinks
            sinks_data, sink_inputs_data, playback_data = await asyncio.gather(
                self.client.get_sinks(),
                self.client.get_sink_inputs(),
                self.client.get_playback_status(),
            )

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

            return {
                "sinks": sinks_data.get("sinks", []),
                "default_sink": sinks_data.get("default_sink"),
                "sink_inputs": sink_inputs_data.get("sink_inputs", []),
                "playback": playback_data,
                "radio_streams": radio_data.get("streams", {}),
                "bluetooth_devices": bluetooth_data.get("devices", []),
                "keep_alive": keep_alive_data,
                "players": players_data.get("players", []),
                "player_assignments": player_assignments_data.get("assignments", {}),
            }
        except ApiClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
