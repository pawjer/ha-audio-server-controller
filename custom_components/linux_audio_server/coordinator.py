"""Data update coordinator for Linux Audio Server."""
from __future__ import annotations

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
            # Fetch all data in parallel
            sinks_data = await self.client.get_sinks()
            sink_inputs_data = await self.client.get_sink_inputs()
            default_sink_data = await self.client.get_default_sink()

            return {
                "sinks": sinks_data.get("sinks", []),
                "default_sink": default_sink_data.get("default_sink"),
                "sink_inputs": sink_inputs_data.get("sink_inputs", []),
            }
        except ApiClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
