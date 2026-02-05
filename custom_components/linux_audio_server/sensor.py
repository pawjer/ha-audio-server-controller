"""Sensor platform for Linux Audio Server."""
from __future__ import annotations

from datetime import datetime
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

    # Create sensors
    entities = [
        ActiveStreamsSensor(coordinator, entry),
        BluetoothKeepAliveSensor(coordinator, entry),
        MopidyPlayersSensor(coordinator, entry),
        PlayedTracksHistorySensor(coordinator, entry),
    ]

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
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

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


class BluetoothKeepAliveSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing Bluetooth keep-alive status."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:bluetooth-connect"

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_bluetooth_keep_alive"
        self._attr_name = "Bluetooth Keep-Alive"

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
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> str:
        """Return the keep-alive status."""
        keep_alive = self.coordinator.data.get("keep_alive", {})
        return "on" if keep_alive.get("enabled", False) else "off"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        keep_alive = self.coordinator.data.get("keep_alive", {})
        return {
            "interval": keep_alive.get("interval", 240),
            "enabled_sinks": keep_alive.get("enabled_sinks", []),
        }


class MopidyPlayersSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing Mopidy player instances and assignments."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:audio-video"

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_mopidy_players"
        self._attr_name = "Mopidy Players"

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
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> int:
        """Return the number of active players."""
        players = self.coordinator.data.get("players", [])
        return len([p for p in players if p.get("active", False)])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        players = self.coordinator.data.get("players", [])
        assignments = self.coordinator.data.get("player_assignments", {})
        return {
            "players": [
                {
                    "name": player.get("name"),
                    "active": player.get("active", False),
                    "status": player.get("status"),
                }
                for player in players
            ],
            "assignments": assignments,
        }


class PlayedTracksHistorySensor(CoordinatorEntity, SensorEntity):
    """Sensor tracking recently played tracks history."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:playlist-music"

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_played_tracks_history"
        self._attr_name = "Played Tracks History"
        self._history: list[dict[str, Any]] = []
        self._last_track_uri: str | None = None
        self._max_history = 50  # Keep last 50 tracks

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
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> str:
        """Return the most recently played track."""
        if self._history:
            recent = self._history[0]
            artist = recent.get("artist", "Unknown Artist")
            title = recent.get("title", "Unknown Title")
            return f"{artist} - {title}"
        return "No tracks played"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return track history as attributes."""
        return {
            "history": self._history[:20],  # Show last 20 in attributes
            "total_tracks": len(self._history),
            "last_updated": self._history[0]["timestamp"] if self._history else None,
        }

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Get current track from playback data
        playback = self.coordinator.data.get("playback", {})
        track = playback.get("track")

        if not track:
            # No track playing, check all players
            players = self.coordinator.data.get("players", [])
            for player in players:
                player_track = player.get("current_track")
                if player_track:
                    track = player_track
                    break

        if track:
            # Create a unique identifier for the track
            track_uri = track.get("uri", "")
            track_name = track.get("name", "")
            track_artist = track.get("artist", "")

            # Use URI or fallback to name+artist combination
            track_id = track_uri or f"{track_artist}|{track_name}"

            # Only add to history if it's a different track
            if track_id and track_id != self._last_track_uri:
                _LOGGER.debug(
                    "New track detected for history: %s - %s",
                    track_artist,
                    track_name
                )

                # Add to history
                self._history.insert(0, {
                    "title": track_name,
                    "artist": track_artist,
                    "album": track.get("album", ""),
                    "uri": track_uri,
                    "timestamp": datetime.now().isoformat(),
                    "duration": track.get("length"),  # Duration in ms
                })

                # Trim history to max size
                self._history = self._history[:self._max_history]

                # Update last track
                self._last_track_uri = track_id

        # Call parent to trigger entity update
        super()._handle_coordinator_update()
