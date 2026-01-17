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
        | MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.PLAY_MEDIA
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

        # Use playback state if available
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
        playback = self.coordinator.data.get("playback", {})
        if playback.get("track"):
            return "music"
        return None

    @property
    def media_title(self) -> str | None:
        """Return the title of current playing media."""
        playback = self.coordinator.data.get("playback", {})
        track = playback.get("track")
        if track:
            return track.get("name")
        return None

    @property
    def media_artist(self) -> str | None:
        """Return the artist of current playing media."""
        playback = self.coordinator.data.get("playback", {})
        track = playback.get("track")
        if track:
            return track.get("artist")
        return None

    @property
    def media_album_name(self) -> str | None:
        """Return the album name of current playing media."""
        playback = self.coordinator.data.get("playback", {})
        track = playback.get("track")
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
        """Send play command."""
        await self.coordinator.client.play()
        await self.coordinator.async_request_refresh()

    async def async_media_pause(self) -> None:
        """Send pause command."""
        await self.coordinator.client.pause()
        await self.coordinator.async_request_refresh()

    async def async_media_stop(self) -> None:
        """Send stop command."""
        await self.coordinator.client.stop()
        await self.coordinator.async_request_refresh()

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        await self.coordinator.client.next_track()
        await self.coordinator.async_request_refresh()

    async def async_media_previous_track(self) -> None:
        """Send previous track command."""
        await self.coordinator.client.previous_track()
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
            await self.coordinator.client.play_radio_url(media_id)
        elif media_id.startswith("spotify:"):
            # Spotify URI - use Mopidy's tracklist.add + playback.play
            _LOGGER.debug("Playing Spotify URI: %s", media_id)
            # For now, use play_radio_url which will forward to Mopidy
            # TODO: Could add dedicated Mopidy tracklist API methods
            await self.coordinator.client.play_radio_url(media_id)
        elif media_id.startswith("file://"):
            # Local file - use Mopidy
            _LOGGER.debug("Playing local file: %s", media_id)
            await self.coordinator.client.play_radio_url(media_id)
        else:
            # Assume it's a URI and try to play it
            _LOGGER.debug("Playing URI: %s", media_id)
            await self.coordinator.client.play_radio_url(media_id)

        await self.coordinator.async_request_refresh()
