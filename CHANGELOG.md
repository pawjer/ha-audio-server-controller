# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.9] - 2026-01-25

### Added
- **Source routing selectors** - Route Airplay, Spotify, and TTS to any sink
  - `select.airplay_output` - Choose where Airplay audio plays
  - `select.spotify_output` - Choose where Spotify audio plays
  - `select.tts_output` - Choose where TTS audio plays
- **Source volume controls** - Individual volume control for each audio source
  - `number.airplay_volume` - Airplay volume slider (0-100%)
  - `number.spotify_volume` - Spotify volume slider (0-100%)
  - `number.tts_volume` - TTS volume slider (0-100%)
- Number platform for volume slider entities
- Smart availability - Source controls only visible when actively streaming

### Changed
- Increased Bluetooth operation timeout from 10s to 30s
- Dashboard Bluetooth buttons now use `bluetooth_connect` instead of `bluetooth_connect_and_set_default`
- More consistent with media player turn_on behavior (doesn't force default sink change)

### Fixed
- Bluetooth connection timeout errors for slow-to-connect devices
- Combined sinks now work correctly (already included in regular sinks list from backend)

### Technical
- Added `SourceSinkRouterSelect` base class for routing audio sources
- Added `SourceVolumeNumber` base class for source volume control
- Source identifiers: Airplay = "Shairport Sync", TTS = "Mopidy Player 1 (TTS)", Spotify = "librespot"
- Uses `move_stream` API for routing, `set_stream_volume` API for volume control
- All source entities attached to integration device (not sink-specific)

## [0.6.8] - 2026-01-25

### Added
- **Per-sink radio station selectors** - Automatic dropdown selector for each audio sink
- Each sink now gets its own `select.<sink_name>_radio` entity
- Radio stations automatically populated from backend (no manual configuration needed!)
- "Off" option in dropdowns to stop playback
- Selecting a station plays it immediately on that specific sink
- New minimalist dashboard with per-sink radio control
- `SinkRadioStationSelect` class for per-sink radio selection

### Changed
- Select platform now creates per-sink radio selectors in addition to global selector
- Dashboard examples updated to showcase new per-sink radio control
- Documentation updated with zero-configuration setup instructions

### Technical
- Auto-discovery of radio stations from backend for each sink selector
- Dynamic entity creation for new sinks
- Proper device info attachment for sink-based entities
- Current station detection based on player assignments
- Uses `stop_sink()` API method for stopping specific sink playback

## [0.6.7] - 2026-01-25

### Fixed
- **Entity IDs no longer have duplicate names** - Entity IDs like `john_paulacton_ii_john_paulacton_ii` are now correctly named as `john_paulacton_ii`
- Fixed `_attr_has_entity_name` setting in media_player and switch platforms that was causing device name to be combined with entity name

### Changed
- Media player entities now use entity name directly instead of combining device + entity name
- Switch entities (default sink switches) now use entity name directly

### Migration
- After updating, users should reload the integration in Home Assistant
- Delete old duplicate entities in Settings → Devices & Services → Entities
- New correctly-named entities will be created automatically

## [0.6.6] - 2026-01-23

### Fixed
- **State now based on actual audio routing, not stale assignments** - Fixes "idle" state when audio is actually playing
- State and media info now use sink-inputs to determine which player is ACTUALLY routing audio to each sink
- Handles cases where player assignments are out of sync with reality

### Added
- `_get_active_player_for_sink()` method to check which player is routing audio via sink-inputs (ground truth)
- Sink-inputs checking in state property before falling back to assignments
- Sink-inputs checking in `_get_assigned_player_track()` for accurate media information

### Changed
- State property now prioritizes actual audio routing over recorded assignments
- Multi-player state detection is now robust against stale assignment data
- Falls back to assignments only when sink-inputs don't show active routing

### Technical
- v0.6.5 attempted to fix by passing sink parameter, but assignments can become stale
- v0.6.6 solves the root cause by checking PulseAudio sink-inputs for ground truth
- Sink-inputs show which Mopidy player is actually sending audio to which sink

## [0.6.5] - 2026-01-23

### Fixed
- **Player assignments now recorded correctly when playing media** - Backend can now track which player is assigned to which sink, completing the multi-player state fix from v0.6.4
- Media player state now updates correctly after starting playback on Bluetooth speakers

### Changed
- `play_radio_stream()` and `play_radio_url()` API methods now accept optional `sink` parameter
- Media player entities now pass their sink name when playing media, enabling backend to record player assignments
- Coordinator refetches assignments every 5 seconds, ensuring dynamic state updates

### Technical
- Completes the multi-player state tracking: v0.6.4 fixed reading assignments, v0.6.5 fixes recording them
- No backend changes required - uses existing assignment API
- Backwards compatible: sink parameter is optional

## [0.6.4] - 2026-01-23

### Fixed
- **Media player state now shows correct status in multi-player setups** - State showed "idle" when Bluetooth speaker was actually playing on player2-4
- **Media information now displays correct track details** - Title, artist, and album now pulled from assigned player instead of always showing player1's data
- State and media info now match the actual player assigned to each sink

### Added
- `_get_assigned_player_track()` helper method to centralize track data fetching
- Player assignment checking in state property
- Automatic fallback chain: assigned player → player1 → PulseAudio sink state

### Changed
- `state` property now checks player assignments before falling back to global playback state
- `media_content_type`, `media_title`, `media_artist`, `media_album_name` now use assigned player's current track
- Maintains full backwards compatibility with single-player setups

### Technical
- Complements v0.6.3 playback control fixes - now both controls AND status work correctly
- No additional API calls - uses existing coordinator data
- Minimal performance impact (dict lookups only)

## [0.6.3] - 2026-01-23

### Fixed
- **Play/pause/stop buttons now work correctly in multi-player setups** - Buttons previously only controlled player1 regardless of which player was assigned to the Bluetooth speaker/sink
- Media controls (play, pause, stop, next, previous) now automatically route to the correct player based on sink assignments
- Integration starts gracefully even when Bluetooth service is initializing

### Added
- Sink-based playback API methods for precise control
- Debug logging for playback commands showing which sink received the command
- Graceful error handling for playback commands when no player is assigned
- Support for backend's new `available` field in Bluetooth devices API

### Changed
- Media player playback controls now use sink-based endpoints instead of global player1 endpoints
- 404 errors from unassigned sinks are logged at DEBUG level instead of ERROR (expected behavior)
- Improved coordinator handling of Bluetooth service availability during startup

### Technical
- Requires linux-audio-server with sink-based playback endpoints (commit 5b22004 or later)
- API client properly encodes sink names in URLs to handle special characters
- All playback methods maintain backward compatibility

## [0.6.2] - 2026-01-18

### Added
- **Multi-player management support** - 100% API coverage achieved (51/51 endpoints)!
- `assign_player` service for assigning specific Mopidy players to sinks
- Mopidy players sensor showing active player instances and sink assignments
- Support for independent content per room using player1-4

### Technical
- Complete coverage of linux-audio-server API
- Multi-player endpoints integrated for advanced multi-room setups

## [0.6.1] - 2026-01-18

### Added
- **Batch operations**: `pause_all` and `stop_all` services for controlling all Mopidy players at once
- **Bluetooth scan service** exposed for triggering device discovery
- Bluetooth scan button entity

### Fixed
- Bluetooth speaker availability when disconnected - entities remain available for power control

## [0.6.0] - 2026-01-18

### Added
- **"Follow Me" feature** - `move_all_streams` service to move audio between rooms
- **TTS speaker configuration** - Set default speaker for text-to-speech
- Per-call TTS speaker override via `sinks` parameter
- `get_tts_settings` and `set_tts_settings` services

### Technical
- 98% API coverage (50/51 endpoints)

## [0.5.4] - 2026-01-17

### Fixed
- Stereo pair deletion now works correctly

### Added
- `update_radio_stream` service to modify existing radio station URLs

## [0.5.3] - 2026-01-17

### Added
- Stream mute/unmute service for per-application audio control
- `set_stream_mute` service with stream index parameter

## [0.5.2] - 2026-01-17

### Added
- **Automatic cleanup of stale Bluetooth speaker entities**
- `cleanup_stale_bluetooth` service for manual cleanup
- Entities are removed when Bluetooth device is unpaired and sink no longer exists

### Changed
- Bluetooth speaker entities are kept available even when disconnected (for power button functionality)

## [0.5.1] - 2026-01-17

### Fixed
- Bluetooth speaker entities remain available when disconnected (not unpaired)
- Power button (turn_on/turn_off) works even when speaker is disconnected

### Changed
- Entity availability logic improved for Bluetooth devices

## [0.5.0] - 2026-01-17

### Added
- **Turn on/off support for Bluetooth speakers** - Power button controls connect/disconnect
- `async_turn_on` and `async_turn_off` methods for Bluetooth media players
- TURN_ON and TURN_OFF features added to Bluetooth speaker entities

## [0.4.x] - 2026-01-16

### Added
- **BROWSE_MEDIA feature** for media dashboard integration
- **PLAY_MEDIA feature** - Media players appear as audio output targets
- Cast media to specific sinks from Home Assistant media screen
- Browse and play radio stations from media player interface

## [0.3.0] - 2026-01-15

### Added
- **Internet radio management** - Add, delete, play radio stations
- **Bluetooth device management** - Scan, pair, connect, disconnect
- Radio station selector (select entity)
- Device tracker entities for Bluetooth devices
- Bluetooth keep-alive functionality to prevent auto-disconnect
- Services: `add_radio_stream`, `delete_radio_stream`, `play_radio_stream`, `play_radio_url`
- Services: `bluetooth_pair`, `bluetooth_connect`, `bluetooth_disconnect`, `bluetooth_scan`
- Services: `keep_alive_start`, `keep_alive_stop`, `keep_alive_set_interval`, `keep_alive_enable_sink`, `keep_alive_disable_sink`

## [0.2.0] - 2026-01-14

### Added
- **Full playback control** - Play, pause, stop, next, previous
- **Media information display** - Track name, artist, album, position
- Playback state tracking (playing, paused, stopped, idle)
- Media content type and metadata extraction

## [0.1.1] - 2026-01-13

### Fixed
- API endpoint error for default sink

## [0.1.0] - 2026-01-13

### Added
- Initial release
- Media player entities for each audio sink
- Volume control per sink
- Mute/unmute functionality
- Multi-room audio support (combined sinks and stereo pairs)
- Individual stream control (per-app volume and routing)
- Switch entities for default sink selection
- Active streams sensor
- Services: `create_combined_sink`, `create_stereo_pair`, `delete_combined_sink`
- Services: `move_stream`, `set_stream_volume`, `move_all_streams`
- UI-based configuration flow
- Real-time updates via 5-second polling

[0.6.6]: https://github.com/pawjer/ha-audio-server-controller/compare/v0.6.5...v0.6.6
[0.6.5]: https://github.com/pawjer/ha-audio-server-controller/compare/v0.6.4...v0.6.5
[0.6.4]: https://github.com/pawjer/ha-audio-server-controller/compare/v0.6.3...v0.6.4
[0.6.3]: https://github.com/pawjer/ha-audio-server-controller/compare/v0.6.2...v0.6.3
[0.6.2]: https://github.com/pawjer/ha-audio-server-controller/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/pawjer/ha-audio-server-controller/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/pawjer/ha-audio-server-controller/compare/v0.5.4...v0.6.0
[0.5.4]: https://github.com/pawjer/ha-audio-server-controller/compare/v0.5.3...v0.5.4
[0.5.3]: https://github.com/pawjer/ha-audio-server-controller/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/pawjer/ha-audio-server-controller/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/pawjer/ha-audio-server-controller/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/pawjer/ha-audio-server-controller/compare/v0.4.0...v0.5.0
[0.4.x]: https://github.com/pawjer/ha-audio-server-controller/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/pawjer/ha-audio-server-controller/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/pawjer/ha-audio-server-controller/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/pawjer/ha-audio-server-controller/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/pawjer/ha-audio-server-controller/releases/tag/v0.1.0
