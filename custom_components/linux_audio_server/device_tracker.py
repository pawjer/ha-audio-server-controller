"""Device tracker platform for Linux Audio Server."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import ScannerEntity
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
    """Set up Linux Audio Server device tracker entities."""
    coordinator: LinuxAudioServerCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create device tracker for each Bluetooth device
    entities = []
    for device in coordinator.data.get("bluetooth_devices", []):
        entities.append(BluetoothDeviceTracker(coordinator, entry, device))

    async_add_entities(entities)

    # Set up listener to add new devices dynamically
    async def async_update_entities() -> None:
        """Update entities when coordinator data changes."""
        current_entities = {entity.unique_id for entity in entities}
        new_devices = coordinator.data.get("bluetooth_devices", [])

        for device in new_devices:
            unique_id = f"{entry.entry_id}_bluetooth_{device['address'].replace(':', '_')}"
            if unique_id not in current_entities:
                new_entity = BluetoothDeviceTracker(coordinator, entry, device)
                entities.append(new_entity)
                async_add_entities([new_entity])

    coordinator.async_add_listener(async_update_entities)


class BluetoothDeviceTracker(CoordinatorEntity, ScannerEntity):
    """Bluetooth device tracker entity."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:bluetooth"

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
        device: dict[str, Any],
    ) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._entry = entry
        self._device_address = device["address"]
        safe_address = device["address"].replace(":", "_")
        self._attr_unique_id = f"{entry.entry_id}_bluetooth_{safe_address}"
        self._attr_name = device.get("name", device["address"])

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        device = self._device_data
        device_name = device.get("name", self._device_address) if device else self._device_address

        return {
            "identifiers": {(DOMAIN, f"bluetooth_{self._device_address}")},
            "name": device_name,
            "manufacturer": "Bluetooth Device",
            "model": "Audio Device",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self._device_data is not None

    @property
    def _device_data(self) -> dict[str, Any] | None:
        """Get current device data from coordinator."""
        for device in self.coordinator.data.get("bluetooth_devices", []):
            if device["address"] == self._device_address:
                return device
        return None

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.BLUETOOTH

    @property
    def is_connected(self) -> bool:
        """Return if device is connected."""
        device = self._device_data
        return device.get("connected", False) if device else False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device attributes."""
        device = self._device_data
        if not device:
            return {}

        return {
            "address": device.get("address"),
            "paired": device.get("paired", False),
            "trusted": device.get("trusted", False),
        }
