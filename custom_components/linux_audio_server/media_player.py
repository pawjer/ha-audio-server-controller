"""Media player platform for Linux Audio Server."""
from __future__ import annotations

import logging
from typing import Any

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
    coordinator: LinuxAudioServerCoordinator = hass.data[DOMAIN][entry.entry_id]
    entity_reg = er.async_get(hass)

    # Create media player entities for each sink
    entities = []
    for sink in coordinator.data.get("sinks", []):
        entities.append(AudioSinkMediaPlayer(coordinator, entry, sink))

    async_add_entities(entities)

    # Set up a listener to add new sinks dynamically and remove stale entities
    async def async_update_entities() -> None:
        """Update entities when coordinator data changes."""
        current_entities = {entity.unique_id for entity in entities}
        new_sinks = coordinator.data.get("sinks", [])

        # Get current Bluetooth devices
        bluetooth_devices = coordinator.data.get("bluetooth_devices", [])
        paired_addresses = {dev.get("address") for dev in bluetooth_devices if dev.get("paired", False)}

        # Add new sinks
        for sink in new_sinks:
            unique_id = f"{entry.entry_id}_{sink['name']}"
            if unique_id not in current_entities:
                new_entity = AudioSinkMediaPlayer(coordinator, entry, sink)
                entities.append(new_entity)
                async_add_entities([new_entity])

        # Remove stale Bluetooth speaker entities
        # An entity is stale if:
        # 1. It's a Bluetooth device (sink name starts with bluez_output.)
        # 2. The Bluetooth device is no longer paired
        # 3. The sink no longer exists
        current_sink_names = {sink["name"] for sink in new_sinks}

        entities_to_remove = []
        for entity in entities:
            # Check if this is a Bluetooth entity
            if not entity._sink_name.startswith("bluez_output."):
                continue

            # Extract Bluetooth address
            bt_address = entity._bluetooth_address
            if not bt_address:
                continue

            # Check if device is still paired
            is_paired = bt_address in paired_addresses
            sink_exists = entity._sink_name in current_sink_names

            # Remove entity if device is no longer paired AND sink doesn't exist
            if not is_paired and not sink_exists:
                _LOGGER.info(
                    "Removing stale Bluetooth speaker entity: %s (address: %s, paired: %s, sink exists: %s)",
                    entity._attr_name,
                    bt_address,
                    is_paired,
                    sink_exists,
                )
                entities_to_remove.append(entity)

                # Remove from entity registry
                entity_id = entity_reg.async_get_entity_id(
                    "media_player",
                    DOMAIN,
                    entity.unique_id,
                )
                if entity_id:
                    entity_reg.async_remove(entity_id)

        # Remove from our entities list
        for entity in entities_to_remove:
            entities.remove(entity)

    coordinator.async_add_listener(async_update_entities)


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

        For Bluetooth devices: Always available if paired (so power button works when disconnected)
        For other devices: Available only when sink exists
        """
        if not self.coordinator.last_update_success:
            return False

        # For Bluetooth devices, check if device is paired
        if self._is_bluetooth and self._bluetooth_address:
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
                        self._sink_data is not None,
                    )
                    if is_paired:
                        return True
                    # If found but not paired, entity should be unavailable
                    return False

            # If Bluetooth device not found in device list, check if sink exists
            # This handles the case where the device was just discovered
            _LOGGER.debug(
                "Bluetooth device %s (%s) not found in device list, checking sink: %s",
                self._attr_name,
                self._bluetooth_address,
                self._sink_data is not None,
            )
            return self._sink_data is not None

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
        """Get the player actually routing audio to this sink (ground truth from sink-inputs)."""
        sink_inputs = self.coordinator.data.get("sink_inputs", [])

        # Look for Mopidy sink-inputs routing to this sink
        for sink_input in sink_inputs:
            if sink_input.get("sink") == self._sink_name:
                app_name = sink_input.get("name", "")
                # Match "Mopidy Player 2@unix:/run/pulse/native" -> "player2"
                # Match "Mopidy Player 1 (TTS)@unix:/run/pulse/native" -> "player1"
                if "Mopidy Player" in app_name:
                    # Extract player number
                    if "Player 1" in app_name:
                        return "player1"
                    elif "Player 2" in app_name:
                        return "player2"
                    elif "Player 3" in app_name:
                        return "player3"
                    elif "Player 4" in app_name:
                        return "player4"
        return None

    def _get_assigned_player_track(self) -> dict[str, Any] | None:
        """Get current track info from the player assigned to this sink."""
        # First check which player is ACTUALLY routing audio to this sink (ground truth)
        active_player = self._get_active_player_for_sink()

        if active_player:
            # Get track from the active player
            players = self.coordinator.data.get("players", [])
            for player in players:
                if player.get("id") == active_player:
                    return player.get("current_track")

        # Fallback: check player assignments (might be stale but better than nothing)
        player_assignments = self.coordinator.data.get("player_assignments", {})
        assigned_player = player_assignments.get(self._sink_name)

        if assigned_player:
            # Get the assigned player's data
            players = self.coordinator.data.get("players", [])
            for player in players:
                if player.get("id") == assigned_player:
                    return player.get("current_track")

        # Fallback to global playback data (player1)
        playback = self.coordinator.data.get("playback", {})
        return playback.get("track")

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the device."""
        sink = self._sink_data
        if sink is None:
            return MediaPlayerState.OFF

        # For multi-player setups, check which player is ACTUALLY routing audio to this sink
        # This is the ground truth from sink-inputs, not just assignments which can be stale
        active_player = self._get_active_player_for_sink()

        if active_player:
            # Get the state of the active player
            players = self.coordinator.data.get("players", [])
            for player in players:
                if player.get("id") == active_player:
                    player_state = player.get("state")
                    if player_state == "playing":
                        return MediaPlayerState.PLAYING
                    elif player_state == "paused":
                        return MediaPlayerState.PAUSED
                    elif player_state == "stopped":
                        return MediaPlayerState.IDLE
                    break

        # Fallback: check player assignments (might be stale but better than nothing)
        player_assignments = self.coordinator.data.get("player_assignments", {})
        assigned_player = player_assignments.get(self._sink_name)

        if assigned_player:
            # Get the state of the assigned player
            players = self.coordinator.data.get("players", [])
            for player in players:
                if player.get("id") == assigned_player:
                    player_state = player.get("state")
                    if player_state == "playing":
                        return MediaPlayerState.PLAYING
                    elif player_state == "paused":
                        return MediaPlayerState.PAUSED
                    elif player_state == "stopped":
                        return MediaPlayerState.IDLE
                    break

        # Fallback to global playback state (player1)
        playback = self.coordinator.data.get("playback", {})
        playback_state = playback.get("state")

        if playback_state == "playing":
            return MediaPlayerState.PLAYING
        elif playback_state == "paused":
            return MediaPlayerState.PAUSED
        elif playback_state == "stopped":
            return MediaPlayerState.IDLE

        # Fallback to sink state if no playback info
        pa_state = sink.get("state", "IDLE")
        if pa_state == "RUNNING":
            return MediaPlayerState.ON
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
