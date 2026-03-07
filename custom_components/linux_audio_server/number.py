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

    # Create latency offset sliders for each Bluetooth sink
    for sink in coordinator.data.get("sinks", []):
        if sink["name"].startswith("bluez_output."):
            entities.append(SinkLatencyOffsetNumber(coordinator, entry, sink))

    async_add_entities(entities)

    # Add latency offset sliders for new BT sinks as they appear
    known_sinks: set[str] = {s["name"] for s in coordinator.data.get("sinks", [])}

    async def _async_update_latency_entities() -> None:
        for sink in coordinator.data.get("sinks", []):
            if sink["name"].startswith("bluez_output.") and sink["name"] not in known_sinks:
                known_sinks.add(sink["name"])
                async_add_entities([SinkLatencyOffsetNumber(coordinator, entry, sink)])

    coordinator.async_add_listener(_async_update_latency_entities)


class SourceVolumeNumber(CoordinatorEntity, NumberEntity):
    """Base class for source volume control.

    When streaming: shows and controls the live stream volume.
    When idle: shows the last known stream volume (cached in memory).
    Setting while idle updates the cache only — no API call, no sink cascade.
    """

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
        source_default_id: str,
    ) -> None:
        """Initialize the source volume number entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._source_name = source_name
        self._source_identifier = source_identifier
        self._source_default_id = source_default_id
        self._attr_unique_id = f"{entry.entry_id}_{source_name.lower().replace(' ', '_')}_volume"
        self._attr_name = f"{source_name} Volume"
        self._last_volume: float = 0.5

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
        """Find the active sink-input for this source."""
        sink_inputs = self.coordinator.data.get("sink_inputs", [])
        identifier = self._source_identifier.lower().replace(" ", "-")
        for sink_input in sink_inputs:
            name = sink_input.get("name", "").lower().replace(" ", "-")
            if identifier in name:
                return sink_input
        return None

    def _default_sink_name(self) -> str | None:
        """Return the stored default sink name for this source."""
        return self.coordinator.data.get("source_defaults", {}).get(self._source_default_id)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> float:
        """Return stream volume when active, or last known volume when idle."""
        sink_input = self._find_sink_input()
        if sink_input:
            self._last_volume = sink_input.get("volume", self._last_volume)
        return self._last_volume

    async def async_set_native_value(self, value: float) -> None:
        """Set stream volume when active. When idle, caches value only — no API call."""
        self._last_volume = value
        try:
            sink_input = self._find_sink_input()
            if sink_input:
                _LOGGER.info("Setting %s stream volume to %.2f", self._source_name, value)
                await self.coordinator.client.set_stream_volume(sink_input["index"], value)
            else:
                _LOGGER.debug("Caching %s volume %.2f — no active stream", self._source_name, value)
        except Exception as err:
            _LOGGER.error("Failed to set %s volume: %s", self._source_name, err)


class AirplayVolumeNumber(SourceVolumeNumber):
    """Number entity for Airplay volume control."""

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize Airplay volume control."""
        super().__init__(coordinator, entry, "Airplay", "Shairport Sync", "airplay")


class TTSVolumeNumber(SourceVolumeNumber):
    """Number entity for TTS volume control."""

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize TTS volume control."""
        super().__init__(coordinator, entry, "TTS", "mopidy-player1", "tts")


class SpotifyVolumeNumber(SourceVolumeNumber):
    """Number entity for Spotify volume control."""

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize Spotify volume control."""
        super().__init__(coordinator, entry, "Spotify", "librespot", "spotify")


class SinkLatencyOffsetNumber(CoordinatorEntity, NumberEntity):
    """Latency offset slider for a Bluetooth sink (0–500 ms).

    Delays the sink relative to others in a combined sink to eliminate echo.
    """

    _attr_has_entity_name = False
    _attr_icon = "mdi:timer-sync-outline"
    _attr_native_min_value = 0
    _attr_native_max_value = 2000
    _attr_native_step = 10
    _attr_native_unit_of_measurement = "ms"
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
        sink: dict[str, Any],
    ) -> None:
        """Initialize the latency offset entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._sink_name = sink["name"]
        self._attr_unique_id = f"{entry.entry_id}_{sink['name']}_latency_offset"
        self._attr_name = f"{sink.get('description', sink['name'])} Latency Offset"

    @property
    def device_info(self) -> dict[str, Any]:
        """Attach to the same device as the media player for this sink."""
        sink = self._sink_data
        device_name = sink.get("description", self._sink_name) if sink else self._sink_name
        return {
            "identifiers": {(DOMAIN, self._sink_name)},
            "name": device_name,
            "manufacturer": "Linux Audio Server",
            "model": "Audio Sink",
        }

    @property
    def _sink_data(self) -> dict[str, Any] | None:
        for sink in self.coordinator.data.get("sinks", []):
            if sink["name"] == self._sink_name:
                return sink
        return None

    @property
    def available(self) -> bool:
        """Available whenever coordinator is healthy."""
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> float:
        """Return the stored latency offset in ms."""
        latency_offsets = self.coordinator.data.get("latency_offsets", {})
        return latency_offsets.get(self._sink_name, 0)

    async def async_set_native_value(self, value: float) -> None:
        """Apply latency offset to the sink."""
        try:
            await self.coordinator.client.set_sink_latency_offset(
                self._sink_name, int(value)
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set latency offset for %s: %s", self._sink_name, err)
