"""Number platform for Linux Audio Server."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
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
    """Set up Linux Audio Server number entities."""
    coordinator: LinuxAudioServerCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Create volume control entities for audio sources
    entities.append(AirplayVolumeNumber(coordinator, entry))
    entities.append(TTSVolumeNumber(coordinator, entry))
    entities.append(SpotifyVolumeNumber(coordinator, entry))

    async_add_entities(entities)


class SourceVolumeNumber(CoordinatorEntity, NumberEntity):
    """Base class for source volume control."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:volume-high"
    _attr_native_min_value = 0.0
    _attr_native_max_value = 1.0
    _attr_native_step = 0.01
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
        source_name: str,
        source_identifier: str,
    ) -> None:
        """Initialize the source volume number entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._source_name = source_name
        self._source_identifier = source_identifier
        self._attr_unique_id = f"{entry.entry_id}_{source_name.lower().replace(' ', '_')}_volume"
        self._attr_name = f"{source_name} Volume"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Linux Audio Server",
            "manufacturer": "Linux Audio Server",
            "model": "Audio Controller",
        }

    def _find_sink_input(self) -> dict[str, Any] | None:
        """Find the sink-input for this source."""
        sink_inputs = self.coordinator.data.get("sink_inputs", [])
        for sink_input in sink_inputs:
            if self._source_identifier in sink_input.get("name", ""):
                return sink_input
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available (source is active)."""
        return self.coordinator.last_update_success and self._find_sink_input() is not None

    @property
    def native_value(self) -> float | None:
        """Return current volume level."""
        sink_input = self._find_sink_input()
        if not sink_input:
            return None
        return sink_input.get("volume", 0.0)

    async def async_set_native_value(self, value: float) -> None:
        """Set the volume level."""
        try:
            sink_input = self._find_sink_input()
            if not sink_input:
                _LOGGER.warning("Cannot set volume for %s: source not active", self._source_name)
                return

            _LOGGER.info("Setting %s volume to %.2f", self._source_name, value)
            await self.coordinator.client.set_stream_volume(
                sink_input["index"],
                value
            )
            await self.coordinator.async_request_refresh()

        except Exception as err:
            _LOGGER.error(
                "Failed to set %s volume: %s",
                self._source_name,
                err,
            )


class AirplayVolumeNumber(SourceVolumeNumber):
    """Number entity for Airplay volume control."""

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize Airplay volume control."""
        super().__init__(coordinator, entry, "Airplay", "Shairport Sync")


class TTSVolumeNumber(SourceVolumeNumber):
    """Number entity for TTS volume control."""

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize TTS volume control."""
        super().__init__(coordinator, entry, "TTS", "Mopidy Player 1 (TTS)")


class SpotifyVolumeNumber(SourceVolumeNumber):
    """Number entity for Spotify volume control."""

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize Spotify volume control."""
        super().__init__(coordinator, entry, "Spotify", "librespot")
