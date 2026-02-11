# Release Notes v0.7.5

**Bluetooth Media Player Auto-Creation Fix** 🔧

## Bug Fixes

### 🐛 Fixed Bluetooth Media Player Auto-Creation

**Issue**: When a Bluetooth speaker connected after Home Assistant startup, the media player entity wouldn't appear automatically. Users had to reload the integration to see the new entity.

**Root Causes Identified and Fixed**:

1. **Event Field Name Mismatch**
   - PulseAudio events use `event_type` field
   - Mopidy events use `event` field
   - Coordinator was only checking `event` field, causing PulseAudio events to be mishandled

2. **Race Condition**
   - WebSocket event could arrive before PulseAudio fully initialized the sink
   - Added 0.5s delay for new sink events to ensure data is ready

3. **Missing Error Handling**
   - Entity creation failures were silent
   - Added comprehensive error handling with detailed logging

## Technical Changes

### Modified Files

**`custom_components/linux_audio_server/coordinator.py`**
- Fixed event type extraction to handle both PulseAudio (`event_type`) and Mopidy (`event`) fields
- Added 0.5s initialization delay for new PulseAudio sink events
- Enhanced logging with facility information
- Added safe access for private `_listeners` attribute
- Added explanatory comment about race condition prevention

**`custom_components/linux_audio_server/media_player.py`**
- Added comprehensive error handling with try-except blocks
- Enhanced duplicate entity detection (checks both unique_id and sink_name)
- Improved logging with debug/info/error levels throughout entity lifecycle
- Better variable naming (`existing_entity_sink_names` vs `current_sink_names`)
- Added detailed error messages with full stack traces

**`custom_components/linux_audio_server/manifest.json`**
- Bumped version from 0.7.4 to 0.7.5

## What's Fixed

✅ **Automatic Entity Creation**: Media players now appear immediately when Bluetooth speakers connect
✅ **Event Handling**: Correctly processes both PulseAudio and Mopidy WebSocket events
✅ **Timing Issues**: Eliminates race conditions with initialization delay
✅ **Error Visibility**: All failures are now logged with detailed context
✅ **Robustness**: Comprehensive error handling prevents listener crashes

## Expected Behavior After Update

**Scenario 1: Speaker Connects at Runtime**
1. Bluetooth speaker connects to audio server
2. PulseAudio creates sink (e.g., `bluez_output.XX_XX_XX_XX_XX_XX.1`)
3. WebSocket event triggers (with 0.5s delay)
4. Media player entity appears automatically ✨
5. Entity is immediately available and functional

**Scenario 2: Speaker Already Connected at Startup**
- Works as before - entity created during integration setup

**Scenario 3: Speaker Disconnects**
- Entity remains but becomes unavailable (if device still paired)
- Entity removed only if device unpaired AND sink removed

## Debugging Support

New debug logging helps diagnose issues:

```yaml
logger:
  default: info
  logs:
    custom_components.linux_audio_server: debug
```

Expected log sequence when speaker connects:
```
[INFO] Triggering update from WebSocket event: pulseaudio.new (facility: sink)
[DEBUG] New sink detected, waiting 0.5s for PulseAudio initialization
[DEBUG] Data refresh completed, notifying X listeners
[DEBUG] Entity update triggered: current_entities=Y, new_sinks=Z
[INFO] Creating new media player entity for sink: Speaker Name (bluez_output.XX_XX_XX_XX_XX_XX.1)
[INFO] Successfully added media player entity: entry_id_bluez_output.XX_XX_XX_XX_XX_XX.1
```

## Installation

### Via HACS
1. Update integration through HACS
2. Restart Home Assistant
3. Test by connecting a Bluetooth speaker

### Manual Installation
1. Copy updated files to `custom_components/linux_audio_server/`
2. Restart Home Assistant
3. Test by connecting a Bluetooth speaker

## Breaking Changes

**None** - This is a bug fix release with no breaking changes.

## Upgrade Notes

- No configuration changes needed
- Existing entities remain unchanged
- No need to reload integration after update
- Improved behavior is automatic after restart

## Requirements

- Home Assistant 2024.1+
- Linux Audio Server backend v1.0.0+
- Backend WebSocket events (already available since v0.7.0)

## What's Next?

This release completes the auto-creation functionality for Bluetooth media players. Future enhancements may include:
- Configurable initialization delay
- Entity pre-creation for paired-but-disconnected devices (optional)
- Enhanced entity naming options

## Credits

- Thanks to the community for reporting the auto-creation issue
- Deep code review ensured robust error handling and edge case coverage

---

**Enjoy seamless Bluetooth speaker integration!** 🎵

For support: [GitHub Issues](https://github.com/pawjer/ha-audio-server-controller/issues)
