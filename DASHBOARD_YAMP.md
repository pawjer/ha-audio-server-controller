# YAMP Dashboard Guide for Linux Audio Server

Modern, professional multi-room audio control using YAMP (Yet Another Media Player).

## 🎯 Why YAMP?

**Perfect for Multi-Room Audio:**
- ✅ All rooms in one card with quick chip switching
- ✅ Modern, clean UI that collapses when idle
- ✅ Custom action buttons for player assignment
- ✅ Adaptive controls for mobile and desktop
- ✅ Professional look with extended artwork
- ✅ Actively developed and maintained

**Better UX than Standard Cards:**
- Single card controls all rooms (vs. separate cards per room)
- Quick room switching via chips (vs. scrolling between cards)
- Built-in source/radio menu integration
- Collapsible design saves screen space
- Smart auto-selection when music starts playing

## 📦 Installation

### Step 1: Install YAMP via HACS

1. Open **HACS** in Home Assistant
2. Click **Frontend**
3. Click **+ Explore & Download Repositories**
4. Search for **"yet another media player"**
5. Click **Download**
6. Restart Home Assistant

### Step 2: Optional - Install Mushroom Cards

For enhanced status displays in `dashboard-yamp-advanced.yaml`:

1. Open **HACS** → **Frontend**
2. Search for **"mushroom"**
3. Download **Mushroom Cards**
4. Restart Home Assistant

### Step 3: Add Dashboard

1. Go to **Settings** → **Dashboards**
2. Click **+ Add Dashboard**
3. Choose **New dashboard from scratch**
4. Name it "Audio Control" (or your preference)
5. Click **Create**
6. Click **✏️ Edit**
7. Click **⋮** → **Raw configuration editor**
8. Copy content from `dashboard-yamp.yaml` or `dashboard-yamp-advanced.yaml`
9. Paste and customize (see below)
10. Click **Save**

## 🎨 Dashboard Variants

### Standard YAMP (`dashboard-yamp.yaml`)

**Best for:** Most users, clean and functional

**Features:**
- All rooms in main YAMP card
- **Radio stations in menu** (clean, organized)
- Player status visibility
- Global controls
- Bluetooth device management

**Complexity:** ⭐⭐ Moderate

### Advanced YAMP (`dashboard-yamp-advanced.yaml`)

**Best for:** Power users, enhanced UX

**Additional Features:**
- Enhanced player routing visualization with Mushroom cards
- Real-time status with dynamic colors
- Confirmation dialogs on destructive actions
- Optional audio scenes section
- More polished visual design

**Complexity:** ⭐⭐⭐ Advanced (requires Mushroom cards)

## 🔧 Customization

### 1. Find Your Radio Station Names

Before customizing, you need to know your exact radio station names from the backend.

**Method 1: Backend Config File**
```bash
# SSH into your server
cat /path/to/linux-audio-server/config/bluetooth-api/radio_streams.conf

# Output format:
# Jazz Radio=http://jazz-url.mp3
# Classical=http://classical-url.mp3
```

**Method 2: Developer Tools**
1. Open **Developer Tools** → **States**
2. Search for `sensor.linux_audio_server`
3. Find `radio_streams` in attributes
4. Note the station names (keys in the dict)

**Method 3: Via Select Entities**
1. Open any `select.*_radio` entity
2. Look at available options
3. These are your station names

**Example Station Names:**
```yaml
# From backend config:
Jazz FM=http://url...        → Use "Jazz FM"
Classical Music=http://url... → Use "Classical Music"
Rock=http://url...           → Use "Rock"
```

### 2. Update Entity IDs

Find your entities:
```bash
# In Developer Tools → States, search for:
media_player.*           # Your audio sinks
select.*_radio          # Radio selectors (auto-created)
device_tracker.*        # Bluetooth devices
sensor.linux_audio_server_mopidy_players
sensor.active_streams
```

Replace in YAML:
```yaml
# ❌ Template
- entity_id: media_player.usb_c_dual_4k_dock_analogowe_stereo
  name: Dock

# ✅ Your actual entity
- entity_id: media_player.kitchen_speaker
  name: Kitchen
```

### 2. Add Your Rooms

In the main YAMP card:
```yaml
entities:
  - entity_id: media_player.kitchen_speaker
    name: Kitchen
  - entity_id: media_player.living_room
    name: Living Room
  - entity_id: media_player.bedroom_speaker
    name: Bedroom
  # etc...
```

**Pro Tip:** Keep names short (1-2 words) for better chip display.

### 3. Update Bluetooth Addresses

Find MAC addresses in **Developer Tools** → **States**:
```yaml
- entity: device_tracker.your_bt_speaker
  tap_action:
    service: linux_audio_server.bluetooth_connect_and_set_default
    data:
      address: "XX:XX:XX:XX:XX:XX"  # Your actual MAC
  hold_action:
    service: linux_audio_server.bluetooth_disconnect
    data:
      address: "XX:XX:XX:XX:XX:XX"  # Same MAC
```

