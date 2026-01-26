# Release Notes v0.7.2

**Enhanced Radio Control + YAMP Dashboard Examples** 🎵

## New Features

### 🎨 YAMP Dashboard Integration
- ✨ **Professional multi-room audio dashboards** using YAMP (Yet Another Media Player)
- ✨ **Two dashboard variants**: Standard and Advanced (with Mushroom cards)
- ✨ **Menu-based UX**: Radio stations, player assignment, and speaker controls in organized menu
- ✨ **Dynamic templates**: Automatically routes to selected room
- ✨ **Comprehensive documentation**: 3 guides (Full, Quick Start, Visual Examples)

### 🔊 Enhanced Radio Service
- ✨ **Sink parameter support**: `play_radio_stream` now accepts optional `sink` parameter
- ✨ **Room-specific playback**: Play radio on specific rooms without changing default sink
- ✨ **YAMP integration**: Seamless radio selection per room via menu

## Dashboard Files

### New Dashboards
1. **`dashboard-yamp.yaml`** - Modern YAMP dashboard with menu-based controls
2. **`dashboard-yamp-advanced.yaml`** - Enhanced version with Mushroom cards

### Documentation
1. **`DASHBOARD_YAMP.md`** - Complete setup and usage guide
2. **`YAMP_QUICK_START.md`** - 5-minute quick start guide
3. **`YAMP_MENU_EXAMPLE.md`** - Visual UX examples and patterns

## Technical Changes

### Service Enhancement
**`linux_audio_server.play_radio_stream`**
```yaml
# Before (v0.7.0)
service: linux_audio_server.play_radio_stream
data:
  name: "Jazz FM"
# Plays on default sink

# After (v0.7.1)
service: linux_audio_server.play_radio_stream
data:
  name: "Jazz FM"
  sink: "bluez_output.KITCHEN.1"  # Optional - play on specific room
```

### Modified Files
- `custom_components/linux_audio_server/__init__.py`
  - Updated `handle_play_radio_stream()` to accept sink parameter
  - Updated `play_radio_stream_schema` with optional sink field
  - Enhanced logging to show target sink

- `custom_components/linux_audio_server/services.yaml`
  - Added sink field documentation to play_radio_stream service

- `README.md`
  - Updated dashboard section with YAMP options
  - Added YAMP dashboards to feature list

## YAMP Dashboard Features

### Menu Organization
```
⋮ Menu
├── 📻 RADIO STATIONS
│   └── Dynamic list of your stations
├── 🎵 ASSIGN PLAYER
│   └── Player 2/3/4 assignment to rooms
├── 🔊 SPEAKER CONTROLS
│   ├── Follow Me (move audio)
│   ├── BT Keep-Alive enable/disable
│   └── Set as TTS speaker
└── ⚙️ UTILITIES
    └── Stop, Source, More Info
```

### Key Benefits
- **All rooms in one card** - Tap chips to switch between rooms
- **Contextual actions** - Templates auto-fill sink names based on selected room
- **Scalable** - Add unlimited stations without UI clutter
- **Professional UX** - Collapsible, adaptive, theme-matching design

## Installation

### Existing Users
1. **Update integration** via HACS or manual install
2. **Restart Home Assistant**
3. **Optional**: Install YAMP from HACS → Frontend
4. **Optional**: Copy `dashboard-yamp.yaml` to new dashboard

### New Dashboard Setup
1. Install **YAMP** via HACS (Frontend section)
2. Copy content from `dashboard-yamp.yaml`
3. Customize entity IDs and radio station names
4. Enjoy professional multi-room control!

## Breaking Changes

None - All changes are backward compatible.

## Upgrade Notes

- Existing `play_radio_stream` calls work unchanged
- New `sink` parameter is optional
- YAMP dashboards are optional additions

## Documentation

- **Full Guide**: [DASHBOARD_YAMP.md](DASHBOARD_YAMP.md)
- **Quick Start**: [YAMP_QUICK_START.md](YAMP_QUICK_START.md)
- **Visual Examples**: [YAMP_MENU_EXAMPLE.md](YAMP_MENU_EXAMPLE.md)
- **General Dashboards**: [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md)

## Requirements

### For Basic Features
- Home Assistant 2024.1+
- Linux Audio Server backend v1.0.0+

### For YAMP Dashboards
- **YAMP** card from HACS (required)
- **Mushroom** cards from HACS (optional, for advanced dashboard)

## Migration Guide

No migration needed - all existing functionality preserved.

To use new features:
1. Update integration
2. Restart HA
3. Radio service automatically gains sink parameter support

## What's Next?

Future enhancements being considered:
- Auto-discovery dashboard generator
- Scene-based audio presets
- Enhanced player routing visualization
- Integration with Music Assistant (if requested)

## Credits

- YAMP dashboard design inspired by multi-room audio best practices
- Community feedback on radio station UX
- Thanks to YAMP developers for excellent card flexibility

---

**Enjoy your professional multi-room audio dashboard!** 🎵

For support: [GitHub Issues](https://github.com/pawjer/ha-audio-server-controller/issues)
