"""Sensor platform for Linux Audio Server."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
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
    """Set up Linux Audio Server sensor entities."""
    coordinator: LinuxAudioServerCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create a sensor for active streams count
    entities = [ActiveStreamsSensor(coordinator, entry)]

    async_add_entities(entities)


class ActiveStreamsSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the number of active audio streams."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:music-note"

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_active_streams"
        self._attr_name = "Active Streams"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information about this entity."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Linux Audio Server",
            "manufacturer": "Linux Audio Server",
            "model": "Audio Hub",
        }

    @property
    def native_value(self) -> int:
        """Return the number of active streams."""
        return len(self.coordinator.data.get("sink_inputs", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        streams = self.coordinator.data.get("sink_inputs", [])
        return {
            "streams": [
                {
                    "index": stream.get("index"),
                    "name": stream.get("name"),
                    "sink": stream.get("sink_description"),
                    "volume": stream.get("volume"),
                    "muted": stream.get("muted"),
                }
                for stream in streams
            ]
        }