### 4. Adjust Idle Behavior

```yaml
collapse_on_idle: true        # true = minimize when idle
idle_timeout_ms: 45000        # 45 seconds (30000-120000 recommended)
idle_screen: default          # Options: default, search, search-recently-played
dim_chips_on_idle: true       # Dims room selector when idle
```

**Recommendations:**
- **Desktop:** `collapse_on_idle: false` (always expanded)
- **Mobile:** `collapse_on_idle: true` (saves screen space)
- **Wall tablet:** `idle_timeout_ms: 30000` (quick collapse)

### 5. Visual Customization

```yaml
# Modern, spacious layout
control_layout: modern
adaptive_controls: true
extend_artwork: true          # Premium look

# Classic, compact layout
control_layout: classic
adaptive_controls: false
extend_artwork: false         # Conservative look
```

## 🎵 Usage Guide

### Room Switching

**Via Chips:**
1. Look at chip row at top of card
2. Tap room name to switch control
3. Current room highlighted

**Auto-Selection:**
- When music starts playing, card auto-switches to that room
- Manual selection "pins" that room until you switch

### Player Assignment

**Workflow:**
1. **Select target room** - Tap room chip
2. **Open menu** - Tap ⋮ button
3. **Choose player** - Tap "Player X → Here"
4. **Verify** - Check "Player Status" section

**Example:** Play different music in Kitchen and Living Room
```
1. Tap "Kitchen" chip
2. Menu → "Player 2 → Here"
3. Play jazz radio on Kitchen

4. Tap "Living Room" chip
5. Menu → "Player 3 → Here"
6. Play rock radio on Living Room
```

### Radio Stations

**Using Menu (Recommended):**
1. **Select room** - Tap room chip (e.g., "Kitchen")
2. **Open menu** - Tap ⋮ button
3. **Choose station** - Tap radio station from top of menu
4. Station plays on selected room

**Example Flow:**
```
1. Tap "Kitchen" chip
2. Tap ⋮ menu
3. Tap "Jazz Radio" in menu
4. Jazz plays on Kitchen speaker
```

**Menu Organization:**
```
⋮ Menu
├── 📻 RADIO STATIONS
│   ├── Jazz Radio
│   ├── Classical Music
│   ├── Rock Station
│   └── Chill Music
├── ─────────────────
├── 🎵 ASSIGN PLAYER
│   ├── Player 2 → This Room
│   ├── Player 3 → This Room
│   └── Player 4 → This Room
├── ─────────────────
└── ⚙️ UTILITIES
    ├── Stop Playback
    ├── Output Selection
    └── More Info
```

**Adding Your Stations:**

Find your station names from backend:
```bash
# Check backend config file
cat config/bluetooth-api/radio_streams.conf

# Or via Developer Tools → States
# Look for radio_streams in coordinator data
```

Add to dashboard YAML:
```yaml
actions:
  - name: "Your Station Name"
    icon: mdi:radio-fm
    service: linux_audio_server.play_radio_stream
    service_data:
      name: "Exact Backend Name"  # Must match backend exactly
    in_menu: true
```

**Icon Options for Stations:**
- `mdi:radio` - Generic radio
- `mdi:music-note` - Music/melody
- `mdi:piano` - Classical
- `mdi:guitar-electric` - Rock
- `mdi:jazz` - Jazz
- `mdi:microphone` - Talk radio
- `mdi:podcast` - Podcast
- `mdi:weather-sunset` - Chill/ambient

### Bluetooth Speakers

**Connect:**
1. **Tap** device in Bluetooth section
2. Confirms connection + sets as default output

**Disconnect:**
1. **Hold** device in Bluetooth section
2. Confirms disconnection

**Scan for new:**
1. Tap "Scan BT" in Global Controls
2. Wait 10-30 seconds
3. New devices appear in list

### Global Controls

**Pause All:**
- Pauses all 4 Mopidy players
- Music can resume later
- Use for: Doorbell, phone calls, announcements

**Stop All:**
- Stops all players + clears queues
- Music won't resume
- Use for: Leaving home, bedtime

**Scan BT:**
- Triggers Bluetooth device discovery
- Lasts ~10 seconds
- New devices auto-appear

## 📱 Mobile vs Desktop

### Mobile Optimization

```yaml
# Best mobile settings
collapse_on_idle: true
idle_timeout_ms: 30000
show_chip_row: always
adaptive_text: true
card_height: null             # Auto-height
```

**Mobile Tips:**
- Swipe chips horizontally to see all rooms
- Collapsed card shows current track/room
- Tap anywhere to expand
- Large touch targets (56px icons)

