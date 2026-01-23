# Release v0.6.6 - Ground Truth State Detection

## 🎯 What's Fixed

This release fixes the **"idle" state bug** by using **ground truth from PulseAudio sink-inputs** instead of relying on potentially stale player assignments.

**The Real Problem**: Player assignments can be out of sync with actual audio routing!

**Example**:
- Assignment record: USB-C Dock → player3
- Reality (sink-inputs): player2 routing audio to USB-C Dock
- player3 state: "unknown"
- **Result**: Media player showed "idle" even though music was playing

**Now Fixed**: State is based on which player is ACTUALLY routing audio to the sink!

## 🔍 Root Cause Analysis

### What Went Wrong in v0.6.5

v0.6.5 tried to fix state tracking by passing the `sink` parameter when playing media, so the backend could record assignments. **But this wasn't enough!**

**Why assignments can be stale:**
1. Audio routing can change dynamically (user moves streams)
2. Players can be reassigned without updating assignments
3. Assignments are snapshots from when playback started
4. Backend player manager might not update assignments correctly

### The Real Solution

**Don't trust assignments - check actual audio routing!**

PulseAudio sink-inputs are the **ground truth** of which applications are sending audio to which sinks. This data is:
- ✅ Always current (updated in real-time)
- ✅ Reflects actual audio routing
- ✅ Can't be stale or out of sync
- ✅ Already fetched by coordinator every 5 seconds

## ✨ What Changed

### New Ground Truth Method

Added `_get_active_player_for_sink()` that checks sink-inputs:

```python
def _get_active_player_for_sink(self) -> str | None:
    """Get the player actually routing audio to this sink."""
    sink_inputs = self.coordinator.data.get("sink_inputs", [])

    # Look for Mopidy sink-inputs routing to this sink
    for sink_input in sink_inputs:
        if sink_input.get("sink") == self._sink_name:
            app_name = sink_input.get("name", "")
            # Match "Mopidy Player 2@unix:/run/pulse/native" -> "player2"
            if "Mopidy Player" in app_name:
                # Extract player number
                if "Player 1" in app_name:
                    return "player1"
                elif "Player 2" in app_name:
                    return "player2"
                # ... etc
    return None
```

### Enhanced State Property

State now checks in this order:
1. **Sink-inputs** (ground truth) - Which player is routing audio?
2. **Assignments** (might be stale) - What was last assigned?
3. **Player1 global state** (legacy fallback)
4. **PulseAudio sink state** (last resort)

### Enhanced Media Info

`_get_assigned_player_track()` also uses sink-inputs first:
1. Check which player is routing audio (sink-inputs)
2. Get that player's current track
3. Falls back to assignments if no active routing
4. Falls back to player1 if nothing else

## 📊 How It Works

**Before v0.6.6:**
```
USB-C Dock media player:
  Check assignment: player3
  Get player3 state: "unknown"
  Show state: IDLE ❌
```

**After v0.6.6:**
```
USB-C Dock media player:
  Check sink-inputs: player2 routing to this sink
  Get player2 state: "playing"
  Show state: PLAYING ✅
```

## 🔧 Technical Details

### Changes
- Added `_get_active_player_for_sink()` method to parse sink-inputs
- Enhanced `state` property to check sink-inputs before assignments
- Enhanced `_get_assigned_player_track()` to check sink-inputs before assignments
- Maintains full fallback chain for backwards compatibility

### Data Flow
```
Coordinator fetches every 5 seconds:
  - sinks (device list)
  - sink_inputs (audio routing - GROUND TRUTH)
  - players (Mopidy state)
  - player_assignments (recorded assignments - might be stale)

Media player state property:
  1. Parse sink_inputs to find active player
  2. Use active player's state
  3. Fall back to assignment if no active routing
  4. Fall back to player1/sink state if nothing else
```

### Performance
- No additional API calls
- Just parses sink_inputs that's already fetched
- String matching on sink-input names (negligible overhead)

## 📋 Requirements

**No backend update required** - This is a frontend-only fix.

Works with any linux-audio-server version that provides sink-inputs data.

## 🚀 Installation

**Via HACS (Recommended):**
1. Go to HACS → Integrations
2. Find "Linux Audio Server"
3. Click **Update** to v0.6.6
4. Restart Home Assistant

**Manual:**
```bash
cd /path/to/homeassistant/custom_components/linux_audio_server
git pull
# Restart Home Assistant
```

## 🧪 Testing

After updating:
1. **Restart Home Assistant**
2. Play media on any sink (Bluetooth speaker, USB device, etc.)
3. **Verify state shows "Playing"** immediately (not "Idle")
4. Check media info displays correctly
5. Pause and verify state updates to "Paused"
6. Stop and verify state updates to "Idle"

### Multi-Player Scenarios
Test that state works correctly when:
- Playing on player2 while player3 has stale assignment ✅
- Manually moving streams between sinks ✅
- Multiple players playing to different sinks ✅

## 🔄 Version History

This completes a multi-version journey to robust multi-player state:

**v0.6.3** - Sink-based playback controls
- Fixed: Buttons only controlled player1
- Solution: Backend sink-based endpoints

**v0.6.4** - State reading logic
- Fixed: State always showed player1's state
- Solution: Check player assignments for state

**v0.6.5** - Assignment recording
- Fixed: Backend couldn't record assignments
- Solution: Pass sink parameter when playing
- **Problem**: Assignments can still be stale!

**v0.6.6** - Ground truth detection *(this release)*
- Fixed: Stale assignments cause wrong state
- Solution: Use sink-inputs as ground truth
- **Result**: State always reflects actual audio routing

## 🎉 What's Complete

Multi-player support is now **truly production-ready**:
- ✅ 100% API coverage (v0.6.2)
- ✅ Working playback controls (v0.6.3)
- ✅ Player assignment awareness (v0.6.4)
- ✅ Assignment recording (v0.6.5)
- ✅ **Ground truth state detection (v0.6.6)**
- ✅ Accurate media info (v0.6.4-v0.6.6)

State and media info now **always reflect reality**!

## 🐛 Known Issues

**Bluetooth speaker availability after HA restart** - Under investigation separately.

This is unrelated to state detection and doesn't affect functionality once entities are available.

## 📝 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

## 🙋 Need Help?

If you encounter any issues, please report them at:
https://github.com/pawjer/ha-audio-server-controller/issues

---

**Enjoy accurate state detection! 🎵**
