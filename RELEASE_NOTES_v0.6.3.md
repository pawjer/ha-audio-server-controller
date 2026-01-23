# Release v0.6.3 - Multi-Player Playback Control Fix

## 🎯 What's Fixed

This release fixes a critical bug where **play/pause/stop buttons only controlled player1**, regardless of which player was actually assigned to your Bluetooth speaker or audio sink.

In multi-room setups with multiple Mopidy players (player2-4), clicking pause on a Bluetooth speaker would pause the wrong player. **This is now fixed!**

## ✨ Key Improvements

### Media Controls Now Work Correctly
- **Play/pause/stop buttons** automatically route to the correct player based on sink assignments
- **Next/previous track** buttons work on the right player
- No need to manually track which player is assigned to which speaker
- Works seamlessly in multi-room audio setups with 2-4 independent players

### Better Startup Experience
- Integration now starts gracefully even when Bluetooth service is still initializing
- No more errors in logs during Home Assistant restart
- Bluetooth devices appear automatically once D-Bus is ready

### Enhanced Error Handling
- Playback commands gracefully handle sinks with no active media
- Debug logging shows exactly which sink received each command
- 404 errors (no player assigned) are expected and logged appropriately

## 🔧 Technical Changes

**API Client (`api.py`)**
- Added sink-based playback methods: `play_sink()`, `pause_sink()`, `stop_sink()`
- Added sink-based navigation: `next_track_sink()`, `previous_track_sink()`
- Proper URL encoding for sink names with special characters

**Media Player (`media_player.py`)**
- All playback controls now use sink-based endpoints
- Automatic routing to correct player (player1-4)
- Graceful 404 handling for unassigned sinks
- Debug logging for troubleshooting

**Coordinator (`coordinator.py`)**
- Handles new `available` field from Bluetooth devices API
- Graceful startup when Bluetooth/D-Bus is initializing

**Version Bump**
- `manifest.json` updated to v0.6.3

## 📋 Requirements

**Backend Update Required:**
This release requires **linux-audio-server** with sink-based playback endpoints.

If you're running linux-audio-server in Docker, update to commit `5b22004` or later:
```bash
cd /path/to/linux-audio-server
git pull
docker-compose down
docker-compose up -d
```

Backend changes include:
- New sink-based playback endpoints (`/api/playback/sink/<sink_name>/play`, etc.)
- Improved Bluetooth API resilience (`available` field)
- Graceful disconnect with automatic player stopping

## 🚀 Installation

**Via HACS (Recommended):**
1. Go to HACS → Integrations
2. Find "Linux Audio Server"
3. Click Update
4. Restart Home Assistant

**Manual:**
```bash
cd /path/to/homeassistant/custom_components
git pull  # In your ha-audio-server-controller directory
# Restart Home Assistant
```

## 🧪 Testing

After updating:
1. Reload the Linux Audio Server integration
2. Play radio or media on a Bluetooth speaker
3. Click pause → Should pause the correct player
4. Click play → Should resume
5. Check Home Assistant logs for any errors (there shouldn't be any!)

## 🎉 What's Next

With 100% API coverage achieved in v0.6.2 and playback controls fixed in v0.6.3, the integration is now feature-complete and production-ready!

Future updates will focus on:
- Performance optimizations
- Additional automation examples
- Documentation improvements

## 📝 Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

## 🐛 Known Issues

None! If you encounter any issues, please report them at:
https://github.com/pawjer/ha-audio-server-controller/issues

---

**Enjoy your working media controls! 🎵**
