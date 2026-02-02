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

    entities = []

    # Create ONE global radio station selector
    entities.append(RadioStationSelect(coordinator, entry))

    # Create per-sink radio station selectors
    for sink in coordinator.data.get("sinks", []):
        entities.append(SinkRadioStationSelect(coordinator, entry, sink))

    # Create source routing selectors (Airplay, TTS, Spotify)
    entities.append(AirplaySinkSelect(coordinator, entry))
    entities.append(TTSSinkSelect(coordinator, entry))
    entities.append(SpotifySinkSelect(coordinator, entry))

    async_add_entities(entities)

    # Set up a listener to add selectors for new sinks dynamically
    async def async_update_entities() -> None:
        """Update entities when coordinator data changes."""
        current_entities = {entity.unique_id for entity in entities}
        new_sinks = coordinator.data.get("sinks", [])

        for sink in new_sinks:
            unique_id = f"{entry.entry_id}_{sink['name']}_radio_selector"
            if unique_id not in current_entities:
                new_entity = SinkRadioStationSelect(coordinator, entry, sink)
                entities.append(new_entity)
                async_add_entities([new_entity])

    coordinator.async_add_listener(async_update_entities)


class RadioStationSelect(CoordinatorEntity, SelectEntity):
    """Select entity for choosing radio stations."""

    _attr_has_entity_name = False
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
        if not streams_dict:
            return []
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
        """Play the selected radio station on the default sink."""
        try:
            # Get the current default sink from coordinator data
            default_sink = self.coordinator.data.get("default_sink")

            # Play on default sink to avoid ambiguity
            await self.coordinator.client.play_radio_stream(option, sink=default_sink)
            await self.coordinator.async_request_refresh()

            if default_sink:
                _LOGGER.info("Playing radio station '%s' on default sink '%s'", option, default_sink)
            else:
                _LOGGER.info("Playing radio station: %s", option)
        except Exception as err:
            _LOGGER.error("Failed to play radio station %s: %s", option, err)


class SinkRadioStationSelect(CoordinatorEntity, SelectEntity):
    """Per-sink radio station selector."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:radio"

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
        sink: dict[str, Any],
    ) -> None:
        """Initialize the per-sink select entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._sink_name = sink["name"]
        self._attr_unique_id = f"{entry.entry_id}_{sink['name']}_radio_selector"
        self._attr_name = f"{sink['description']} Radio"

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
    def _sink_data(self) -> dict[str, Any] | None:
        """Get current sink data from coordinator."""
        for sink in self.coordinator.data.get("sinks", []):
            if sink["name"] == self._sink_name:
                return sink
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Check if sink still exists in coordinator data
        return self.coordinator.last_update_success and self._sink_data is not None

    @property
    def options(self) -> list[str]:
        """Return list of radio station names plus Off option."""
        streams_dict = self.coordinator.data.get("radio_streams", {})
        if not streams_dict:
            return ["Off"]
        # Add "Off" option at the beginning
        return ["Off"] + list(streams_dict.keys())

    @property
    def current_option(self) -> str | None:
        """Return currently playing station on this sink if any."""
        # Check which player is assigned to this sink
        player_assignments = self.coordinator.data.get("player_assignments", {})
        assigned_player = None

        for player_id, sink_name in player_assignments.items():
            if sink_name == self._sink_name:
                assigned_player = player_id
                break

        if not assigned_player:
            return "Off"

        # Get playback status for this player
        players_data = self.coordinator.data.get("players", {})
        player_data = players_data.get(assigned_player, {})

        if player_data.get("state") not in ["playing", "paused"]:
            return "Off"

        # Check if current track title matches a radio station name
        track = player_data.get("current_track", {})
        title = track.get("name")

        if title and title in self.options:
            return title

        # If playing but not a recognized station, show first non-Off option or Off
        return "Off"

    async def async_select_option(self, option: str) -> None:
        """Play the selected radio station on this sink."""
        try:
            if option == "Off":
                # Stop playback on this sink
                _LOGGER.info("Stopping playback on sink: %s", self._sink_name)
                await self.coordinator.client.stop_sink(self._sink_name)
            else:
                # Play the selected radio station on this sink
                _LOGGER.info("Playing radio station %s on sink: %s", option, self._sink_name)
                await self.coordinator.client.play_radio_stream(option, sink=self._sink_name)

            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error(
                "Failed to play radio station %s on sink %s: %s",
                option,
                self._sink_name,
                err,
            )


class SourceSinkRouterSelect(CoordinatorEntity, SelectEntity):
    """Base class for routing audio sources to sinks."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:speaker-wireless"

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
        source_name: str,
        source_identifier: str,
    ) -> None:
        """Initialize the source router select entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._source_name = source_name
        self._source_identifier = source_identifier
        self._attr_unique_id = f"{entry.entry_id}_{source_name.lower().replace(' ', '_')}_sink_router"
        self._attr_name = f"{source_name} Output"

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
    def options(self) -> list[str]:
        """Return list of available sink descriptions."""
        sinks = self.coordinator.data.get("sinks", [])
        return [sink.get("description", sink["name"]) for sink in sinks]

    @property
    def current_option(self) -> str | None:
        """Return currently selected sink description."""
        sink_input = self._find_sink_input()
        if not sink_input:
            return None

        return sink_input.get("sink_description")

    async def async_select_option(self, option: str) -> None:
        """Route source to the selected sink."""
        try:
            # Find the sink-input
            sink_input = self._find_sink_input()
            if not sink_input:
                _LOGGER.warning("Cannot route %s: source not active", self._source_name)
                return

            # Find the sink by description
            sinks = self.coordinator.data.get("sinks", [])
            target_sink = None
            for sink in sinks:
                if sink.get("description", sink["name"]) == option:
                    target_sink = sink["name"]
                    break

            if not target_sink:
                _LOGGER.error("Cannot find sink with description: %s", option)
                return

            # Move the stream
            _LOGGER.info("Moving %s to sink: %s", self._source_name, target_sink)
            await self.coordinator.client.move_stream(
                sink_input["index"],
                target_sink
            )
            await self.coordinator.async_request_refresh()

        except Exception as err:
            _LOGGER.error(
                "Failed to route %s to sink %s: %s",
                self._source_name,
                option,
                err,
            )


class AirplaySinkSelect(SourceSinkRouterSelect):
    """Select entity for routing Airplay to different sinks."""

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize Airplay sink router."""
        super().__init__(coordinator, entry, "Airplay", "Shairport Sync")
        self._attr_icon = "mdi:cast-audio"


class TTSSinkSelect(SourceSinkRouterSelect):
    """Select entity for routing TTS to different sinks."""

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize TTS sink router."""
        super().__init__(coordinator, entry, "TTS", "Mopidy Player 1 (TTS)")
        self._attr_icon = "mdi:text-to-speech"


class SpotifySinkSelect(SourceSinkRouterSelect):
    """Select entity for routing Spotify to different sinks."""

    def __init__(
        self,
        coordinator: LinuxAudioServerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize Spotify sink router."""
        super().__init__(coordinator, entry, "Spotify", "librespot")
        self._attr_icon = "mdi:spotify"
