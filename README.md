# Linux Audio Server Integration for Home Assistant

Control your [Linux Audio Server](https://github.com/proboszcz/linux-audio-server) from Home Assistant. This integration provides comprehensive audio management including:

- **Full playback control** (play, pause, stop, next, previous)
- **Media information display** (track name, artist, album)
- **Internet radio management** (add, remove, play stations)
- **Bluetooth device management** (scan, pair, connect, disconnect)
- Dynamic audio sink (output) discovery
- Volume control per sink
- Multi-room audio support (combined sinks and stereo pairs)
- Individual stream control (per-app volume)
- Real-time updates via polling
- **Works on the Media Dashboard!**

## Features

### Media Player Entities
Each audio sink appears as a media player entity with:
- **Cast/Play media to sink** - Appears as audio output target in HA's media screen
- **Browse media** - Browse and play radio stations directly from media player
- **Turn on/off Bluetooth speakers** - Power button connects/disconnects Bluetooth devices
- **URL playback** - Play internet radio, Spotify URIs, local files, any Mopidy-supported URI
- **Playback controls** (play, pause, stop, next, previous)
- **Now playing info** (track name, artist, album, position)
- Volume control (0-100%)
- Mute/unmute
- Source selection (switch between sinks)
- State tracking (playing/paused/idle/off)
- **Full Media Dashboard support**

### Switch Entities
- Default sink selection switches

### Sensor Entities
- Active streams counter with detailed stream information

### Select Entities
- **Radio station selector** - Choose and play internet radio from dropdown

### Button Entities
- **Bluetooth scan button** - Scan for nearby Bluetooth devices

### Device Tracker Entities
- **Bluetooth device trackers** - Monitor connection status of paired Bluetooth audio devices

### Custom Services
- `linux_audio_server.create_combined_sink` - Create multi-room audio setups
- `linux_audio_server.create_stereo_pair` - Create true stereo pairs
- `linux_audio_server.delete_combined_sink` - Remove multi-room setups
- `linux_audio_server.move_stream` - Route specific apps to different outputs
- `linux_audio_server.set_stream_volume` - Control volume per application
- `linux_audio_server.set_stream_mute` - Mute or unmute specific application stream
- `linux_audio_server.add_radio_stream` - Add new internet radio station
- `linux_audio_server.delete_radio_stream` - Remove radio station
- `linux_audio_server.play_radio_stream` - Play saved radio station
- `linux_audio_server.play_radio_url` - Play any radio stream by URL
- `linux_audio_server.bluetooth_pair` - Pair with Bluetooth device
- `linux_audio_server.bluetooth_connect` - Connect to Bluetooth device
- `linux_audio_server.bluetooth_disconnect` - Disconnect from Bluetooth device
- `linux_audio_server.bluetooth_connect_and_set_default` - Connect and set as default output
- `linux_audio_server.tts_speak` - Convert text to speech and play
- `linux_audio_server.keep_alive_start` - Start Bluetooth keep-alive to prevent auto-disconnect
- `linux_audio_server.keep_alive_stop` - Stop Bluetooth keep-alive
- `linux_audio_server.keep_alive_set_interval` - Set keep-alive interval (30-600 seconds)
- `linux_audio_server.keep_alive_enable_sink` - Enable keep-alive for specific sink
- `linux_audio_server.keep_alive_disable_sink` - Disable keep-alive for specific sink
- `linux_audio_server.cleanup_stale_bluetooth` - Remove entities for unpaired Bluetooth devices

### Bluetooth Keep-Alive Support

The integration includes Bluetooth keep-alive functionality to prevent Bluetooth speakers from auto-disconnecting when idle. The server periodically sends silent audio signals to configured sinks.

**Sensor Entities:**
- `sensor.linux_audio_server_bluetooth_keep_alive` - Shows keep-alive status (on/off) with interval and enabled sinks as attributes

**Usage:**

```yaml
# Start keep-alive (default 240s interval)
service: linux_audio_server.keep_alive_start

# Set custom interval (in seconds, 30-600)
service: linux_audio_server.keep_alive_set_interval
data:
  interval: 120

# Enable keep-alive for a specific Bluetooth sink
service: linux_audio_server.keep_alive_enable_sink
data:
  sink_name: "bluez_output.F4_9D_8A_5D_E7_28.1"

# Stop keep-alive
service: linux_audio_server.keep_alive_stop
```

### Text-to-Speech Support

The integration provides native text-to-speech support using Google Text-to-Speech:

```yaml
# Example: Play TTS announcement using the native service
service: linux_audio_server.tts_speak
data:
  message: "Dinner is ready"
  language: "en"  # Optional, defaults to "en"
```

Supported languages include: `en`, `es`, `fr`, `de`, `it`, `pl`, `ja`, `zh-CN`, and many more.

**Note:** Ensure the Linux Audio Server has write permissions to `/tmp/tts/` for TTS file generation.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots menu (top right)
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/pawjer/ha-audio-server-controller`
6. Category: Integration
7. Click "Add"
8. Find "Linux Audio Server" in HACS and install it
9. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/linux_audio_server` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Linux Audio Server"
4. Enter your server's:
   - **Host**: IP address or hostname
   - **Port**: Default is 6681
5. Click **Submit**

The integration will automatically discover all available audio sinks and create entities for them.

## Usage

### Basic Volume Control

Use the media player entity to control volume:

```yaml
service: media_player.volume_set
target:
  entity_id: media_player.soundcore_liberty_4_pro
data:
  volume_level: 0.5  # 50%
```

### Play Media to Audio Sink

Send media to any audio sink - they appear as audio output targets in Home Assistant:

```yaml
# Play internet radio
service: media_player.play_media
target:
  entity_id: media_player.soundcore_liberty_4_pro
data:
  media_content_type: music
  media_content_id: "http://jazz-wr11.ice.infomaniak.ch/jazz-wr11-128.mp3"

# Play Spotify track (requires Spotify Premium & Mopidy-Spotify)
service: media_player.play_media
target:
  entity_id: media_player.soundcore_liberty_4_pro
data:
  media_content_type: music
  media_content_id: "spotify:track:6rqhFgbbKwnb9MLmUQDhG6"

# Play local file
service: media_player.play_media
target:
  entity_id: media_player.soundcore_liberty_4_pro
data:
  media_content_type: music
  media_content_id: "file:///path/to/audio.mp3"
```

**Note:** The sink will automatically be set as the default audio output before playing.

### Switch Default Output

Use the source selector or switch entities:

```yaml
service: media_player.select_source
target:
  entity_id: media_player.soundcore_liberty_4_pro
data:
  source: "Built-in Audio Analog Stereo"
```

### Create Multi-Room Audio

Play audio on multiple speakers simultaneously:

```yaml
service: linux_audio_server.create_combined_sink
data:
  name: "whole_house"
  sinks:
    - "bluez_output.F4_9D_8A_5D_E7_28.1"
    - "alsa_output.pci-0000_00_1f.3.analog-stereo"
```

Then set it as default:

```yaml
service: media_player.select_source
target:
  entity_id: media_player.soundcore_liberty_4_pro
data:
  source: "whole_house"
```

### Create Stereo Pair

For true stereo separation:

```yaml
service: linux_audio_server.create_stereo_pair
data:
  name: "living_room_stereo"
  left_sink: "bluez_output.LEFT_SPEAKER.1"
  right_sink: "bluez_output.RIGHT_SPEAKER.1"
```

### Control Individual App Volume

Find the stream index from the active streams sensor, then:

```yaml
service: linux_audio_server.set_stream_volume
data:
  stream_index: 42  # From sensor.active_streams attributes
  volume: 0.3  # 30%
```

### Move Stream to Different Output

Route a specific application to a different speaker:

```yaml
service: linux_audio_server.move_stream
data:
  stream_index: 42
  sink_name: "bluez_output.F4_9D_8A_5D_E7_28.1"
```

### Manage Radio Stations

Add a new internet radio station:

```yaml
service: linux_audio_server.add_radio_stream
data:
  name: "Jazz FM"
  url: "http://jazz-wr11.ice.infomaniak.ch/jazz-wr11-128.mp3"
```

Play a saved radio station:

```yaml
service: linux_audio_server.play_radio_stream
data:
  name: "Jazz FM"
```

Or use the radio station selector entity to choose from a dropdown in the UI.

Play any radio stream by URL without saving:

```yaml
service: linux_audio_server.play_radio_url
data:
  url: "http://stream.example.com/radio.mp3"
```

### Turn On/Off Bluetooth Speakers

Bluetooth speaker media players have a power button that connects/disconnects the device:

**From UI:**
- Click the power button on the media player card to connect
- Click again to disconnect
- Use the switch entity or source selector to set as default output

**From Automations:**
```yaml
# Turn on (connect only)
service: media_player.turn_on
target:
  entity_id: media_player.creative_muvo_1c

# Turn off (disconnect)
service: media_player.turn_off
target:
  entity_id: media_player.creative_muvo_1c

# Connect and set as default output
service: media_player.turn_on
target:
  entity_id: media_player.creative_muvo_1c
- service: switch.turn_on
  target:
    entity_id: switch.creative_muvo_1c_creative_muvo_1c_default
```

**Example - Auto-connect speaker and set as default:**
```yaml
automation:
  - alias: "Connect Bluetooth Speaker at 7am"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: media_player.turn_on
        target:
          entity_id: media_player.creative_muvo_1c
      - delay: 2  # Wait for connection
      - service: switch.turn_on
        target:
          entity_id: switch.creative_muvo_1c_creative_muvo_1c_default
```

### Manage Bluetooth Devices

Scan for nearby Bluetooth devices:

Use the "Scan for Bluetooth Devices" button entity, or call the service:

```yaml
service: button.press
target:
  entity_id: button.linux_audio_server_scan_for_bluetooth_devices
```

Pair with a Bluetooth device:

```yaml
service: linux_audio_server.bluetooth_pair
data:
  address: "F4:9D:8A:5D:E7:28"
```

Connect to a paired device:

```yaml
service: linux_audio_server.bluetooth_connect
data:
  address: "F4:9D:8A:5D:E7:28"
```

Connect and automatically set as default output:

```yaml
service: linux_audio_server.bluetooth_connect_and_set_default
data:
  address: "F4:9D:8A:5D:E7:28"
```

### Play Text-to-Speech Announcements

Use the native TTS service:

```yaml
service: linux_audio_server.tts_speak
data:
  message: "The front door is open"
  language: "en"
```

## Example Automations

### Auto-Switch to Bluetooth When Connected

```yaml
automation:
  - alias: "Switch to Bluetooth Speakers When Connected"
    trigger:
      - platform: state
        entity_id: media_player.soundcore_liberty_4_pro
        to: "idle"
        from: "off"
    action:
      - service: media_player.select_source
        target:
          entity_id: media_player.soundcore_liberty_4_pro
        data:
          source: "soundcore Liberty 4 Pro"
```

### Lower Spotify Volume at Night

```yaml
automation:
  - alias: "Lower Spotify Volume at Night"
    trigger:
      - platform: time
        at: "22:00:00"
    condition:
      - condition: template
        value_template: >
          {{ states.sensor.active_streams.attributes.streams
             | selectattr('name', 'eq', 'Spotify')
             | list | length > 0 }}
    action:
      - service: linux_audio_server.set_stream_volume
        data:
          stream_index: >
            {{ states.sensor.active_streams.attributes.streams
               | selectattr('name', 'eq', 'Spotify')
               | map(attribute='index') | first }}
          volume: 0.2
```

## Troubleshooting

### Integration Won't Connect

- Verify the Linux Audio Server is running: `curl http://<server-ip>:6681/api/health`
- Check firewall settings on the audio server
- Ensure you're using the correct IP address and port

### Entities Not Updating

- Check Home Assistant logs for errors
- Verify the coordinator is polling (default: every 5 seconds)
- Restart the integration from Settings → Devices & Services

### Sinks Not Appearing

- Make sure audio sinks are available on the server: `curl http://<server-ip>:6681/api/audio/sinks`
- Reload the integration
- Check that PulseAudio is running on the server

## Changelog

### v0.5.3 (2026-01-17)

**New Feature:**
- ✨ **Stream mute/unmute control** - New service to mute/unmute individual playback streams
- Added `linux_audio_server.set_stream_mute` service

**Implementation:**
- Added `set_stream_mute` service for per-stream audio muting
- Mute/unmute specific applications (Spotify, AirPlay, radio, etc.) independently
- Works alongside existing `set_stream_volume` for full per-stream control

**Usage:**
```yaml
# Mute a specific stream (e.g., Spotify)
service: linux_audio_server.set_stream_mute
data:
  stream_index: 42  # From active streams sensor
  mute: true

# Unmute the stream
service: linux_audio_server.set_stream_mute
data:
  stream_index: 42
  mute: false
```

**Benefits:**
- Full per-application audio control (volume + mute)
- Mute background music without affecting other streams
- Perfect for automations (auto-mute during calls, etc.)

### v0.5.2 (2026-01-17)

**New Feature:**
- ✨ **Automatic cleanup of stale Bluetooth speaker entities** - Entities for unpaired devices are automatically removed
- ✨ Added `cleanup_stale_bluetooth` service to manually trigger cleanup

**Implementation:**
- Entities are automatically removed when both conditions are met:
  1. Bluetooth device is no longer paired
  2. Audio sink no longer exists
- Cleanup runs automatically on each coordinator update
- Manual cleanup available via service call

**Usage:**
```yaml
# Manually trigger cleanup
service: linux_audio_server.cleanup_stale_bluetooth
```

**Benefits:**
- No more orphaned entities cluttering your device list
- Entities disappear automatically when Bluetooth devices are unpaired
- Clean entity registry after removing old speakers

### v0.5.1 (2026-01-17)

**Critical Fix:**
- 🐛 **Fixed: Bluetooth entities stay available when disconnected** - Power button now works when speaker is off!
- Previously: Speaker disconnects → entity becomes unavailable → can't reconnect from UI
- Now: Bluetooth entities remain available (show as "off") → power button always clickable
- Works by checking if Bluetooth device is paired (from device tracker data)
- Non-Bluetooth sinks behavior unchanged

### v0.5.0 (2026-01-17)

**Major UX Improvement:**
- ✨ **Turn On/Off Bluetooth Speakers** - Media players now have power button to connect/disconnect
- 🔌 Click power button to connect Bluetooth speaker
- 🔴 Click again to disconnect
- 🤖 Perfect for automations - auto-connect speakers at specific times
- 🎯 Use switch entity or source selector to set as default output

**Implementation:**
- Automatically detects Bluetooth sinks (starts with `bluez_output`)
- Extracts Bluetooth MAC address from sink name
- Adds `TURN_ON` and `TURN_OFF` features dynamically for Bluetooth devices only
- Turn on → calls `connect_bluetooth()` (does NOT set as default)
- Turn off → calls `disconnect_bluetooth()`

**Usage:**
```yaml
# Connect only
service: media_player.turn_on
target:
  entity_id: media_player.creative_muvo_1c

# Connect and set as default (two-step)
service: media_player.turn_on
target:
  entity_id: media_player.creative_muvo_1c
- service: switch.turn_on
  target:
    entity_id: switch.creative_muvo_1c_creative_muvo_1c_default
```

### v0.4.2 (2026-01-17)

**Improvements:**
- ✨ Added `BROWSE_MEDIA` feature - Browse and play radio stations directly from media player UI
- 🔧 Improved media player visibility in Home Assistant's media interface

**Technical Changes:**
- Added `MediaPlayerEntityFeature.BROWSE_MEDIA` to supported features
- Implemented `async_browse_media()` method showing radio stations library
- Media players now appear more prominently in media dashboard and browser

**Note:** After updating, reload the integration: Settings → Devices & Services → Linux Audio Server → ⋮ → Reload

### v0.4.1 (2026-01-17)

**Major Features:**
- ✨ **Media players now appear as audio output targets** - Cast/send media from Home Assistant to audio sinks
- ✨ Added `PLAY_MEDIA` feature to all media player entities
- ✨ Support for playing URLs, Spotify URIs, local files, and any Mopidy-supported URI

**Usage:**
```yaml
service: media_player.play_media
target:
  entity_id: media_player.your_speaker
data:
  media_content_type: music
  media_content_id: "http://stream-url.mp3"  # or spotify:track:... or file://...
```

**Technical Changes:**
- Added `MediaPlayerEntityFeature.PLAY_MEDIA` to supported features
- Implemented `async_play_media()` method with URI type detection
- Automatically sets sink as default before playing media
- Supports HTTP(S) URLs, Spotify URIs, file URIs, and generic URIs

### v0.4.0 (2026-01-17)

**Major Features:**
- ✨ Added Bluetooth keep-alive functionality to prevent auto-disconnect of idle speakers
- ✨ Added keep-alive status sensor with interval and enabled sinks attributes
- ✨ Added 5 new services for keep-alive management (start, stop, set interval, enable/disable per sink)

**Technical Changes:**
- Added keep-alive API methods to client (start, stop, status, set_interval, enable/disable sink)
- Enhanced coordinator to fetch keep-alive status
- Added `BluetoothKeepAliveSensor` showing on/off status with attributes
- Added comprehensive service descriptions for keep-alive in services.yaml
- Added Polish translations for keep-alive sensor and services
- Keep-alive interval configurable from 30 to 600 seconds
- Keep-alive can be enabled/disabled per sink or globally

### v0.3.1 (2026-01-17)

**New Features:**
- ✨ Added native text-to-speech service (`linux_audio_server.tts_speak`)
- ✨ Integrated Google Text-to-Speech with multi-language support

**Technical Changes:**
- Added `speak_tts()` API method to client
- Added `tts_speak` service with message and language parameters
- Added service description in services.yaml with language selector
- Added Polish translations for TTS service
- Updated README with native TTS service documentation

### v0.3.0 (2026-01-16)

**Major Features:**
- ✨ Added internet radio management (add, delete, play stations)
- ✨ Added radio station selector entity (dropdown in UI)
- ✨ Added Bluetooth device management (scan, pair, connect, disconnect)
- ✨ Added Bluetooth device tracker entities (monitor connection status)
- ✨ Added Bluetooth scan button entity
- ✨ Support for playing arbitrary radio URLs

**Technical Changes:**
- Added radio API endpoints to client (get_radio_streams, add_radio_stream, delete_radio_stream, play_radio_stream, play_radio_url)
- Added Bluetooth API endpoints to client (scan_bluetooth, pair_bluetooth, connect_bluetooth, disconnect_bluetooth, connect_and_set_default_bluetooth)
- Added SelectEntity platform for radio station selection
- Added ButtonEntity platform for Bluetooth scanning
- Added DeviceTrackerEntity platform for Bluetooth devices
- Enhanced coordinator with graceful error handling for optional features (radio/Bluetooth)
- Added 8 new services for radio and Bluetooth management
- Added comprehensive service descriptions in services.yaml
- Added Polish translations for new entities and services
- Radio and Bluetooth features fail gracefully if not available

### v0.2.0 (2026-01-16)

**Major Features:**
- ✨ Added full playback control support (play, pause, stop, next, previous)
- ✨ Added media information display (track name, artist, album)
- ✨ Added media position tracking
- ✨ Media player entities now work fully on the Media Dashboard
- ✨ Integration now controls both audio routing AND playback

**Technical Changes:**
- Added playback API endpoints to API client
- Added playback status fetching to coordinator
- Enhanced media player entity with playback features
- Added media_title, media_artist, media_album_name properties
- Added media_position property
- Added playback control methods (play, pause, stop, next, previous)

### v0.1.1 (2026-01-16)

**Bug Fixes:**
- Fixed 405 error on `/api/audio/sink/default` endpoint
- Removed unnecessary API call - default sink is already included in sinks response
- Improved performance by reducing API calls from 3 to 2

**Improvements:**
- Added comprehensive error handling to all services
- Added input validation schemas for all services
- Added URL encoding for sink names to prevent malformed URLs
- Added JSON decode error handling
- Added availability tracking for all entities
- Fixed device info consistency across entity types
- Optimized coordinator to use parallel API calls (3x faster)
- Added proper service cleanup on integration unload
- Added support for multiple audio server instances

### v0.1.0 (2026-01-16)

**Initial Release:**
- Dynamic audio sink discovery with media player entities
- Volume control and mute functionality per sink
- Switch entities for default sink selection
- Sensor for active audio streams tracking
- Custom services for multi-room audio (combined sinks, stereo pairs)
- Stream management (move streams, per-app volume control)
- UI-based configuration flow
- English and Polish localizations
- Auto-discovery of new/removed sinks
- 5-second polling interval for real-time updates

## Development

This integration is open source and contributions are welcome!

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/pawjer/ha-audio-server-controller.git
cd ha-audio-server-controller

# Install in development mode
ln -s $(pwd)/custom_components/linux_audio_server ~/.homeassistant/custom_components/
```

### Running Tests

(Tests to be added)

## License

This project is licensed under the MIT License.

## Credits

Created for use with [Linux Audio Server](https://github.com/proboszcz/linux-audio-server).

## Support

- Report issues: [GitHub Issues](https://github.com/pawjer/ha-audio-server-controller/issues)
- Documentation: [Linux Audio Server API Docs](https://github.com/proboszcz/linux-audio-server/tree/main/docs/api)
