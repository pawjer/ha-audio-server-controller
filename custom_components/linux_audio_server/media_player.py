"""Media player platform for Linux Audio Server."""
from __future__ import annotations

import logging
import time
from typing import Any

from homeassistant.core import callback
from homeassistant.components.media_player import (
    BrowseMedia,
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaClass,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
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
    _LOGGER.info("[MEDIA_PLAYER_SETUP] async_setup_entry called!")
    coordinator: LinuxAudioServerCoordinator = hass.data[DOMAIN][entry.entry_id]
    entity_reg = er.async_get(hass)

    # Store async_add_entities callback for dynamic entity creation
    if "media_player_add_entities" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["media_player_add_entities"] = {}
    hass.data[DOMAIN]["media_player_add_entities"][entry.entry_id] = async_add_entities
    _LOGGER.info("[MEDIA_PLAYER_SETUP] Stored async_add_entities callback")

    # Get existing entities from registry (to restore disconnected speakers)
    existing_registry_entities = {
        entity.unique_id: entity
        for entity in entity_reg.entities.values()
        if entity.config_entry_id == entry.entry_id
        and entity.domain == "media_player"
    }
    _LOGGER.info(f"[MEDIA_PLAYER_SETUP] Found {len(existing_registry_entities)} entities in registry")

    # Create media player entities
    entities = []
    sink_names_created = set()
    current_sinks = coordinator.data.get("sinks", [])
    current_sink_map = {sink["name"]: sink for sink in current_sinks}

    # First, create entities for all existing sinks
    for sink in current_sinks:
        entities.append(AudioSinkMediaPlayer(coordinator, entry, sink))
        sink_names_created.add(sink["name"])
        _LOGGER.debug(f"[MEDIA_PLAYER_SETUP] Created entity for existing sink: {sink['name']}")

    # Second, restore entities from registry that don't have sinks (disconnected speakers)
    for unique_id, registry_entry in existing_registry_entities.items():
        # Extract sink name from unique_id (format: entry_id_sink_name)
        sink_name = unique_id.replace(f"{entry.entry_id}_", "")

        if sink_name not in sink_names_created:
            # This entity exists in registry but sink is gone - create placeholder
            _LOGGER.info(
                f"[MEDIA_PLAYER_SETUP] Restoring entity for disconnected sink: "
                f"{registry_entry.name or registry_entry.original_name} ({sink_name})"
            )

            # Create minimal sink dict for placeholder entity
            placeholder_sink = {
                "name": sink_name,
                "description": registry_entry.original_name or "Disconnected Device",
                "driver": "module-bluez5-device.c" if sink_name.startswith("bluez_") else "unknown",
            }
            entities.append(AudioSinkMediaPlayer(coordinator, entry, placeholder_sink))
            sink_names_created.add(sink_name)

    async_add_entities(entities)
    _LOGGER.info(f"[MEDIA_PLAYER_SETUP] Added {len(entities)} entities ({len(current_sinks)} with sinks, {len(entities) - len(current_sinks)} placeholders)")
    _LOGGER.info("[MEDIA_PLAYER_SETUP] Setup complete - dynamic entity creation handled by __init__.py")


class AudioSinkMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Representation of an audio sink as a media player."""

    _attr_has_entity_name = False
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER

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

        # Check if this is a Bluetooth sink
        self._is_bluetooth = self._sink_name.startswith("bluez_output.")
        self._bluetooth_address = self._extract_bluetooth_address() if self._is_bluetooth else None
        self._attr_volume_level: float = 0.5  # optimistic display value
        self._volume_set_at: float = 0.0

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("Coordinator update received for %s", self._sink_name)
        if time.monotonic() - self._volume_set_at > 3.0:
            assigned = self._get_active_player_for_sink()
            if assigned:
                for player in self.coordinator.data.get("players", []):
                    if player.get("id") == assigned and player.get("volume") is not None:
                        self._attr_volume_level = player["volume"] / 100
                        break
        super()._handle_coordinator_update()

    def _extract_bluetooth_address(self) -> str | None:
        """Extract Bluetooth MAC address from sink name.

        Converts: bluez_output.00_02_3C_71_8B_55.1 -> 00:02:3C:71:8B:55
        """
        try:
            # Format: bluez_output.XX_XX_XX_XX_XX_XX.Y
            parts = self._sink_name.split(".")
            if len(parts) >= 2:
                # Replace underscores with colons
                return parts[1].replace("_", ":")
        except Exception as err:
            _LOGGER.warning("Failed to extract Bluetooth address from %s: %s", self._sink_name, err)
        return None

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Return supported features."""
        features = (
            MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.SELECT_SOURCE
            | MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.STOP
            | MediaPlayerEntityFeature.NEXT_TRACK
            | MediaPlayerEntityFeature.PREVIOUS_TRACK
            | MediaPlayerEntityFeature.PLAY_MEDIA
            | MediaPlayerEntityFeature.BROWSE_MEDIA
        )

        # Add turn on/off for Bluetooth devices
        if self._is_bluetooth:
            features |= MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF

        return features

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
        """Return if entity is available.

        For Bluetooth devices: Available if paired OR if sink exists (connected)
        For other devices: Available only when sink exists
        """
        if not self.coordinator.last_update_success:
            return False

        # For Bluetooth devices, check if device is paired or sink exists
        if self._is_bluetooth and self._bluetooth_address:
            sink_exists = self._sink_data is not None

            # Check if this Bluetooth device exists in device tracker data
            bluetooth_devices = self.coordinator.data.get("bluetooth_devices", [])
            for device in bluetooth_devices:
                if device.get("address") == self._bluetooth_address:
                    # Device is paired - keep entity available even if disconnected
                    is_paired = device.get("paired", False)
                    _LOGGER.debug(
                        "Bluetooth device %s (%s) found: paired=%s, sink_exists=%s",
                        self._attr_name,
                        self._bluetooth_address,
                        is_paired,
                        sink_exists,
                    )
                    # Available if paired OR if sink exists (handles race condition)
                    if is_paired or sink_exists:
                        return True
                    # If found but not paired AND no sink, entity should be unavailable
                    return False

            # If Bluetooth device not found in device list, check if sink exists
            # This handles the case where the device was just discovered or paired
            _LOGGER.debug(
                "Bluetooth device %s (%s) not found in device list, checking sink: %s",
                self._attr_name,
                self._bluetooth_address,
                sink_exists,
            )
            return sink_exists

        # For non-Bluetooth devices, only available when sink exists
        return self._sink_data is not None

    @property
    def _sink_data(self) -> dict[str, Any] | None:
        """Get the current sink data from coordinator."""
        for sink in self.coordinator.data.get("sinks", []):
            if sink["name"] == self._sink_name:
                return sink
        return None

    def _get_active_player_for_sink(self) -> str | None:
        """Return the player assigned to this sink.

        Assignments are the source of truth — each media player entity reflects
        exactly its assigned player, regardless of what other streams (e.g. TTS)
        may be routed to the same hardware sink.
        """
        player = self.coordinator.data.get("player_assignments", {}).get(self._sink_name)
        _LOGGER.debug("[%s] Assigned player: %s", self._sink_name, player)
        return player

    def _get_assigned_player_track(self) -> dict[str, Any] | None:
        """Get current track info from the player assigned to this sink."""
        assigned_player = self._get_active_player_for_sink()
        if not assigned_player:
            return None
        for player in self.coordinator.data.get("players", []):
            if player.get("id") == assigned_player:
                track = player.get("current_track")
                _LOGGER.debug("[%s] Track from assigned player '%s': %s", self._sink_name, assigned_player, track)
                return track
        _LOGGER.debug("[%s] Assigned player '%s' not found in players array", self._sink_name, assigned_player)
        return None

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the device."""
        sink = self._sink_data
        if sink is None:
            return MediaPlayerState.OFF

        assigned_player = self._get_active_player_for_sink()

        if assigned_player:
            for player in self.coordinator.data.get("players", []):
                if player.get("id") == assigned_player:
                    player_state = player.get("state")
                    _LOGGER.debug("[%s] Assigned player '%s' state: %s", self._sink_name, assigned_player, player_state)
                    if player_state == "playing":
                        return MediaPlayerState.PLAYING
                    elif player_state == "paused":
                        return MediaPlayerState.PAUSED
                    else:
                        # stopped, unknown, or anything unrecognised → idle
                        return MediaPlayerState.IDLE
            # Assigned player not in players array (API hiccup) → idle
            _LOGGER.debug("[%s] Assigned player '%s' not in players array", self._sink_name, assigned_player)
            return MediaPlayerState.IDLE

        # No assignment — fall back to raw PA sink state
        pa_state = sink.get("state", "IDLE").upper()
        _LOGGER.debug("[%s] No assignment, PA sink state: %s", self._sink_name, pa_state)
        if pa_state == "RUNNING":
            return MediaPlayerState.ON
        elif pa_state in ("IDLE", "SUSPENDED"):
            return MediaPlayerState.IDLE
        return MediaPlayerState.OFF

    def _get_mopidy_stream_for_sink(self) -> dict[str, Any] | None:
        """Find the sink-input for the assigned player on this sink."""
        active_player = self._get_active_player_for_sink()
        if active_player is None:
            return None
        player_num = active_player.replace("player", "")
        for si in self.coordinator.data.get("sink_inputs", []):
            if si.get("sink") != self._sink_name:
                continue
            name = si.get("name", "")
            if f"mopidy-player{player_num}" in name or f"Player {player_num}" in name:
                return si
        return None

    @property
    def volume_level(self) -> float:
        """Optimistic volume level — updated from server on coordinator refresh."""
        return self._attr_volume_level

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
    def media_content_type(self) -> str | None:
        """Return the content type of current playing media."""
        track = self._get_assigned_player_track()
        if track:
            return "music"
        return None

    @property
    def media_title(self) -> str | None:
        """Return the title of current playing media."""
        track = self._get_assigned_player_track()
        if track:
            return track.get("name")
        return None

    @property
    def media_artist(self) -> str | None:
        """Return the artist of current playing media."""
        track = self._get_assigned_player_track()
        if track:
            return track.get("artist")
        return None

    @property
    def media_album_name(self) -> str | None:
        """Return the album name of current playing media."""
        track = self._get_assigned_player_track()
        if track:
            return track.get("album")
        return None

    @property
    def media_position(self) -> int | None:
        """Return the position of current playing media in seconds."""
        playback = self.coordinator.data.get("playback", {})
        time_position = playback.get("time_position")
        if time_position is not None:
            return time_position // 1000  # Convert ms to seconds
        return None

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
        """Set Mopidy mixer volume for the assigned player."""
        self._attr_volume_level = volume
        self._volume_set_at = time.monotonic()
        self.async_write_ha_state()
        assigned = self._get_active_player_for_sink()
        if assigned:
            await self.coordinator.client.set_player_volume(assigned, round(volume * 100))
        else:
            _LOGGER.debug("No assigned player for %s — volume not sent", self._sink_name)

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute the media player."""
        await self.coordinator.client.set_sink_mute(self._sink_name, mute)
        self._attr_is_volume_muted = mute
        self.async_write_ha_state()

    async def async_select_source(self, source: str) -> None:
        """Select input source (set as default sink)."""
        # Find the sink name from description
        for sink in self.coordinator.data.get("sinks", []):
            if sink["description"] == source:
                await self.coordinator.client.set_default_sink(sink["name"])
                await self.coordinator.async_request_refresh()
                return

        _LOGGER.warning("Source '%s' not found in available sinks", source)

    async def async_media_play(self) -> None:
        """Send play command to this sink's assigned player."""
        try:
            # Use sink-based playback control (routes to correct player automatically)
            await self.coordinator.client.play_sink(self._sink_name)
            _LOGGER.debug("Play command sent to sink %s", self._sink_name)
        except Exception as err:
            # If no player is assigned (404), this is expected - user needs to play media first
            _LOGGER.debug("Play command failed for sink %s: %s", self._sink_name, err)
            # Silently ignore - playback control requires active media
        await self.coordinator.async_request_refresh()

    async def async_media_pause(self) -> None:
        """Send pause command to this sink's assigned player."""
        try:
            # Use sink-based playback control (routes to correct player automatically)
            await self.coordinator.client.pause_sink(self._sink_name)
            _LOGGER.debug("Pause command sent to sink %s", self._sink_name)
        except Exception as err:
            # If no player is assigned (404), this is expected
            _LOGGER.debug("Pause command failed for sink %s: %s", self._sink_name, err)
        await self.coordinator.async_request_refresh()

    async def async_media_stop(self) -> None:
        """Send stop command to this sink's assigned player."""
        try:
            # Use sink-based playback control (routes to correct player automatically)
            await self.coordinator.client.stop_sink(self._sink_name)
            _LOGGER.debug("Stop command sent to sink %s", self._sink_name)
        except Exception as err:
            # If no player is assigned (404), this is expected
            _LOGGER.debug("Stop command failed for sink %s: %s", self._sink_name, err)
        await self.coordinator.async_request_refresh()

    async def async_media_next_track(self) -> None:
        """Send next track command to this sink's assigned player."""
        try:
            # Use sink-based playback control (routes to correct player automatically)
            await self.coordinator.client.next_track_sink(self._sink_name)
            _LOGGER.debug("Next track command sent to sink %s", self._sink_name)
        except Exception as err:
            # If no player is assigned (404), this is expected
            _LOGGER.debug("Next track command failed for sink %s: %s", self._sink_name, err)
        await self.coordinator.async_request_refresh()

    async def async_media_previous_track(self) -> None:
        """Send previous track command to this sink's assigned player."""
        try:
            # Use sink-based playback control (routes to correct player automatically)
            await self.coordinator.client.previous_track_sink(self._sink_name)
            _LOGGER.debug("Previous track command sent to sink %s", self._sink_name)
        except Exception as err:
            # If no player is assigned (404), this is expected
            _LOGGER.debug("Previous track command failed for sink %s: %s", self._sink_name, err)
        await self.coordinator.async_request_refresh()

    async def async_play_media(self, media_type: str, media_id: str, **kwargs) -> None:
        """Play media from URL or URI.

        Supports:
        - Direct URLs (http://, https://) - plays via radio URL endpoint
        - Spotify URIs (spotify:track:...) - plays via Mopidy
        - File URIs (file://...) - plays via Mopidy
        """
        _LOGGER.info("Playing media: type=%s, id=%s", media_type, media_id)

        # Set this sink as default before playing
        await self.coordinator.client.set_default_sink(self._sink_name)

        # Handle different media types
        if media_id.startswith(("http://", "https://")):
            # Direct URL - use radio URL endpoint
            _LOGGER.debug("Playing HTTP(S) URL via radio endpoint: %s", media_id)
            await self.coordinator.client.play_radio_url(media_id, sink=self._sink_name)
        elif media_id.startswith("spotify:"):
            # Spotify URI - use Mopidy's tracklist.add + playback.play
            _LOGGER.debug("Playing Spotify URI: %s", media_id)
            # For now, use play_radio_url which will forward to Mopidy
            # TODO: Could add dedicated Mopidy tracklist API methods
            await self.coordinator.client.play_radio_url(media_id, sink=self._sink_name)
        elif media_id.startswith("file://"):
            # Local file - use Mopidy
            _LOGGER.debug("Playing local file: %s", media_id)
            await self.coordinator.client.play_radio_url(media_id, sink=self._sink_name)
        else:
            # Assume it's a URI and try to play it
            _LOGGER.debug("Playing URI: %s", media_id)
            await self.coordinator.client.play_radio_url(media_id, sink=self._sink_name)

        await self.coordinator.async_request_refresh()

    async def async_browse_media(
        self, media_content_type: str | None = None, media_content_id: str | None = None
    ) -> BrowseMedia:
        """Implement the browse_media media player platform method.

        This provides basic media browsing support showing radio stations.
        """
        if media_content_id is None:
            # Root level - show radio stations
            radio_streams = self.coordinator.data.get("radio_streams", {})

            children = [
                BrowseMedia(
                    title=name,
                    media_class=MediaClass.MUSIC,
                    media_content_type=MediaType.MUSIC,
                    media_content_id=url,
                    can_play=True,
                    can_expand=False,
                )
                for name, url in radio_streams.items()
            ]

            return BrowseMedia(
                title="Radio Stations",
                media_class=MediaClass.DIRECTORY,
                media_content_type="library",
                media_content_id="root",
                can_play=False,
                can_expand=True,
                children=children,
            )

        # If a specific ID is requested, we don't have subcategories
        return None

    async def async_turn_on(self) -> None:
        """Turn on the media player (connect Bluetooth device)."""
        if not self._is_bluetooth or not self._bluetooth_address:
            _LOGGER.warning("Turn on is only supported for Bluetooth devices")
            return

        _LOGGER.info("Turning on Bluetooth device: %s (%s)", self._attr_name, self._bluetooth_address)
        try:
            # Just connect - use switch/source selector to set as default
            await self.coordinator.client.connect_bluetooth(self._bluetooth_address)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on %s: %s", self._attr_name, err)
            raise

    async def async_turn_off(self) -> None:
        """Turn off the media player (disconnect Bluetooth device)."""
        if not self._is_bluetooth or not self._bluetooth_address:
            _LOGGER.warning("Turn off is only supported for Bluetooth devices")
            return

        _LOGGER.info("Turning off Bluetooth device: %s (%s)", self._attr_name, self._bluetooth_address)
        try:
            # Disconnect Bluetooth device
            await self.coordinator.client.disconnect_bluetooth(self._bluetooth_address)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off %s: %s", self._attr_name, err)
            raise
