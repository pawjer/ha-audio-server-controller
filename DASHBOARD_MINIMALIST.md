# Minimalist Dashboard Guide

A clean, functional, per-sink audio control dashboard with no custom cards required.

## Philosophy

**Simple. Functional. Fast.**

- Each speaker gets ONE section with everything you need
- Radio dropdown selector per sink (no global selector confusion)
- Built-in cards only - works out of the box
- At-a-glance view of what's playing where
- Minimal clicks to change what's playing

## What You Get

### Per-Sink Section
Each speaker has its own box containing:
- **Media Control Card** - Play/pause/stop, volume slider, current track info
- **Radio Dropdown** - Clean dropdown selector for your favorite stations
- **Bluetooth Controls** (if applicable) - Connect/disconnect buttons

### Global Controls
One small section with:
- Pause All button
- Stop All button
- Active streams counter

## Installation

### 1. Ensure You Have the Integration

Make sure you have `linux-audio-server` integration installed and configured (v0.6.8+).

The integration automatically creates:
- ✅ One media player entity per sink
- ✅ One radio selector entity per sink (NEW!)
- ✅ All radio stations from your backend

No manual configuration needed! 🎉

### 2. Find Your Entity IDs

**Media Players:**
- Developer Tools → States → Filter by "media_player"
- Example: `media_player.usb_c_dual_4k_dock_analogowe_stereo`

**Radio Selectors (automatically created):**
- Developer Tools → States → Filter by "select" and look for ones ending in "_radio"
- Example: `select.usb_c_dual_4k_dock_analogowe_stereo_radio`
- Example: `select.john_paulacton_ii_radio`

**Bluetooth Devices (if applicable):**
- Developer Tools → States → Filter by "device_tracker"
- Get MAC address from attributes

### 3. Copy the Dashboard

```bash
# The file is already in your repository
dashboard-minimalist.yaml
```

### 4. Customize Entity IDs

Update `dashboard-minimalist.yaml` with your actual entity IDs:

```yaml
# Replace media player entities
entity: media_player.YOUR_SINK_NAME

# Replace radio selector entities
entity: select.YOUR_SINK_NAME_radio

# Replace Bluetooth MAC addresses (if applicable)
address: "YOUR:MAC:ADDRESS"
```

### 5. Add to Home Assistant

**Option A: Via UI (Recommended)**
1. Go to Settings → Dashboards
2. Click "+ ADD DASHBOARD"
3. Choose "New dashboard from scratch"
4. Name it "Audio" (or whatever you prefer)
5. Click the ⋮ menu → "Edit" → "Raw configuration editor"
6. Paste the contents of your customized `dashboard-minimalist.yaml`
7. Click "SAVE"

**Option B: Via YAML**
Add to your `configuration.yaml`:
```yaml
lovelace:
  mode: storage
  dashboards:
    lovelace-audio:
      mode: yaml
      title: Audio
      icon: mdi:speaker
      show_in_sidebar: true
      filename: dashboard-minimalist.yaml
```

### 6. Done!

That's it! Your dashboard is ready to use:
- Dropdowns are populated with your backend radio stations
- Selecting a station plays it on that specific sink
- "Off" option stops playback
- Add stations via `linux_audio_server.add_radio_stream` service

## Adding More Speakers

Simply copy this template to `dashboard-minimalist.yaml`:

```yaml
  - type: grid
    title: Kitchen Speaker
    columns: 1
    cards:
      # Playback control
      - type: media-control
        entity: media_player.kitchen_speaker

      # Radio selector (automatically populated!)
      - type: entities
        entities:
          - entity: select.kitchen_speaker_radio
            name: Radio Station
```

That's it! The integration automatically created the `select.kitchen_speaker_radio` entity for you.

## Customization Tips

### Adding More Radio Stations

Simply add stations to the backend - the dropdowns update automatically!

```yaml
# Developer Tools → Services
service: linux_audio_server.add_radio_stream
data:
  name: "Rock Radio"
  url: "http://your-rock-radio-url"
```

The station will immediately appear in all sink radio selectors.

### Removing Radio Selector

If you don't use radio on a speaker, just remove the entities card:

```yaml
  - type: grid
    title: Your Speaker
    columns: 1
    cards:
      - type: media-control
        entity: media_player.your_speaker

      # Remove the input_select card entirely
```

### Changing Dropdown Icon

Customize the icon in the dashboard:

```yaml
- entity: input_select.usb_dock_radio
  name: Radio Station
  icon: mdi:radio-fm  # Or any other icon
```

Popular icon choices:
- `mdi:radio` - Generic radio
- `mdi:radio-fm` - FM radio
- `mdi:radio-tower` - Broadcasting
- `mdi:access-point` - Internet radio
- `mdi:music` - Generic music
- `mdi:podcast` - Podcasts

