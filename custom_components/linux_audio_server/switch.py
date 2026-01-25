"""Switch platform for Linux Audio Server."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up Linux Audio Server switch entities."""
    coordinator: LinuxAudioServerCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create switch entities for setting default sink
    entities = []
    for sink in coordinator.data.get("sinks", []):
        entities.append(DefaultSinkSwitch(coordinator, entry, sink))

    async_add_entities(entities)

    # Set up a listener to add new sinks dynamically
    async def async_update_entities() -> None:
        """Update entities when coordinator data changes."""
        current_entities = {entity.unique_id for entity in entities}
        new_sinks = coordinator.data.get("sinks", [])

        for sink in new_sinks:
            unique_id = f"{entry.entry_id}_{sink['name']}_default_switch"
            if unique_id not in current_entities:
                new_entity = DefaultSinkSwitch(coordinator, entry, sink)
                entities.append(new_entity)
                async_add_entities([new_entity])

    coordinator.async_add_listener(async_update_entities)


class DefaultSinkSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to set a sink as the default."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
        sink: dict[str, Any],
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._entry = entry
        self._sink_name = sink["name"]
        self._attr_unique_id = f"{entry.entry_id}_{sink['name']}_default_switch"
        self._attr_name = f"{sink['description']} Default"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information about this entity."""
        # Find sink description for consistent device naming
        device_name = self._sink_name
        for sink in self.coordinator.data.get("sinks", []):
            if sink["name"] == self._sink_name:
                device_name = sink.get("description", self._sink_name)
                break

        return {
            "identifiers": {(DOMAIN, self._sink_name)},
            "name": device_name,
            "manufacturer": "Linux Audio Server",
            "model": "Audio Sink",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Check if sink still exists in coordinator data
        for sink in self.coordinator.data.get("sinks", []):
            if sink["name"] == self._sink_name:
                return self.coordinator.last_update_success
        return False

    @property
    def is_on(self) -> bool:
        """Return true if this sink is the default."""
        default_sink = self.coordinator.data.get("default_sink")
        return default_sink == self._sink_name

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Set this sink as the default."""
        await self.coordinator.client.set_default_sink(self._sink_name)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Cannot turn off default sink - do nothing."""
        # You can't have no default sink, so turning off doesn't make sense
        pass
