# Linux Audio Server - Dashboard Guide

This guide provides ready-to-use dashboard configurations for controlling your multi-room audio setup with Home Assistant.

## 📱 Dashboard Options

We provide **4 dashboard configurations** to suit different needs:

### 1. **Minimalist Dashboard** (`dashboard-minimalist.yaml`) ⭐ NEW
**Best for:** Clean UI, per-sink control, zero configuration

**Features:**
- ✅ Per-sink radio dropdowns (automatically populated from backend)
- ✅ Media control cards with volume and playback
- ✅ At-a-glance view of all speakers
- ✅ Bluetooth connect/disconnect
- ✅ Global pause/stop controls
- ✅ One box per speaker - everything together
- ✅ **Zero configuration** - radio selectors auto-created by integration

**Requirements:**
- **None** - Uses only built-in Home Assistant cards
- Integration v0.6.8+ (includes automatic per-sink radio selectors)

**Design Philosophy:**
Simple. Functional. Fast. No manual configuration. Radio stations sync automatically from backend.

📖 [Minimalist Dashboard Guide](DASHBOARD_MINIMALIST.md)

### 2. **Full Dashboard** (`dashboard-example.yaml`)
**Best for:** Desktop/tablet, power users, complete feature access

**Features:**
- ✅ All media players with detailed controls
- ✅ Radio station management (add/delete/play)
- ✅ Bluetooth device management
- ✅ Multi-room controls (pause all, follow me)
- ✅ Stream management
- ✅ TTS and keep-alive settings
- ✅ Auto-discovery of new devices