Browse all icons at: https://pictogrammers.com/library/mdi/

### Removing Bluetooth Controls

If your speaker isn't Bluetooth, simply remove the third card:

```yaml
  - type: grid
    title: Your Speaker
    columns: 1
    cards:
      - type: media-control
        entity: media_player.your_speaker

      - type: entities
        entities:
          - entity: input_select.your_speaker_radio
            name: Radio Station
            icon: mdi:radio

      # Remove the bluetooth entities card entirely
```

## Complete Example: Kitchen Speaker

### Dashboard Section

Add this to `dashboard-minimalist.yaml`:

```yaml
  - type: grid
    title: Kitchen
    columns: 1
    cards:
      - type: media-control
        entity: media_player.kitchen_speaker

      - type: entities
        entities:
          - entity: select.kitchen_speaker_radio
            name: Radio Station
```

### Add Radio Stations (if needed)

```bash
# Via Developer Tools → Services
service: linux_audio_server.add_radio_stream
data:
  name: "NPR News"
  url: "http://nprdmp.ic.llnwd.net/stream/nprdmp_live01_mp3"

# Add more stations...
service: linux_audio_server.add_radio_stream
data:
  name: "Jazz FM"
  url: "http://jazz.streamr.ru/jazz-64.mp3"
```

That's all! No configuration.yaml edits needed.

## How It Works

### Automatic Per-Sink Radio Selectors

The integration automatically creates one `select` entity per audio sink:

**Entity Creation (select.py):**
- Detects all audio sinks from the backend
- Creates `select.<sink_name>_radio` entity for each
- Dynamically populates options from backend radio streams
- Adds "Off" option automatically

**When You Select a Station:**
1. The select entity's `async_select_option()` method is called
2. If "Off": Stops playback on that sink
3. If a station: Calls `play_radio_stream(name, sink=sink_name)`
4. Backend routes audio to that specific sink
5. Dashboard updates to show current selection

**Benefits:**
- ✅ Zero configuration - works out of the box
- ✅ Stations automatically sync from backend
- ✅ Add a station once, appears in all dropdowns
- ✅ Per-sink control without manual automations
- ✅ Clean dropdown UI, no button clutter

### Media Control Card
The built-in `media-control` card provides:
- Play/Pause/Stop buttons
- Previous/Next track buttons
- Volume slider
- Mute button
- Current track artwork and info
- All automatically synced with the media player entity

### Global Controls
Simple service calls:
- `linux_audio_server.pause_all` - Pauses all Mopidy players
- `linux_audio_server.stop_all` - Stops all Mopidy players

## Troubleshooting

### "Entity not available"
- Check if the integration is loaded
- Verify entity IDs in Developer Tools → States
- Reload the integration if needed

### Radio doesn't play
- Verify the stream URL is correct (test in VLC or browser)
- Check integration logs in Settings → System → Logs
- Ensure linux-audio-server backend is running

### Bluetooth connect doesn't work
- Verify MAC address format: `XX:XX:XX:XX:XX:XX` (with colons)
- Ensure device is paired first
- Check if device is in range

### Dashboard shows wrong entity names
- If you updated from v0.6.6 or earlier, reload the integration
- Delete duplicate entities in Settings → Devices & Services → Entities
- New correctly-named entities will be created automatically

## Advantages Over Other Dashboards

**vs dashboard-simple.yaml:**
- Per-sink radio control (not global)
- Cleaner layout with dropdowns (not buttons taking up space)
- Fewer sections (less scrolling)
- More intuitive (everything for a speaker is together)
- Can have dozens of stations without cluttering UI

**vs dashboard-example.yaml:**
- No custom cards required
- Simpler setup (no HACS dependencies)
- Faster loading
- Easier to customize
- Same dropdown approach but without HACS complexity

**vs dashboard-mobile.yaml:**
- Better for desktop/tablet use
- More radio stations in compact dropdown
- Clearer speaker separation
- Still mobile-friendly

## Why Dropdowns > Buttons

**Advantages of dropdown selectors:**
- ✅ Compact - doesn't take vertical space
- ✅ Scalable - add 20 stations without UI clutter
- ✅ Clean - one line per speaker for radio control
- ✅ Familiar - standard UI pattern users understand
- ✅ Fast - one tap to open, one tap to select

**When buttons might be better:**
- If you only have 2-3 stations total
- If you want visual icons for each station
- If you prefer tap-to-play without opening dropdown

## Next Steps

1. Copy the dashboard file to your Home Assistant config
2. Update entity IDs for your speakers
3. Add your favorite radio station URLs
4. Update Bluetooth MAC addresses
5. Add/remove speakers as needed
6. Customize icons and layout to your taste

Enjoy your clean, functional audio dashboard! 🎵