### Desktop Optimization

```yaml
# Best desktop settings
collapse_on_idle: false       # Always expanded
idle_timeout_ms: 60000
extend_artwork: true
display_timestamps: true
```

**Desktop Tips:**
- All controls visible at once
- Extended artwork for visual appeal
- More breathing room for UI elements

## 🎬 Advanced: Audio Scenes (Optional)

Create scripts for common scenarios:

### Example Script: Morning Radio Kitchen

```yaml
# configuration.yaml or scripts.yaml
script:
  morning_radio:
    alias: Morning Radio - Kitchen
    sequence:
      # Connect Bluetooth speaker
      - service: linux_audio_server.bluetooth_connect_and_set_default
        data:
          address: "XX:XX:XX:XX:XX:XX"

      # Wait for connection
      - delay: 3

      # Assign player 2 to kitchen
      - service: linux_audio_server.assign_player
        data:
          player_name: player2
          sink_name: bluez_output.KITCHEN_SPEAKER.1

      # Play morning radio
      - service: linux_audio_server.play_radio_stream
        data:
          name: "Morning News"

      # Set volume
      - service: media_player.volume_set
        target:
          entity_id: media_player.kitchen_speaker
        data:
          volume_level: 0.3
```

### Add Scene Button to Dashboard

Uncomment the "Audio Scenes" section in `dashboard-yamp-advanced.yaml`:
```yaml
- type: grid
  title: 🎬 Audio Scenes
  cards:
    - type: button
      name: Morning Radio
      icon: mdi:weather-sunny
      tap_action:
        action: call-service
        service: script.morning_radio
```

## 🔍 Troubleshooting

### YAMP Card Not Loading

**Error:** "Custom element doesn't exist: yet-another-media-player"

**Solution:**
1. Verify HACS installation
2. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
3. Check HACS → Frontend → YAMP is installed
4. Restart Home Assistant

### Entities Not Showing

**Problem:** Card is empty or shows "No entities"

**Solution:**
1. Check entity IDs in **Developer Tools** → **States**
2. Verify integration is loaded
3. Ensure entities exist before adding to YAMP
4. Check for typos in entity_id

### Player Assignment Not Working

**Problem:** Menu action doesn't assign player

**Solution:**
1. Verify `sink_name` attribute exists:
   - Check in **Developer Tools** → **States**
   - Look at media_player attributes
2. Update service data to use correct sink name:
   ```yaml
   sink_name: "{{ state_attr(config.entity, 'sink_name') }}"
   ```
3. Or hardcode for testing:
   ```yaml
   sink_name: "bluez_output.YOUR_SINK.1"
   ```

### Mushroom Cards Not Found (Advanced Dashboard)

**Error:** "Custom element doesn't exist: mushroom-template-card"

**Solution:**
1. Install Mushroom via HACS (see Installation Step 2)
2. Or use standard dashboard (`dashboard-yamp.yaml`) instead

### Chip Row Too Crowded

**Problem:** Too many rooms, chips are tiny

**Solution:**
1. Use shorter names (1-2 words max)
2. Group similar sinks
3. Create separate dashboards for different zones
4. Use `show_chip_row: in_menu` to hide when idle

## 💡 Pro Tips

### 1. Name Patterns
```yaml
✅ Good: "Kitchen", "Living Room", "Dock", "BT 1"
❌ Avoid: "USB-C Dual 4K Dock Analogowe Stereo"
```

### 2. Player Strategy
- **Player 1:** Reserved for TTS (don't assign)
- **Player 2-4:** Music players (assign to rooms)
- Check status section to see current routing

### 3. Radio Workflow
- Add stations via backend (not dashboard)
- Radio selectors auto-populate
- One selector per room = clean UX

### 4. Bluetooth Best Practice
- Tap = Quick connect + default
- Hold = Disconnect
- Scan only when adding new devices

### 5. Idle Optimization
```yaml
# Active dashboard (desktop)
collapse_on_idle: false

# Passive display (wall tablet)
collapse_on_idle: true
idle_timeout_ms: 20000

# Mobile (pocket)
collapse_on_idle: true
idle_timeout_ms: 45000
```

## 🎉 Next Steps

1. **Install YAMP** via HACS
2. **Copy** `dashboard-yamp.yaml` to start
3. **Customize** entity IDs and names
4. **Test** on mobile and desktop
5. **Upgrade** to advanced version if desired
6. **Create scenes** for common usage patterns

## 📚 Related Documentation

- [YAMP GitHub](https://github.com/jianyu-li/yet-another-media-player)
- [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom)
- [Linux Audio Server README](README.md)
- [Dashboard Guide](DASHBOARD_GUIDE.md)

---

**Enjoy your professional multi-room audio dashboard!** 🎵
