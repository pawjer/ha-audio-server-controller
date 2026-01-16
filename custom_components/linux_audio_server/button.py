"""Button platform for Linux Audio Server."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
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
    """Set up Linux Audio Server button entities."""
    coordinator: LinuxAudioServerCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create ONE Bluetooth scan button per integration
    async_add_entities([BluetoothScanButton(coordinator, entry)])


class BluetoothScanButton(CoordinatorEntity, ButtonEntity):
    """Button to trigger Bluetooth scan."""

    _attr_has_entity_name = True
    _attr_device_class = ButtonDeviceClass.IDENTIFY
    _attr_icon = "mdi:bluetooth-audio"

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_bluetooth_scan_button"
        self._attr_name = "Scan for Bluetooth Devices"

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
        return self.coordinator.last_update_success

    async def async_press(self) -> None:
        """Handle button press."""
        try:
            # Start scan with 10 second duration
            await self.coordinator.client.scan_bluetooth(duration=10)
            _LOGGER.info("Started Bluetooth scan for 10 seconds")
            # Wait for scan to complete
            await asyncio.sleep(2)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to start Bluetooth scan: %s", err)
