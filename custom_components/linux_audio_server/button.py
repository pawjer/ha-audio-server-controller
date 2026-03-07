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

    entities: list = [BluetoothScanButton(coordinator, entry)]

    # Create an auto-sync button for each combined sink
    known_combined: set[str] = set()
    for sink in coordinator.data.get("combined_sinks", []):
        name = sink["name"]
        known_combined.add(name)
        entities.append(AutoSyncButton(coordinator, entry, sink))

    async_add_entities(entities)

    # Add buttons for new combined sinks as they appear
    async def _async_update_combined_entities() -> None:
        for sink in coordinator.data.get("combined_sinks", []):
            if sink["name"] not in known_combined:
                known_combined.add(sink["name"])
                async_add_entities([AutoSyncButton(coordinator, entry, sink)])

    coordinator.async_add_listener(_async_update_combined_entities)


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


class AutoSyncButton(CoordinatorEntity, ButtonEntity):
    """Button to auto-sync BT speaker latency in a combined sink.

    Measures each slave's codec latency via pactl while audio is playing
    and applies equalizing latencyOffsetNsec offsets so both speakers
    deliver audio at the same wall-clock time.
    Audio must be actively playing through the combined sink when pressed.
    """

    _attr_has_entity_name = False
    _attr_icon = "mdi:sync"

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
        sink: dict[str, Any],
    ) -> None:
        """Initialize the auto-sync button."""
        super().__init__(coordinator)
        self._entry = entry
        self._combined_name = sink["name"]
        self._attr_unique_id = f"{entry.entry_id}_{sink['name']}_auto_sync"
        self._attr_name = f"{sink.get('description', sink['name'])} Auto Sync"

    @property
    def device_info(self) -> dict[str, Any]:
        """Attach to the Linux Audio Server hub device."""
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
        """Measure slave latencies and apply equalizing offsets."""
        try:
            result = await self.coordinator.client.auto_sync_combined_sink(self._combined_name)
            _LOGGER.info("Auto-sync '%s': %s", self._combined_name, result)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Auto-sync failed for '%s': %s", self._combined_name, err)
