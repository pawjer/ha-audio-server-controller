# Linux Audio Server Integration for Home Assistant

Control your [Linux Audio Server](https://github.com/proboszcz/linux-audio-server) from Home Assistant. This integration provides comprehensive audio management including:

- Dynamic audio sink (output) discovery
- Volume control per sink
- Multi-room audio support (combined sinks and stereo pairs)
- Individual stream control (per-app volume)
- Bluetooth device management
- Real-time updates via polling

## Features

### Media Player Entities
Each audio sink appears as a media player entity with:
- Volume control (0-100%)
- Mute/unmute
- Source selection (switch between sinks)
- State tracking (playing/idle/off)

### Switch Entities
- Default sink selection switches

### Sensor Entities
- Active streams counter with detailed stream information

### Custom Services
- `linux_audio_server.create_combined_sink` - Create multi-room audio setups
- `linux_audio_server.create_stereo_pair` - Create true stereo pairs
- `linux_audio_server.delete_combined_sink` - Remove multi-room setups
- `linux_audio_server.move_stream` - Route specific apps to different outputs
- `linux_audio_server.set_stream_volume` - Control volume per application

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