**Requirements:**
- HACS custom cards:
  - [mini-media-player](https://github.com/kalkih/mini-media-player)
  - [auto-entities](https://github.com/thomasloven/lovelace-auto-entities)
  - [multiple-entity-row](https://github.com/benct/lovelace-multiple-entity-row)
  - [text-input-row](https://github.com/gadgetchnnel/lovelace-text-input-row)

### 3. **Simple Dashboard** (`dashboard-simple.yaml`)
**Best for:** Users who don't want custom cards, simpler setup

**Features:**
- ✅ All media players
- ✅ Radio station quick access
- ✅ Bluetooth controls
- ✅ Multi-room controls
- ✅ Volume control
- ❌ No auto-discovery (manual configuration)
- ❌ No inline radio management

**Requirements:**
- **None** - Uses only built-in Home Assistant cards

### 4. **Mobile Dashboard** (`dashboard-mobile.yaml`)
**Best for:** Phones, quick access, minimal UI

**Features:**
- ✅ Essential playback controls
- ✅ Quick radio selection
- ✅ Bluetooth quick connect/disconnect
- ✅ Global pause/stop
- ❌ No detailed management features

**Requirements:**
- **None** - Uses only built-in Home Assistant cards

## 🚀 Installation

### Method 1: Via UI (Recommended)

1. **Open Home Assistant**
2. Go to **Settings** → **Dashboards**
3. Click **+ Add Dashboard**
4. Choose **New dashboard from scratch**
5. Name it "Audio Control"
6. Click **Create**
7. Click the **✏️ (Edit)** button
8. Click **⋮** (three dots) → **Raw configuration editor**
9. **Delete all existing content**
10. **Copy and paste** content from your chosen dashboard file
11. Update entity IDs to match your setup (see below)
12. Click **Save**

### Method 2: Via YAML File

1. Copy your chosen dashboard YAML to Home Assistant config directory:
   ```bash
   cp dashboard-simple.yaml /path/to/homeassistant/dashboards/audio.yaml
   ```

2. Edit `configuration.yaml`:
   ```yaml
   lovelace:
     mode: storage
     dashboards:
       audio-control:
         mode: yaml
         title: Audio Control
         icon: mdi:speaker
         filename: dashboards/audio.yaml
   ```

3. Restart Home Assistant

## 🔧 Customization

### Finding Your Entity IDs

1. Go to **Developer Tools** → **States**
2. Filter by `linux_audio_server`
3. Copy your entity IDs

Common entity patterns:
- Media players: `media_player.sink_description`
- Radio selector: `select.radio_stations`
- Bluetooth trackers: `device_tracker.device_name`
- Players sensor: `sensor.mopidy_players`
- Streams sensor: `sensor.active_streams`

### Updating Dashboard with Your Entities

Replace these placeholders in the YAML:

```yaml
# ❌ Template (replace this)
- entity: media_player.usb_c_dual_4k_dock_analogowe_stereo

# ✅ Your actual entity
- entity: media_player.your_speaker_name
```

### Adding More Speakers

Copy-paste media player blocks:

```yaml
# Add to any section with media players
- type: media-control
  entity: media_player.your_new_speaker
```

### Adding Radio Stations

For **dashboard-simple.yaml** and **dashboard-mobile.yaml**, add buttons manually:

```yaml
- type: button
  name: Your Station Name
  icon: mdi:radio
  tap_action:
    action: call-service
    service: linux_audio_server.play_radio_stream
    data:
      name: Your Station Name  # Must match station name in integration
```

For **dashboard-example.yaml**, stations auto-populate from `select.radio_stations`.

### Adding Bluetooth Devices

Find your device's MAC address:
1. Go to **Developer Tools** → **States**
2. Find your `device_tracker.device_name`
3. Check **Attributes** → `address`

Add to Bluetooth section:

```yaml
- entity: device_tracker.your_bt_speaker
  name: Your BT Speaker
  tap_action:
    action: call-service
    service: linux_audio_server.bluetooth_connect_and_set_default
    data:
      address: "XX:XX:XX:XX:XX:XX"  # Your MAC address
  hold_action:
    action: call-service
    service: linux_audio_server.bluetooth_disconnect
    data:
      address: "XX:XX:XX:XX:XX:XX"
```

## 🎨 Dashboard Features Explained

### Media Player Cards

**Built-in media-control:**
- Shows album art, track info, playback state
- Play/pause/stop/next/previous buttons
- Volume slider
- Works on all dashboards

**Custom mini-media-player (dashboard-example.yaml):**
- More compact
- Better mobile experience
- Customizable layout
- Artwork display options

### Radio Controls

**Quick Play:**
- Click any radio button to start playing immediately
- Uses `linux_audio_server.play_radio_stream` service

**Station Selector:**
- Dropdown showing all available stations
- Syncs with integration's radio management

**Add Station (dashboard-example.yaml):**
- Add new stations directly from dashboard
- Requires input helpers (see below)

### Bluetooth Controls

**Device Status:**
- Shows "home" when connected
- Shows "away" when disconnected
- Last changed timestamp

**Quick Actions:**
- **Tap** = Connect and set as default sink
- **Hold** = Disconnect
- **Scan** button = Search for new devices

### Multi-Room Features

**Pause All:**
- Pauses all Mopidy players (player1-4)
- Useful when doorbell rings or phone call

**Stop All:**
- Stops all playback completely
- Clears all queues

**Follow Me (dashboard-example.yaml):**
- Move all audio streams to current room
- Requires setting default sink first

## 🛠️ Required Helper Entities

For **dashboard-example.yaml**, create these helpers:

### Configuration → Helpers → Create Helper

**1. Radio Station Name Input**
```yaml
input_text.radio_name:
  name: Radio Station Name
  max: 100
```

**2. Radio Stream URL Input**
```yaml
input_text.radio_url:
  name: Radio Stream URL
  max: 500
```

**3. Default Sink Selector**
```yaml
input_select.default_sink:
  name: Default Audio Sink
  options:
    - USB-C Dual-4K Dock Analogowe stereo
    - John Paulacton II
    # Add all your sink names here
```

## 📊 Custom Cards Setup (for dashboard-example.yaml)

### Install via HACS

1. **Open HACS** → **Frontend**
2. **Search and install:**
   - mini-media-player
   - auto-entities
   - multiple-entity-row
   - text-input-row (optional, for radio management)
3. **Restart Home Assistant**

### Manual Installation

Download from GitHub and copy to `/config/www/`:
- https://github.com/kalkih/mini-media-player
- https://github.com/thomasloven/lovelace-auto-entities
- https://github.com/benct/lovelace-multiple-entity-row

## 🎯 Dashboard Tips

### Desktop Layout
- Use **dashboard-example.yaml** for full control
- Wide screens show multiple columns
- All features accessible at once

### Tablet Layout
- Use **dashboard-simple.yaml** or **dashboard-example.yaml**
- Good balance of features and usability
- Perfect for wall-mounted tablets

### Mobile Layout
- Use **dashboard-mobile.yaml** for best experience
- Optimized for one-handed use
- Quick access to most common actions

### Multi-Dashboard Setup
You can have ALL THREE installed:
- **Desktop:** Full dashboard
- **Mobile app:** Mobile dashboard
- **Wall tablet:** Simple dashboard

## 🚨 Troubleshooting

### "Entity not available"
- Check entity ID is correct
- Ensure integration is loaded
- Reload dashboard

### "Service not found"
- Integration not loaded correctly
- Check integration is enabled
- Restart Home Assistant

### Custom cards not working
- Install via HACS
- Clear browser cache (Ctrl+Shift+R)
- Check HACS integration is installed

### Buttons don't work on mobile
- Increase button tap area
- Use hold_action for secondary functions
- Consider dashboard-mobile.yaml

## 📱 Example Automation

Combine with automations for enhanced functionality:

```yaml
# Auto-connect Bluetooth when you arrive home
automation:
  - alias: Connect John Paulacton when home
    trigger:
      - platform: state
        entity_id: person.your_name
        to: home
    action:
      - service: linux_audio_server.bluetooth_connect_and_set_default
        data:
          address: "54:B7:E5:89:E6:E3"

  # Auto-play morning radio
  - alias: Morning radio
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.workday
        state: "on"
    action:
      - service: linux_audio_server.play_radio_stream
        data:
          name: "Radio Nowy Swiat"
```

## 🎉 Enjoy Your Multi-Room Audio!

Your dashboard is now ready to control your entire audio system. Happy listening! 🎵
