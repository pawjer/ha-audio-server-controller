# Release v0.6.5 - Player Assignment Recording Fix

## 🎯 What's Fixed

This release completes the multi-player state tracking by **fixing player assignment recording**.

**The Missing Piece**: v0.6.4 taught the integration how to *read* player assignments, but the backend couldn't *record* them because the HA integration wasn't telling it which sink was playing!

**Now Fixed**: When you play media on a Bluetooth speaker, the integration tells the backend which sink it is, so the assignment gets recorded and state displays correctly!

## 🔍 The Problem

After v0.6.4, you noticed:
- Media starts playing on Bluetooth speaker
- State still shows "idle" instead of "playing"
- Backend has player2 playing, but no assignment for the Bluetooth speaker sink

**Root Cause**: The HA integration was calling the backend's play endpoints without passing the `sink` parameter, so the backend couldn't record which player was assigned to which sink.

## ✨ What Changed

### Sink Parameter Added to API Methods
- `play_radio_stream()` now accepts optional `sink` parameter
- `play_radio_url()` now accepts optional `sink` parameter
- Media player entities automatically pass their sink name when playing media

### Automatic Assignment Recording
When you play media from a media player entity:
1. Entity calls `play_radio_url(url, sink="bluez_output.54_B7_E5_89_E6_E3.1")`
2. Backend receives sink parameter and records player assignment
3. Coordinator fetches assignments every 5 seconds
4. State property finds assignment and displays correct state
5. **It just works!** 🎉

### Dynamic Updates
The coordinator already refetches all data every 5 seconds, including:
- Player states
- Player assignments
- Sink states
- Bluetooth device status

This ensures changes are reflected within 5 seconds without manual refresh!

## 🔄 Version History

This completes a 3-version journey to full multi-player support:

**v0.6.3** - Fixed playback controls
- Problem: Buttons only controlled player1
- Solution: Added sink-based playback endpoints

**v0.6.4** - Fixed state reading
- Problem: State showed idle when player2-4 were playing
- Solution: Enhanced state property to check player assignments

**v0.6.5** - Fixed assignment recording *(this release)*
- Problem: Backend couldn't record assignments (missing sink parameter)
- Solution: Media player entities now pass sink name when playing media

**Together**: Multi-player setups now work perfectly!

## 🔧 Technical Details

### Changes
- Updated `play_radio_stream()` method signature: `name: str, sink: str | None = None`
- Updated `play_radio_url()` method signature: `url: str, sink: str | None = None`
- Updated `async_play_media()` to pass `sink=self._sink_name` in all playback calls
- Maintains full backwards compatibility (sink parameter is optional)

### How It Works
```python
# Before v0.6.5
await self.coordinator.client.play_radio_url(media_id)
# Backend gets: {"url": "..."}
# No sink → no assignment recorded → state shows idle

# After v0.6.5
await self.coordinator.client.play_radio_url(media_id, sink=self._sink_name)
# Backend gets: {"url": "...", "sink": "bluez_output.54_B7_E5_89_E6_E3.1"}
# Has sink → assignment recorded → state shows playing ✅
```

### Performance
- No additional API calls
- Uses existing coordinator polling (5-second interval)
- Minimal overhead (just passing sink parameter)

## 📋 Requirements

**No backend update required** - This is a frontend-only fix.

The backend already supports sink parameter in play endpoints (since initial implementation). This release just makes the HA integration use it!

Works with any recent linux-audio-server version.

## 🚀 Installation

**Via HACS (Recommended):**
1. Go to HACS → Integrations
2. Find "Linux Audio Server"
3. Click **Update** to v0.6.5
4. Restart Home Assistant

**Manual:**
```bash
cd /path/to/homeassistant/custom_components/linux_audio_server
git pull
# Restart Home Assistant
```

## 🧪 Testing

After updating:
1. **Reload the integration** (Settings → Devices & Services → Linux Audio Server → Reload)
2. Play media on a Bluetooth speaker (from media browser or radio selector)
3. **Wait 5 seconds** for coordinator to fetch assignments
4. **Verify state shows "Playing"** (not "Idle")
5. **Verify track title shows correct information**
6. Stop playback and verify state updates to "Idle"

### Test Checklist
- [ ] Playing radio from media browser updates state correctly
- [ ] Playing from radio selector updates state correctly
- [ ] State updates within 5 seconds of starting playback
- [ ] Pause/play buttons work (v0.6.3)
- [ ] Track info displays correctly (v0.6.4)

## 🐛 Known Issues

**Intermittent Availability Issue**: Some users report Bluetooth speaker entities showing "unavailable" after Home Assistant restart, requiring integration reload.

- **Root cause**: Coordinator data sync timing issue when Bluetooth service initializes slowly
- **Workaround**: Reload the integration after HA restart
- **Status**: Under investigation
- **Impact**: Temporary, resolves automatically or with reload

This is a separate issue from assignment tracking and does not affect functionality once entities are available.

## 🎉 What's Complete

With v0.6.3, v0.6.4, and v0.6.5, multi-player support is now **fully functional**:
- ✅ 100% API coverage (v0.6.2)
- ✅ Working playback controls (v0.6.3)
- ✅ Correct state display (v0.6.4)
- ✅ Assignment recording (v0.6.5)
- ✅ Media info display (v0.6.4)

**Multi-room audio with multiple independent players is production-ready!**

## 📝 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

## 🙋 Need Help?

If you encounter any issues, please report them at:
https://github.com/pawjer/ha-audio-server-controller/issues

---

**Enjoy your fully working multi-player setup! 🎵**
