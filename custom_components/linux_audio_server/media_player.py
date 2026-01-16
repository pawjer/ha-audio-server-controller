"""Media player platform for Linux Audio Server."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
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
    """Set up Linux Audio Server media player entities."""
    coordinator: LinuxAudioServerCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create media player entities for each sink
    entities = []
    for sink in coordinator.data.get("sinks", []):
        entities.append(AudioSinkMediaPlayer(coordinator, entry, sink))

    async_add_entities(entities)

    # Set up a listener to add new sinks dynamically
    async def async_update_entities() -> None:
        """Update entities when coordinator data changes."""
        current_entities = {entity.unique_id for entity in entities}
        new_sinks = coordinator.data.get("sinks", [])

        for sink in new_sinks:
            unique_id = f"{entry.entry_id}_{sink['name']}"
            if unique_id not in current_entities:
                new_entity = AudioSinkMediaPlayer(coordinator, entry, sink)
                entities.append(new_entity)
                async_add_entities([new_entity])

    coordinator.async_add_listener(async_update_entities)


class AudioSinkMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Representation of an audio sink as a media player."""

    _attr_has_entity_name = True
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER
    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
        sink: dict[str, Any],
    ) -> None:
        """Initialize the media player."""
        super().__init__(coordinator)
        self._entry = entry
        self._sink_name = sink["name"]
        self._attr_unique_id = f"{entry.entry_id}_{sink['name']}"
        self._attr_name = sink["description"]

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information about this entity."""
        sink = self._sink_data
        device_name = sink.get("description", self._sink_name) if sink else self._sink_name
        return {
            "identifiers": {(DOMAIN, self._sink_name)},
            "name": device_name,
            "manufacturer": "Linux Audio Server",
            "model": "Audio Sink",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self._sink_data is not None

    @property
    def _sink_data(self) -> dict[str, Any] | None:
        """Get the current sink data from coordinator."""
        for sink in self.coordinator.data.get("sinks", []):
            if sink["name"] == self._sink_name:
                return sink
        return None

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the device."""
        sink = self._sink_data
        if sink is None:
            return MediaPlayerState.OFF

        # Map PulseAudio states to media player states
        pa_state = sink.get("state", "IDLE")
        if pa_state == "RUNNING":
            return MediaPlayerState.PLAYING
        elif pa_state in ("IDLE", "SUSPENDED"):
            return MediaPlayerState.IDLE
        else:
            return MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        sink = self._sink_data
        return sink.get("volume") if sink else None

    @property
    def is_volume_muted(self) -> bool | None:
        """Return boolean if volume is currently muted."""
        sink = self._sink_data
        return sink.get("muted") if sink else None

    @property
    def source(self) -> str | None:
        """Return the current input source."""
        # The current sink is the "source" from media player perspective
        sink = self._sink_data
        return sink.get("description") if sink else None

    @property
    def source_list(self) -> list[str]:
        """List of available input sources."""
        # All available sinks
        return [
            sink["description"]
            for sink in self.coordinator.data.get("sinks", [])
        ]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        sink = self._sink_data
        if not sink:
            return {}

        return {
            "sink_name": sink.get("name"),
            "sink_index": sink.get("index"),
            "sink_state": sink.get("state"),
            "is_default": sink.get("is_default", False),
        }

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        await self.coordinator.client.set_sink_volume(self._sink_name, volume)
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute the media player."""
        await self.coordinator.client.set_sink_mute(self._sink_name, mute)
        await self.coordinator.async_request_refresh()

    async def async_select_source(self, source: str) -> None:
        """Select input source (set as default sink)."""
        # Find the sink name from description
        for sink in self.coordinator.data.get("sinks", []):
            if sink["description"] == source:
                await self.coordinator.client.set_default_sink(sink["name"])
                await self.coordinator.async_request_refresh()
                return

        _LOGGER.warning("Source '%s' not found in available sinks", source)
