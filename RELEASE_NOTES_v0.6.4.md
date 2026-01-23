# Release v0.6.4 - Multi-Player State & Media Info Fix

## 🎯 What's Fixed

This release fixes **incorrect state and media information** for Bluetooth speakers in multi-player setups.

**Problem**: When a Bluetooth speaker was playing on player2-4, the media player entity would show:
- ❌ State: "idle" (even when actually playing)
- ❌ Track title: Info from player1 (wrong player)
- ❌ Artist/Album: Info from player1 (wrong player)

**Now Fixed**: Media player entities display the correct state and track information from the assigned player!

## ✨ What Changed

### Correct State Display
- **Playing** state now shows when speaker is actually playing
- **Paused** state reflects the correct player's state
- **Idle** only shows when playback is truly stopped
- Works correctly with player2, player3, and player4

### Accurate Media Information
- **Track title** now shows what's actually playing on that speaker
- **Artist** and **Album** come from the assigned player
- Radio station names display correctly
- No more showing player1's info on other speakers

### Smart Fallback Chain
When no player is assigned to a sink:
1. First checks assigned player (player2-4)
2. Falls back to player1 if no assignment
3. Falls back to PulseAudio sink state as last resort

This ensures backwards compatibility with single-player setups!

## 🔧 Technical Details

### Changes
- Added `_get_assigned_player_track()` helper method
- Enhanced `state` property to check player assignments
- Updated media properties: `media_title`, `media_artist`, `media_album_name`, `media_content_type`
- All changes use existing coordinator data (no new API calls)

### Performance
- Minimal overhead (just dict/list lookups)
- No additional API calls
- Same 5-second polling interval

## 📊 Before vs After

**Before v0.6.4:**
```yaml
# Bluetooth speaker on player2 playing "Jazz FM"
state: idle                    # Wrong! It's playing
media_title: null             # Wrong! Should show "Jazz FM"
media_artist: null
```

**After v0.6.4:**
```yaml
# Bluetooth speaker on player2 playing "Jazz FM"
state: playing                # Correct!
media_title: "Jazz FM"        # Correct!
media_artist: ""              # Correct (radio has no artist)
```

## 🔄 Relationship to v0.6.3

**v0.6.3** fixed the **controls** (play/pause/stop buttons)
**v0.6.4** fixes the **display** (state and media info)

Together, these releases make multi-player setups fully functional:
- ✅ Buttons control the right player (v0.6.3)
- ✅ Status shows the right information (v0.6.4)

## 📋 Requirements

**No backend update required** - This is a frontend-only fix.

Works with any recent linux-audio-server version.

## 🚀 Installation

**Via HACS (Recommended):**
1. Go to HACS → Integrations
2. Find "Linux Audio Server"
3. Click **Update** to v0.6.4
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
2. Play media on a Bluetooth speaker
3. **Verify state shows "Playing"** (not "Idle")
4. **Verify track title shows correct information**
5. Pause and check state updates to "Paused"
6. Stop and check state updates to "Idle"

## 🐛 Known Issues

**Intermittent Availability Issue**: Some users report Bluetooth speaker entities showing "unavailable" after Home Assistant restart, requiring integration reload.

- **Root cause**: Coordinator data sync timing issue when Bluetooth service initializes slowly
- **Workaround**: Reload the integration after HA restart
- **Status**: Under investigation for v0.6.5
- **Impact**: Temporary, resolves automatically or with reload

See [Deep Investigation Report](https://github.com/pawjer/ha-audio-server-controller/issues) for details.

## 🎉 What's Next

With v0.6.3 and v0.6.4, multi-player support is now **fully functional**:
- ✅ 100% API coverage (v0.6.2)
- ✅ Working playback controls (v0.6.3)
- ✅ Correct state and media info (v0.6.4)

**Future updates will focus on:**
- Fixing availability sync issue
- Performance optimizations
- Enhanced logging and diagnostics

## 📝 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

## 🙋 Need Help?

If you encounter any issues, please report them at:
https://github.com/pawjer/ha-audio-server-controller/issues

---

**Enjoy accurate media player status! 🎵**
