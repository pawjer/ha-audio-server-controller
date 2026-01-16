"""Select platform for Linux Audio Server."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import LinuxAudioServerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Linux Audio Server select entities."""
    coordinator: LinuxAudioServerCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create ONE radio station selector per integration
    async_add_entities([RadioStationSelect(coordinator, entry)])


class RadioStationSelect(CoordinatorEntity, SelectEntity):
    """Select entity for choosing radio stations."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:radio"

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_radio_station_selector"
        self._attr_name = "Radio Station"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Linux Audio Server",
            "manufacturer": "Linux Audio Server",
            "model": "Audio Controller",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and len(self.options) > 0
        )

    @property
    def options(self) -> list[str]:
        """Return list of radio station names."""
        streams_dict = self.coordinator.data.get("radio_streams", {})
        # Convert dictionary keys to list
        return list(streams_dict.keys())

    @property
    def current_option(self) -> str | None:
        """Return currently playing station if any."""
        playback = self.coordinator.data.get("playback", {})
        track = playback.get("track", {})
        # Check if current track is from radio
        title = track.get("name")
        if title and title in self.options:
            return title
        return None

    async def async_select_option(self, option: str) -> None:
        """Play the selected radio station."""
        try:
            await self.coordinator.client.play_radio_stream(option)
            await self.coordinator.async_request_refresh()
            _LOGGER.info("Playing radio station: %s", option)
        except Exception as err:
            _LOGGER.error("Failed to play radio station %s: %s", option, err)
